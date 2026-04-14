#!/usr/bin/env python3
"""
LLM Agent - Local Generation (M2 Apple Silicon)
================================================
Connects to locally running LLM via Ollama or MLX-LM for resume/cover letter generation.
Zero external API calls - all inference happens on-device.

NO cloud LLMs: Uses Ollama (llama3.2, mistral) or MLX-LM natively on M2.
NO data leakage: All prompts and responses stay within local network.
"""

import json
import os
from typing import List, Dict, Optional
from pathlib import Path


class LocalLLMAgent:
    """
    Local LLM agent for resume and cover letter generation.
    Supports both Ollama and MLX-LM backends running locally on M2.
    """

    def __init__(
        self,
        backend: str = "ollama",  # "ollama" or "mlx"
        model: str = "llama3.2:3b",
        base_url: str = "http://127.0.0.1:11434",
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ):
        """
        Initialize local LLM agent.

        Args:
            backend: LLM backend ("ollama" or "mlx")
            model: Model name to use
            base_url: Ollama API base URL (if using Ollama)
            temperature: Generation temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
        """
        self.backend = backend
        self.model = model
        self.base_url = base_url
        self.temperature = temperature
        self.max_tokens = max_tokens

        # Read profile from environment or use defaults
        self.profile_name = os.environ.get("HYRED_PROFILE_NAME", "Julian Mackler")
        self.profile_email = os.environ.get("HYRED_PROFILE_EMAIL", "julianmackler@gmail.com")
        self.profile_phone = os.environ.get("HYRED_PROFILE_PHONE", "347-882-6333")
        self.profile_location = os.environ.get("HYRED_PROFILE_LOCATION", "Washington, DC Metro")
        profile_display = os.environ.get("HYRED_PROFILE_DISPLAY", "Julian (Juju) Mackler")

        # System prompt for CV writing
        self.system_prompt = f"""You are an offline Expert CV writer and career consultant. The user operates with absolute privacy constraints - no data may ever leave their local network.

USER'S IDENTITY (USE THIS EXACT INFORMATION):
- Name: {profile_display}
- Email: {self.profile_email}
- Phone: {self.profile_phone}
- Location: {self.profile_location}

A Job Description and specific factual elements from the User's Real History will be provided to you via RAG context chunks.

YOUR TASKS:
1. Analyze the job requirements carefully
2. Extract relevant facts from the user's RAG context (their actual work history, projects, skills)
3. Synthesize a tailored resume and cover letter that matches their literal capabilities against the job requirements

CRITICAL CONSTRAINTS:
- YOU MUST strictly use only the explicit facts (numbers, project scale, specific tools, dates) listed in the user's RAG context chunks
- Hallucination is BANNED - do not invent experiences, skills, or achievements
- If the user's background doesn't match a requirement, acknowledge the gap honestly rather than fabricating
- Use professional, ATS-friendly formatting
- Quantify achievements where possible (use numbers from their actual history)
- Match keywords from the job description naturally (don't keyword stuff)
- For the resume header, use: {profile_display} | {self.profile_email} | {self.profile_phone} | {self.profile_location}
- For the cover letter salutation, use "Dear Hiring Team," (NOT "Dear Hiring Manager")
- For the cover letter signature, use "{self.profile_name}" (NOT "[Your Name]" or "[Hiring Manager]")

OUTPUT FORMAT:
Provide TWO sections:
1. **Tailored Resume** (Markdown format, ATS-friendly, 1-2 pages)
   - Header MUST include: {profile_display} | {self.profile_email} | {self.profile_phone} | {self.profile_location}
2. **Cover Letter** (3 paragraphs, professional tone, specific examples from their history)
   - Salutation: "Dear Hiring Team,"
   - Signature: "{self.profile_name}"

Focus on:
- Matching their proven experience to the job requirements
- Highlighting transferable skills
- Using concrete examples from their actual work history
- Maintaining honesty and authenticity"""

        # Test connection
        self.available = self._test_connection()

        if self.available:
            print("✅ LLM Agent initialized")
            print(f"   🤖 Backend: {backend}")
            print(f"   📦 Model: {model}")
            print(f"   🌐 Base URL: {base_url}")
        else:
            print("⚠️  LLM backend not available. Please ensure Ollama is running:")
            print("   ollama serve")
            print(f"   Or pull a model: ollama pull {model}")

    def _ollama_endpoint(self, suffix: str) -> str:
        """
        Normalize Ollama endpoint construction whether the base URL points at:
        - Apollo Bridge: http://127.0.0.1:8000/api/ollama
        - Raw Ollama:    http://127.0.0.1:11434
        """
        base = self.base_url.rstrip("/")
        suffix = suffix.lstrip("/")

        if base.endswith("/api/ollama") or base.endswith("/api"):
            return f"{base}/{suffix}"
        return f"{base}/api/{suffix}"

    def _test_connection(self) -> bool:
        """Test connection to local LLM backend"""
        if self.backend == "ollama":
            try:
                import requests

                response = requests.get(self._ollama_endpoint("tags"), timeout=5)
                return response.status_code == 200
            except Exception:
                return False
        elif self.backend == "mlx":
            try:
                # Test if MLX-LM server is running
                import requests

                response = requests.get("http://localhost:8080/health", timeout=5)
                return response.status_code == 200
            except Exception:
                return False
        return False

    def generate_resume_and_cover_letter(
        self, job_description: str, rag_chunks: List[Dict], stream: bool = False, tone: int = 50, profile: Optional[Dict] = None
    ) -> Dict[str, str]:
        """
        Generate tailored resume and cover letter.
        tone: 0 = most formal (temp 0.3), 100 = most conversational (temp 0.85)

        Args:
            job_description: Job posting text
            rag_chunks: Relevant chunks from RAG search
            stream: Whether to stream response
            profile: Optional profile data (e.g. from NotebookLM)

        Returns:
            Dictionary with 'resume' and 'cover_letter' keys
        """
        # Apply tone → temperature mapping
        self.temperature = 0.3 + (tone / 100.0) * 0.55

        # Build prompt with RAG context
        user_prompt = self._build_prompt(job_description, rag_chunks, profile)

        if self.backend == "ollama":
            return self._generate_with_ollama(user_prompt, stream)
        elif self.backend == "mlx":
            return self._generate_with_mlx(user_prompt, stream)
        else:
            return {
                "resume": "Error: Invalid backend specified",
                "cover_letter": "Error: Please use 'ollama' or 'mlx' backend",
            }

    def _build_prompt(self, job_description: str, rag_chunks: List[Dict], profile: Optional[Dict] = None) -> str:
        """
        Build prompt with job description and RAG context.

        Args:
            job_description: Job posting text
            rag_chunks: Relevant resume chunks from RAG
            profile: Optional profile summary

        Returns:
            Formatted prompt string
        """
        # User's identity info
        name = profile.get("name", self.profile_name) if profile else self.profile_name
        summary = profile.get("summary", "") if profile else ""

        user_identity = f"""USER'S IDENTIFYING INFORMATION (USE THIS EXACTLY):
- Full Name: {name}
- Email: {self.profile_email}
- Phone: {self.profile_phone}
- Location: {self.profile_location}
"""
        if summary:
            user_identity += f"\nCORE PROFESSIONAL PROFILE (from NotebookLM):\n{summary}\n"
        
        # Format RAG chunks
        context_text = "USER'S ACTUAL WORK HISTORY (from RAG context):\n\n"
        for i, chunk in enumerate(rag_chunks, 1):
            context_text += f"[Chunk {i} - {chunk['metadata']['section']} - {Path(chunk['file_path']).name}]\n"
            context_text += f"{chunk['text']}\n\n"

        # Build full prompt with explicit identity block
        prompt = f"""{self.system_prompt}

{user_identity}
{context_text}

JOB DESCRIPTION:
{job_description}

INSTRUCTIONS:
Based on the user's ACTUAL work history above (from their local documents), create:

1. A tailored resume that:
   - Matches their proven experience to the job requirements
   - Uses specific numbers and achievements from their history
   - Is ATS-friendly (clear headings, standard sections, no graphics)
   - Highlights transferable skills
   - Uses EXACT contact info: {name} | {self.profile_email} | {self.profile_phone} | {self.profile_location}

2. A 3-paragraph cover letter that:
   - Opens with enthusiasm for the specific role at the specific company
   - Provides 2-3 concrete examples from their actual work history
   - Explains why they're a strong match (based on facts, not fluff)
   - Uses salutation: "Dear Hiring Team,"
   - Signs off with: "{name}"
   - NEVER use placeholders like "[Company Name]" - extract company from job description or omit

Remember: ONLY use facts from their actual history. Do not invent experiences.
DO NOT use placeholder text like "[Your Name]" or "[Hiring Manager]" or "[Company Name]" or "[University Name]" or fake emails/phones.
If information is not in their RAG context, omit it rather than using placeholders.

OUTPUT:"""

        return prompt

    def _generate_with_ollama(
        self, prompt: str, stream: bool = False
    ) -> Dict[str, str]:
        """Generate using Ollama API (non-streaming path is generator-free)."""
        import requests

        if stream:
            return self._stream_with_ollama(prompt)

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "keep_alive": "60m",
            "options": {
                "temperature": self.temperature,
                "num_predict": self.max_tokens,
            },
        }

        try:
            response = requests.post(
                self._ollama_endpoint("generate"),
                json=payload,
                stream=False,
                timeout=180,
            )
            full_response = response.json().get("response", "")
            resume, cover_letter = self._parse_response(full_response)
            return {"resume": resume, "cover_letter": cover_letter}

        except requests.exceptions.ConnectionError:
            return {
                "resume": "Error: Cannot connect to Ollama. Please run: ollama serve",
                "cover_letter": "Error: Ollama is not running on localhost:11434",
            }
        except Exception as e:
            return {
                "resume": f"Error generating resume: {str(e)}",
                "cover_letter": f"Error generating cover letter: {str(e)}",
            }

    def _stream_with_ollama(self, prompt: str):
        """Streaming generator — separate from the non-streaming path so the
        non-streaming method contains no yield and returns a plain dict."""
        import requests

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": True,
            "keep_alive": "60m",
            "options": {"temperature": self.temperature, "num_predict": self.max_tokens},
        }
        try:
            response = requests.post(
                self._ollama_endpoint("generate"), json=payload, stream=True, timeout=180
            )
            full_response = ""
            for line in response.iter_lines():
                if line:
                    import json as _json
                    chunk = _json.loads(line)
                    if "response" in chunk:
                        full_response += chunk["response"]
                        yield {"chunk": chunk["response"], "done": False}
            yield {"chunk": "", "done": True, "full": full_response}
        except Exception as e:
            yield {"chunk": "", "done": True, "error": str(e)}

    def _generate_with_mlx(self, prompt: str, stream: bool = False) -> Dict[str, str]:
        """Generate using MLX-LM server (non-streaming path is generator-free)."""
        import requests

        if stream:
            return self._stream_with_mlx(prompt)

        payload = {
            "prompt": prompt,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }

        try:
            response = requests.post(
                "http://localhost:8080/generate", json=payload, stream=False, timeout=120
            )
            full_response = response.json().get("generated_text", "")
            resume, cover_letter = self._parse_response(full_response)
            return {"resume": resume, "cover_letter": cover_letter}
        except Exception as e:
            return {
                "resume": f"Error generating resume: {str(e)}",
                "cover_letter": f"Error generating cover letter: {str(e)}",
            }

    def _stream_with_mlx(self, prompt: str):
        """Streaming generator for MLX — separate so non-streaming path has no yield."""
        import requests

        payload = {
            "prompt": prompt,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }
        try:
            response = requests.post(
                "http://localhost:8080/generate", json=payload, stream=True, timeout=120
            )
            full_response = ""
            for line in response.iter_lines():
                if line:
                    import json as _json
                    chunk = _json.loads(line)
                    if "token" in chunk:
                        full_response += chunk["token"]
                        yield {"chunk": chunk["token"], "done": False}
            yield {"chunk": "", "done": True, "full": full_response}
        except Exception as e:
            yield {"chunk": "", "done": True, "error": str(e)}

    def _parse_response(self, response_text: str) -> tuple:
        """
        Parse LLM response into resume and cover letter.
        Handles all common heading styles llama3.2/mistral produce.
        """
        import re

        text = response_text.strip()
        if not text:
            return ("No content generated. Please try again.", "")

        # ── Build a regex that matches any reasonable section heading ──
        # Covers: **Tailored Resume**, # Resume, ## Cover Letter, ---Resume---, etc.
        resume_pattern = re.compile(
            r"(?:^|\n)"                          # start of line
            r"(?:\*{1,3}|#{1,4}|[-=]{2,})?\s*"  # optional markdown prefix
            r"(?:tailored\s+)?resume"            # "resume" or "tailored resume"
            r"(?:\s*\*{1,3}|:)?",                # optional suffix
            re.IGNORECASE,
        )
        cover_pattern = re.compile(
            r"(?:^|\n)"
            r"(?:\*{1,3}|#{1,4}|[-=]{2,})?\s*"
            r"cover\s+letter"
            r"(?:\s*\*{1,3}|:)?",
            re.IGNORECASE,
        )

        rm = resume_pattern.search(text)
        cm = cover_pattern.search(text)

        if rm and cm and rm.start() < cm.start():
            resume = text[rm.start():cm.start()].strip()
            cover_letter = text[cm.start():].strip()
        elif rm and cm and cm.start() < rm.start():
            # Cover letter came first — unusual but handle it
            cover_letter = text[cm.start():rm.start()].strip()
            resume = text[rm.start():].strip()
        elif rm:
            # Only resume found — everything after is the resume
            resume = text[rm.start():].strip()
            cover_letter = ""
        elif cm:
            # Only cover letter found
            resume = text[:cm.start()].strip()
            cover_letter = text[cm.start():].strip()
        else:
            # No markers at all — split at first blank line after ~40% mark
            # so the resume gets the bulk and cover letter gets the tail
            lines = text.split("\n")
            split = max(len(lines) * 2 // 3, 1)
            resume = "\n".join(lines[:split]).strip()
            cover_letter = "\n".join(lines[split:]).strip()

        # Safety: if resume is suspiciously short, treat whole output as resume
        if len(resume) < 100 and len(cover_letter) > 100:
            resume, cover_letter = cover_letter, resume

        return resume, cover_letter

    def list_available_models(self) -> List[str]:
        """List available models on Ollama"""
        if self.backend != "ollama":
            return []

        try:
            import requests

            response = requests.get(self._ollama_endpoint("tags"), timeout=5)
            if response.status_code == 200:
                data = response.json()
                return [model["name"] for model in data.get("models", [])]
        except Exception:
            pass

        return []


# Global instance
_llm_agent: Optional[LocalLLMAgent] = None


def get_llm_agent() -> LocalLLMAgent:
    """Get or create global LLM agent instance"""
    global _llm_agent
    if _llm_agent is None:
        _llm_agent = LocalLLMAgent()
    return _llm_agent


def generate_tailored_documents(
    job_description: str, rag_chunks: List[Dict]
) -> Dict[str, str]:
    """
    Convenience function to generate resume and cover letter.

    Args:
        job_description: Job posting text
        rag_chunks: Relevant RAG chunks

    Returns:
        Dictionary with resume and cover letter
    """
    agent = LocalLLMAgent(model="llama3.2:3b")
    return agent.generate_resume_and_cover_letter(job_description, rag_chunks)


if __name__ == "__main__":
    # Test LLM agent
    print("🚀 Testing Local LLM Agent")
    print("=" * 60)

    # Initialize
    agent = LocalLLMAgent(backend="ollama", model="llama3.2")

    if not agent.available:
        print("\n❌ Ollama not available. Please run:")
        print("   ollama serve")
        print("   ollama pull llama3.2")
    else:
        # List available models
        models = agent.list_available_models()
        print(f"\n📦 Available models: {models}")

        # Test generation
        test_job = """
        Senior Data Engineer
        
        Requirements:
        - 5+ years Python experience
        - Spark, Databricks
        - AWS, S3, Redshift
        - ETL pipeline development
        """

        test_chunks = [
            {
                "text": "Built ETL pipelines processing 10TB+ daily using Python and Apache Spark",
                "metadata": {"section": "experience", "file_type": ".md"},
                "file_path": "/test/resume.md",
            }
        ]

        print("\n📝 Generating test resume...")
        result = agent.generate_resume_and_cover_letter(test_job, test_chunks)

        print("\n✅ Generated Resume:")
        print(result["resume"][:500])
        print("\n✅ Generated Cover Letter:")
        print(result["cover_letter"][:300])
