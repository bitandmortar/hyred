#!/usr/bin/env python3
"""
RAG Engine - Local Knowledge Base
===================================
Converts local documents to markdown via MarkItDown, chunks, embeds with sentence-transformers,
and upserts to LanceDB. Zero external APIs - all processing on M2 Apple Silicon.

NO cloud embeddings: Uses sentence-transformers locally on Apple Silicon.
NO external databases: LanceDB stores vectors locally in ./lancedb_data/
"""

import hashlib
from pathlib import Path
from typing import List, Dict, Optional
import json

# Local imports
from markitdown import MarkItDown
from sentence_transformers import SentenceTransformer
import lancedb


class LocalRAGEngine:
    """
    Local RAG engine for resume/CV knowledge base.
    All processing happens on-device with no data leaving the network.
    """

    def __init__(
        self,
        documents_dir: str = "./my_documents",
        lancedb_dir: str = "/Volumes/OMNI_01/30_DATA_LAKE/00_LanceDB/lancedb_data",
        embedding_model: str = "all-MiniLM-L6-v2",
        chunk_size: int = 500,
        chunk_overlap: int = 50,
    ):
        """
        Initialize RAG engine with local resources.

        Args:
            documents_dir: Path to directory containing resume documents
            lancedb_dir: Path to LanceDB storage directory
            embedding_model: HuggingFace sentence-transformers model (local)
            chunk_size: Words per chunk for embedding
            chunk_overlap: Overlap between chunks for context continuity
        """
        self.documents_dir = Path(documents_dir)
        self.lancedb_dir = Path(lancedb_dir)
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # Create directories if they don't exist
        self.documents_dir.mkdir(parents=True, exist_ok=True)
        self.lancedb_dir.mkdir(parents=True, exist_ok=True)

        # Initialize MarkItDown for document conversion
        self.converter = MarkItDown()

        # Initialize local embedding model (downloads once, then runs locally)
        print(f"🧠 Loading embedding model: {embedding_model}")
        self.embedding_model = SentenceTransformer(embedding_model)
        self.embedding_dim = self.embedding_model.get_sentence_embedding_dimension()

        # Initialize LanceDB connection
        self.db = lancedb.connect(self.lancedb_dir)
        self.table_name = "resume_chunks"
        self.table = self._get_or_create_table()

        # Track indexed files for incremental updates
        self.index_metadata_file = self.lancedb_dir / "index_metadata.json"
        self.indexed_files = self._load_index_metadata()

        print("✅ RAG Engine initialized")
        print(f"   📁 Documents: {self.documents_dir}")
        print(f"   💾 LanceDB: {self.lancedb_dir}")
        print(f"   📊 Embedding dim: {self.embedding_dim}")
        print(f"   📝 Indexed files: {len(self.indexed_files)}")

    def _get_or_create_table(self):
        """Get existing LanceDB table or create new one"""
        try:
            table = self.db.open_table(self.table_name)
            print(f"   📖 Opened existing LanceDB table: {self.table_name}")
            return table
        except Exception:
            # Table doesn't exist, create new one with proper schema
            import pyarrow as pa

            schema = pa.schema(
                [
                    pa.field("id", pa.string()),
                    pa.field("file_path", pa.string()),
                    pa.field("file_hash", pa.string()),
                    pa.field("chunk_index", pa.int32()),
                    pa.field("text", pa.string()),
                    pa.field("metadata", pa.string()),
                    pa.field("vector", pa.list_(pa.float32(), self.embedding_dim)),
                ]
            )

            table = self.db.create_table(self.table_name, schema=schema)
            print(f"   ✨ Created new LanceDB table: {self.table_name}")
            return table

    def _load_index_metadata(self) -> Dict:
        """Load metadata about indexed files"""
        if self.index_metadata_file.exists():
            with open(self.index_metadata_file, "r") as f:
                return json.load(f)
        return {}

    def _save_index_metadata(self):
        """Save metadata about indexed files"""
        with open(self.index_metadata_file, "w") as f:
            json.dump(self.indexed_files, f, indent=2)

    def _get_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file for change detection"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def _convert_to_markdown(self, file_path: Path) -> str:
        """
        Convert document to markdown using MarkItDown.
        Supports: .pdf, .docx, .xlsx, .pptx, .html, .md, .txt, .pages, .rtf, .odt

        Args:
            file_path: Path to document

        Returns:
            Markdown string
        """
        try:
            # Handle .pages files (Apple Pages)
            if file_path.suffix.lower() == ".pages":
                # .pages is actually a ZIP archive, extract and convert
                import zipfile
                import tempfile

                with tempfile.TemporaryDirectory() as tmpdir:
                    tmpdir_path = Path(tmpdir)
                    with zipfile.ZipFile(file_path, "r") as zip_ref:
                        zip_ref.extractall(tmpdir_path)

                    # Look for PDF or preview inside .pages archive
                    for preview_ext in [".pdf", ".jpg", ".png"]:
                        preview_file = list(
                            tmpdir_path.rglob(f"*QuickLook{preview_ext}")
                        )
                        if preview_file:
                            # Convert the preview instead
                            result = self.converter.convert(str(preview_file[0]))
                            return result.text_content

                    # Fallback: look for any text content
                    for xml_file in tmpdir_path.rglob("*.xml"):
                        if "index.xml" in str(xml_file):
                            result = self.converter.convert(str(xml_file))
                            return result.text_content

            # Direct read fallback for plain text formats
            if file_path.suffix.lower() in [".txt", ".md"]:
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        return f.read()
                except Exception:
                    pass

            # Standard conversion for other formats
            result = self.converter.convert(str(file_path))
            return result.text_content
        except Exception as e:
            print(f"⚠️  Error converting {file_path}: {e}")
            return ""

    def _chunk_text(self, text: str, file_path: Path) -> List[Dict]:
        """
        Chunk text into overlapping segments for better retrieval context.

        Args:
            text: Text to chunk
            file_path: Source file path for metadata

        Returns:
            List of chunk dictionaries
        """
        chunks = []

        # Split by paragraphs first
        paragraphs = text.split("\n\n")

        current_chunk = ""
        current_chunk_index = 0
        current_word_count = 0

        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue

            words = paragraph.split()
            word_count = len(words)

            # If paragraph fits in current chunk
            if current_word_count + word_count <= self.chunk_size:
                current_chunk += "\n\n" + paragraph if current_chunk else paragraph
                current_word_count += word_count
            else:
                # Save current chunk if it exists
                if current_chunk:
                    chunks.append(
                        {
                            "id": f"{file_path.stem}_{current_chunk_index}",
                            "file_path": str(file_path.absolute()),
                            "file_hash": self._get_file_hash(file_path),
                            "chunk_index": current_chunk_index,
                            "text": current_chunk,
                            "metadata": json.dumps(
                                {
                                    "file_type": file_path.suffix,
                                    "word_count": current_word_count,
                                    "section": self._detect_section(current_chunk),
                                }
                            ),
                        }
                    )
                    current_chunk_index += 1

                # Start new chunk with overlap
                if self.chunk_overlap > 0 and chunks:
                    # Get last few sentences from previous chunk for overlap
                    overlap_sentences = current_chunk.split(".")[-3:]
                    current_chunk = ". ".join(overlap_sentences) + "\n\n" + paragraph
                else:
                    current_chunk = paragraph

                current_word_count = len(current_chunk.split())

        # Add final chunk
        if current_chunk:
            chunks.append(
                {
                    "id": f"{file_path.stem}_{current_chunk_index}",
                    "file_path": str(file_path.absolute()),
                    "file_hash": self._get_file_hash(file_path),
                    "chunk_index": current_chunk_index,
                    "text": current_chunk,
                    "metadata": json.dumps(
                        {
                            "file_type": file_path.suffix,
                            "word_count": current_word_count,
                            "section": self._detect_section(current_chunk),
                        }
                    ),
                }
            )

        return chunks

    def _detect_section(self, text: str) -> str:
        """Detect which resume section this chunk belongs to"""
        text_lower = text.lower()

        section_keywords = {
            "experience": [
                "experience",
                "work history",
                "employment",
                "role",
                "responsibility",
            ],
            "education": [
                "education",
                "degree",
                "university",
                "college",
                "school",
                "gpa",
            ],
            "skills": [
                "skill",
                "technology",
                "tool",
                "language",
                "framework",
                "proficient",
            ],
            "projects": [
                "project",
                "portfolio",
                "github",
                "repository",
                "built",
                "developed",
            ],
            "certifications": [
                "certification",
                "certificate",
                "credential",
                "aws",
                "azure",
            ],
            "summary": ["summary", "objective", "profile", "about", "professional"],
            "achievements": ["achievement", "award", "recognition", "honor", "metric"],
        }

        for section, keywords in section_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                return section

        return "other"

    def _embed_chunks(self, chunks: List[Dict]) -> List[Dict]:
        """
        Generate embeddings for chunks using local sentence-transformers.

        Args:
            chunks: List of chunk dictionaries

        Returns:
            Chunks with added vector embeddings
        """
        if not chunks:
            return []

        texts = [chunk["text"] for chunk in chunks]

        # Generate embeddings locally on M2
        embeddings = self.embedding_model.encode(
            texts, batch_size=32, show_progress_bar=True, convert_to_numpy=True
        )

        # Add vectors to chunks
        for chunk, embedding in zip(chunks, embeddings):
            chunk["vector"] = embedding.tolist()

        return chunks

    def _upsert_chunks(self, chunks: List[Dict]):
        """
        Upsert chunks into LanceDB (insert new, update existing).

        Args:
            chunks: List of chunk dictionaries with vectors
        """
        if not chunks:
            return

        # Prepare data for LanceDB
        data = []
        for chunk in chunks:
            data.append(
                {
                    "id": chunk["id"],
                    "file_path": chunk["file_path"],
                    "file_hash": chunk["file_hash"],
                    "chunk_index": chunk["chunk_index"],
                    "text": chunk["text"],
                    "metadata": chunk["metadata"],
                    "vector": chunk["vector"],
                }
            )

        # Upsert into LanceDB
        self.table.to_pandas()  # Load existing data
        self.table.add(data, mode="append")

        print(f"   📊 Upserted {len(chunks)} chunks to LanceDB")

    def _delete_old_chunks(self, file_path: Path):
        """
        Delete old chunks for a file before re-indexing.

        Args:
            file_path: Path to file
        """
        try:
            # Delete chunks matching file path
            self.table.delete(f"file_path = '{str(file_path.absolute())}'")
            print(f"   🗑️  Deleted old chunks for: {file_path.name}")
        except Exception as e:
            print(f"   ⚠️  Error deleting old chunks: {e}")

    def index_file(self, file_path: Path) -> int:
        """
        Index a single file: convert → chunk → embed → upsert.

        Args:
            file_path: Path to file to index

        Returns:
            Number of chunks indexed
        """
        print(f"\n📄 Indexing: {file_path.name}")

        # Check if file needs re-indexing
        current_hash = self._get_file_hash(file_path)
        if file_path in self.indexed_files:
            if self.indexed_files[file_path] == current_hash:
                print(f"   ⏭️  Skipping (unchanged): {file_path.name}")
                return 0

        # Convert to markdown
        markdown = self._convert_to_markdown(file_path)
        if not markdown:
            print(f"   ⚠️  No content extracted: {file_path.name}")
            return 0

        print(f"   📝 Converted to markdown ({len(markdown)} chars)")

        # Delete old chunks for this file
        self._delete_old_chunks(file_path)

        # Chunk text
        chunks = self._chunk_text(markdown, file_path)
        print(f"   ✂️  Created {len(chunks)} chunks")

        # Generate embeddings
        chunks = self._embed_chunks(chunks)
        print("   🧠 Generated embeddings")

        # Upsert to LanceDB
        self._upsert_chunks(chunks)

        # Update metadata
        self.indexed_files[str(file_path)] = current_hash
        self._save_index_metadata()

        return len(chunks)

    def index_all_documents(self) -> int:
        """
        Recursively index all documents in documents_dir.

        Returns:
            Total number of chunks indexed
        """
        print(f"\n{'='*60}")
        print(f"📚 Indexing all documents in: {self.documents_dir}")
        print(f"{'='*60}")

        total_chunks = 0
        file_extensions = [".pdf", ".docx", ".xlsx", ".pptx", ".html", ".md", ".txt", ".pages"]

        # Find all supported files
        files_to_index = []
        for ext in file_extensions:
            files_to_index.extend(self.documents_dir.rglob(f"*{ext}"))

        print(f"🔍 Found {len(files_to_index)} files to index")

        # Index each file
        for file_path in files_to_index:
            chunks = self.index_file(file_path)
            total_chunks += chunks

        print(f"\n{'='*60}")
        print("✅ Indexing complete!")
        print(f"   📊 Total chunks: {total_chunks}")
        print(f"   📁 Files indexed: {len(self.indexed_files)}")
        print(f"{'='*60}")

        return total_chunks

    def search(self, query: str, k: int = 10, shuffle: bool = True) -> List[Dict]:
        """
        Search for relevant chunks using semantic similarity or random shuffling.

        Args:
            query: Search query text
            k: Number of results to return
            shuffle: If True, returns a random sample from the top-2x results or 
                    if 'PURE_SHUFFLE' is detected in query, returns purely random chunks.

        Returns:
            List of relevant chunks with scores
        """
        import random
        
        # 1. PURE SHUFFLE MODE (Sampling from entire corpus)
        if shuffle and "PURE_SHUFFLE" in query.upper():
            print("🎲 [RAG] PURE SHUFFLE MODE: Sampling random chunks from corpus")
            df = self.table.to_pandas()
            if len(df) <= k:
                results = df.to_dict('records')
            else:
                results = df.sample(n=k).to_dict('records')
            
            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "text": result["text"],
                    "file_path": result["file_path"],
                    "chunk_index": result["chunk_index"],
                    "metadata": json.loads(result["metadata"]) if isinstance(result["metadata"], str) else result["metadata"],
                    "score": random.random() # Random score for shuffle mode
                })
            return formatted_results

        # 2. SEMANTIC SEARCH (With optional top-K jitter/shuffling)
        query_embedding = self.embedding_model.encode([query])[0].tolist()
        
        # Increase search pool if shuffling results
        search_k = k * 2 if shuffle else k
        results = self.table.search(query_embedding).limit(search_k).to_list()

        # Shuffle the results pool
        if shuffle:
            random.shuffle(results)
            results = results[:k]
        else:
            results = results[:k]

        # Format results
        formatted_results = []
        for result in results:
            formatted_results.append(
                {
                    "text": result["text"],
                    "file_path": result["file_path"],
                    "chunk_index": result["chunk_index"],
                    "metadata": json.loads(result["metadata"]) if isinstance(result["metadata"], str) else result["metadata"],
                    "score": 1 - result.get("_distance", 0.5),
                }
            )

        return formatted_results

    def get_stats(self) -> Dict:
        """Get indexing statistics"""
        try:
            df = self.table.to_pandas()
            return {
                "total_chunks": len(df),
                "total_files": len(self.indexed_files),
                "file_types": df["metadata"]
                .apply(lambda x: json.loads(x)["file_type"])
                .value_counts()
                .to_dict(),
                "sections": df["metadata"]
                .apply(lambda x: json.loads(x)["section"])
                .value_counts()
                .to_dict(),
            }
        except Exception:
            return {
                "total_chunks": 0,
                "total_files": 0,
                "file_types": {},
                "sections": {},
            }


