#!/usr/bin/env python3
"""
NotebookLM CV Auto-Import
Fetches CV/Resume content from existing NotebookLM notebooks with "Julian Mackler" in title
"""

import subprocess
from pathlib import Path
from typing import List, Dict, Optional


class NotebookLMCVImporter:
    """
    Auto-import CV content from NotebookLM notebooks
    Searches for notebooks with "Julian Mackler" in title
    """

    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize NotebookLM CV importer

        Args:
            storage_path: Path to notebooklm storage file
        """
        self.storage_path = storage_path or str(
            Path.home() / ".notebooklm" / "storage_state.json"
        )
        self.notebooks: List[Dict] = []
        self.cv_content: str = ""

    def _run_notebooklm(
        self, args: List[str], timeout: int = 120
    ) -> subprocess.CompletedProcess:
        """Run notebooklm CLI command"""
        cmd = ["uv", "run", "notebooklm", "--storage", self.storage_path] + args
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout
            )
            return result
        except subprocess.TimeoutExpired:
            return subprocess.CompletedProcess(cmd, -1, "", "Timeout")
        except FileNotFoundError:
            return subprocess.CompletedProcess(cmd, -1, "", "notebooklm not found")

    def list_julian_mackler_notebooks(self) -> List[Dict]:
        """
        List all notebooks with "Julian Mackler" in title

        Returns:
            List of notebook dictionaries with id, title, source_count
        """
        result = self._run_notebooklm(["list"])

        if result.returncode != 0:
            print(f"❌ Failed to list notebooks: {result.stderr}")
            return []

        notebooks = []
        for line in result.stdout.split("\n"):
            # Match lines like: "• 842ad6c3-b781-4080-878a-5980dd9d24f4 : OMNI_01 - Census Final"
            if ":" in line and "julian" in line.lower():
                parts = line.split(":")
                if len(parts) >= 2:
                    nb_id = parts[0].replace("•", "").strip()
                    title = ":".join(parts[1:]).strip()

                    # Get source count
                    source_count = self._get_source_count(nb_id)

                    notebooks.append(
                        {"id": nb_id, "title": title, "source_count": source_count}
                    )

        self.notebooks = notebooks
        return notebooks

    def _get_source_count(self, notebook_id: str) -> int:
        """Get number of sources in a notebook"""
        result = self._run_notebooklm(["get", "--notebook", notebook_id])
        if result.returncode == 0:
            # Count sources in output
            sources = result.stdout.count("Added source:")
            return sources
        return 0

    def download_notebook_content(self, notebook_id: str) -> str:
        """
        Download all content from a notebook

        Args:
            notebook_id: Notebook ID

        Returns:
            Combined text content from all sources
        """
        result = self._run_notebooklm(
            ["download", "--notebook", notebook_id, "--output", "text"]
        )

        if result.returncode == 0:
            return result.stdout
        else:
            print(f"❌ Failed to download notebook: {result.stderr}")
            return ""

    def extract_cv_sections(self, content: str) -> Dict[str, str]:
        """
        Extract CV sections from notebook content

        Args:
            content: Raw notebook content

        Returns:
            Dictionary with sections: summary, experience, education, skills, etc.
        """
        sections = {
            "summary": "",
            "experience": "",
            "education": "",
            "skills": "",
            "projects": "",
            "certifications": "",
            "publications": "",
        }

        # Simple section extraction based on headers
        current_section = None
        section_text = []

        for line in content.split("\n"):
            line = line.strip()

            # Detect section headers
            if line.startswith("#") or line.startswith("##"):
                # Save previous section
                if current_section and section_text:
                    sections[current_section] = "\n".join(section_text)
                    section_text = []

                # Detect new section
                line_lower = line.lower()
                if (
                    "summary" in line_lower
                    or "profile" in line_lower
                    or "about" in line_lower
                ):
                    current_section = "summary"
                elif (
                    "experience" in line_lower
                    or "work" in line_lower
                    or "employment" in line_lower
                ):
                    current_section = "experience"
                elif (
                    "education" in line_lower
                    or "degree" in line_lower
                    or "university" in line_lower
                ):
                    current_section = "education"
                elif (
                    "skill" in line_lower
                    or "technology" in line_lower
                    or "tools" in line_lower
                ):
                    current_section = "skills"
                elif "project" in line_lower or "portfolio" in line_lower:
                    current_section = "projects"
                elif "certification" in line_lower or "credential" in line_lower:
                    current_section = "certifications"
                elif "publication" in line_lower or "paper" in line_lower:
                    current_section = "publications"
            else:
                # Add content to current section
                if current_section and line:
                    section_text.append(line)

        # Save last section
        if current_section and section_text:
            sections[current_section] = "\n".join(section_text)

        return sections

    def import_cv_to_documents(
        self, output_dir: str = "./my_documents/cv_base"
    ) -> Optional[Path]:
        """
        Import CV from NotebookLM to local documents

        Args:
            output_dir: Directory to save CV

        Returns:
            Path to saved CV file, or None if failed
        """
        from datetime import datetime

        # Find Julian Mackler notebooks
        notebooks = self.list_julian_mackler_notebooks()

        if not notebooks:
            print("❌ No notebooks found with 'Julian Mackler' in title")
            print("💡 Please ensure you have CV/resume content in NotebookLM")
            return None

        print(f"✅ Found {len(notebooks)} Julian Mackler notebooks:")
        for nb in notebooks:
            print(f"   📓 {nb['title']} ({nb['source_count']} sources)")

        # Download content from all notebooks
        all_content = []
        for nb in notebooks:
            print(f"\n📥 Downloading: {nb['title']}")
            content = self.download_notebook_content(nb["id"])
            if content:
                all_content.append(f"# {nb['title']}\n\n{content}")

        if not all_content:
            print("❌ No content downloaded")
            return None

        # Combine all content
        combined_content = "\n\n---\n\n".join(all_content)

        # Extract sections
        sections = self.extract_cv_sections(combined_content)

        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Save combined CV
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        cv_file = output_path / f"julian_mackler_cv_notebooklm_{timestamp}.md"

        with open(cv_file, "w") as f:
            f.write("# Julian Mackler - CV from NotebookLM\n\n")
            f.write(f"**Imported:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"**Source Notebooks:** {len(notebooks)}\n\n")
            f.write("---\n\n")

            # Write sections
            for section_name, section_content in sections.items():
                if section_content:
                    f.write(f"## {section_name.title()}\n\n")
                    f.write(section_content)
                    f.write("\n\n")

        print(f"\n✅ CV saved to: {cv_file}")
        print(f"📊 Sections extracted: {len([s for s in sections.values() if s])}")

        return cv_file


def import_cv_from_notebooklm() -> Optional[Path]:
    """
    Convenience function to import CV from NotebookLM

    Returns:
        Path to imported CV file
    """
    importer = NotebookLMCVImporter()
    return importer.import_cv_to_documents()


if __name__ == "__main__":
    print("🚀 NotebookLM CV Auto-Import")
    print("=" * 60)

    importer = NotebookLMCVImporter()

    # List notebooks
    print("\n📓 Finding Julian Mackler notebooks...")
    notebooks = importer.list_julian_mackler_notebooks()

    if notebooks:
        print(f"\n✅ Found {len(notebooks)} notebooks:")
        for nb in notebooks:
            print(f"   📓 {nb['title']}")
            print(f"      ID: {nb['id']}")
            print(f"      Sources: {nb['source_count']}")

        # Import CV
        print("\n📥 Importing CV content...")
        cv_path = importer.import_cv_to_documents()

        if cv_path:
            print("\n✅ CV imported successfully!")
            print(f"📁 Location: {cv_path}")
            print("\n💡 Next step: Use the Resume Builder to tailor this CV")
    else:
        print("\n❌ No Julian Mackler notebooks found")
        print("\n💡 To fix this:")
        print("   1. Go to https://notebooklm.google.com")
        print("   2. Create/upload notebooks with your CV/resume")
        print("   3. Include 'Julian Mackler' in the notebook title")
        print("   4. Run this import again")
