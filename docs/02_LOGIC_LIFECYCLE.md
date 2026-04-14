# 02 Logic Lifecycle: Hyred

This document highlights the real data flows, logic sequences, and lifecycle state management embedded inside the Hyred application.

## 1. Application Initialization
When the Hyred backend starts up (`server.py`), it sets up several critical bindings:
- Sub-directories like `my_documents` and `lancedb_data` are initialized if they do not exist.
- It prepares connections to either Ollama (`127.0.0.1:11434`) or M1 Vision services.
- The `LocalRAGEngine` instantiates `markitdown`, the `sentence-transformers` embedding model `all-MiniLM-L6-v2`, and mounts the LanceDB connection to load existing metadata.

## 2. Ingestion & Document Parsing
When a user drags and drops a document via the UI:
1. `POST /documents/upload` receives the binary payload.
2. The file is saved directly to `my_documents/{safe_name}`.
3. If it is a `.pdf` file, `pdf_to_images` converts up to three pages using `pdftoppm` or `pymupdf` fallbacks. 
4. The Base64 images are sent to the `Qwen2.5-VL` endpoint at `192.168.1.159:9339` under a rigid extraction prompt.
5. `docx` is parsed natively. Clean Markdown output is produced and saved as `{stem}_extracted.md`.
6. Later, `LocalRAGEngine` runs `index_all_documents()` where the text is chunked into 500-word sections with 50-word overlaps (`chunk_size=500`, `chunk_overlap=50`), embedded locally via `sentence-transformers`, and upserted into LanceDB under `resume_chunks`.

## 3. Resume & Cover Letter Generation (Neural Mirror)
When the user clicks "Generate Neural Match" in `index.html`/`script.js`:
1. `POST /generate` is called with `GenerateRequest` parameters (job description, profile name/title, tone).
2. The server yields a JSON stream using FastAPI's `StreamingResponse`.
3. The LLM Agent builds the prompt context. It does **not** rely on cloud LLMs; it calls `call_ollama_stream` querying the base `llama3.2` model.
4. The generation consists of two continuous AI requests:
   - Request 1: Tailored resume generation (streaming chunks down to the client).
   - Request 2: Cover letter synthesis using the synthesized resume output.
5. The UI dynamically appends the stream token-by-token to render the results inside a responsive Glassmorphism container.

## 4. ATS Scoring (Heuristic Validation)
During or post-generation:
- The UI triggers `score_ats_match()` (or equivalent local scoring logic) which cross-references the job description and the generated text.
- Common keywords and phrases are checked for presence, yielding a numeric ATS score (0-100) and distinguishing `matched` keywords from `missing` gap keywords. 
- Results dynamically update the radial ATS gauge color (`#00ffca` > 70, `#f47067` < 45).

## 5. Export Strategy
`POST /export` combines the localized outputs into a coherent markdown file with timestamped metadata and responds with a direct download stream triggering the browser's save dialog.