# Global instance for reuse
_rag_engine: Optional[LocalRAGEngine] = None


def get_rag_engine() -> LocalRAGEngine:
    """Get or create global RAG engine instance"""
    global _rag_engine
    if _rag_engine is None:
        _rag_engine = LocalRAGEngine()
    return _rag_engine


def search_resume(query: str, k: int = 10) -> List[Dict]:
    """
    Convenience function to search resume knowledge base.

    Args:
        query: Search query
        k: Number of results

    Returns:
        Relevant chunks
    """
    engine = get_rag_engine()
    return engine.search(query, k)


if __name__ == "__main__":
    # Test RAG engine
    print("🚀 Testing Local RAG Engine")
    print("=" * 60)

    # Initialize
    engine = LocalRAGEngine()

    # Index all documents
    engine.index_all_documents()

    # Get stats
    stats = engine.get_stats()
    print("\n📊 Database Statistics:")
    print(f"   Total chunks: {stats['total_chunks']}")
    print(f"   Total files: {stats['total_files']}")
    print(f"   File types: {stats['file_types']}")
    print(f"   Sections: {stats['sections']}")

    # Test search
    test_query = input("\n🔍 Enter search query (or press Enter to skip): ").strip()
    if test_query:
        results = engine.search(test_query, k=5)
        print(f"\n✅ Found {len(results)} relevant chunks:")
        for i, result in enumerate(results, 1):
            print(
                f"\n{i}. Score: {result['score']:.3f} | Section: {result['metadata']['section']}"
            )
            print(f"   File: {Path(result['file_path']).name}")
            print(f"   Text: {result['text'][:200]}...")
