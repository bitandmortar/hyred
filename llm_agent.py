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
        model: str = "llama3.2",  # or "mistral", "llama3.1", etc.
        base_url: str = "http://localhost:11434",
        temperature: float = 0.7,
        max_tokens: int = 2048,
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

        # System prompt for CV writing
        self.system_prompt = """You are an offline Expert CV writer and career consultant. The user operates with absolute privacy constraints - no data may ever leave their local network.

A Job Description and specific factual elements from the User's Real History will be provided to you via RAG context chunks.

YOUR TASKS:
1. Analyze the job requirements carefully
2. Extract relevant facts from the user's RAG context (their actual work history, projects, skills)
3. Synthesize a tailored resume and cover letter that matches their literal capabilities against the job requirements

CRITICAL CONSTRAINTS:
- YOU MUST strictly use only the explicit facts (numbers, project scale, specific tools, dates) listed in the user's RAG context chunks
- Hallucination is BANDED - do not invent experiences, skills, or achievements
- If the user's background doesn't match a requirement, acknowledge the gap honestly rather than fabricating
- Use professional, ATS-friendly formatting
- Quantify achievements where possible (use numbers from their actual history)
- Match keywords from the job description naturally (don't keyword stuff)

OUTPUT FORMAT:
Provide TWO sections:
1. **Tailored Resume** (Markdown format, ATS-friendly, 1-2 pages)
2. **Cover Letter** (3 paragraphs, professional tone, specific examples from their history)

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

    def _test_connection(self) -> bool:
        """Test connection to local LLM backend"""
        if self.backend == "ollama":
            try:
                import requests

                response = requests.get(f"{self.base_url}/api/tags", timeout=5)
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
        self, job_description: str, rag_chunks: List[Dict], stream: bool = False
    ) -> Dict[str, str]:
        """
        Generate tailored resume and cover letter.

        Args:
            job_description: Job posting text
            rag_chunks: Relevant chunks from RAG search
            stream: Whether to stream response

        Returns:
            Dictionary with 'resume' and 'cover_letter' keys
        """
        # Build prompt with RAG context
        user_prompt = self._build_prompt(job_description, rag_chunks)

        if self.backend == "ollama":
            return self._generate_with_ollama(user_prompt, stream)
        elif self.backend == "mlx":
            return self._generate_with_mlx(user_prompt, stream)
        else:
            return {
                "resume": "Error: Invalid backend specified",
                "cover_letter": "Error: Please use 'ollama' or 'mlx' backend",
            }

    def _build_prompt(self, job_description: str, rag_chunks: List[Dict]) -> str:
        """
        Build prompt with job description and RAG context.

        Args:
            job_description: Job posting text
            rag_chunks: Relevant resume chunks from RAG

        Returns:
            Formatted prompt string
        """
        # Format RAG chunks
        context_text = "USER'S ACTUAL WORK HISTORY (from RAG context):\n\n"
        for i, chunk in enumerate(rag_chunks, 1):
            context_text += f"[Chunk {i} - {chunk['metadata']['section']} - {Path(chunk['file_path']).name}]\n"
            context_text += f"{chunk['text']}\n\n"

        # Build full prompt
        prompt = f"""{self.system_prompt}

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

2. A 3-paragraph cover letter that:
   - Opens with enthusiasm for the specific role
   - Provides 2-3 concrete examples from their actual work history
   - Explains why they're a strong match (based on facts, not fluff)

Remember: ONLY use facts from their actual history. Do not invent experiences.

OUTPUT:"""

        return prompt

    def _generate_with_ollama(
        self, prompt: str, stream: bool = False
    ) -> Dict[str, str]:
        """
        Generate using Ollama API.

        Args:
            prompt: Full prompt text
            stream: Whether to stream response

        Returns:
            Generated resume and cover letter
        """
        import requests

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": stream,
            "options": {
                "temperature": self.temperature,
                "num_predict": self.max_tokens,
            },
        }

        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                stream=stream,
                timeout=120,
            )

            if stream:
                # Stream response
                full_response = ""
                for line in response.iter_lines():
                    if line:
                        chunk = json.loads(line)
                        if "response" in chunk:
                            full_response += chunk["response"]
                            # Yield chunks for UI streaming
                            yield {"chunk": chunk["response"], "done": False}

                yield {"chunk": "", "done": True}
            else:
                # Get full response
                response_data = response.json()
                full_response = response_data.get("response", "")

            # Parse response into resume and cover letter
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

    def _generate_with_mlx(self, prompt: str, stream: bool = False) -> Dict[str, str]:
        """
        Generate using MLX-LM server.

        Args:
            prompt: Full prompt text
            stream: Whether to stream response

        Returns:
            Generated resume and cover letter
        """
        import requests

        payload = {
            "prompt": prompt,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }

        try:
            response = requests.post(
                "http://localhost:8080/generate",
                json=payload,
                stream=stream,
                timeout=120,
            )

            if stream:
                full_response = ""
                for line in response.iter_lines():
                    if line:
                        chunk = json.loads(line)
                        if "token" in chunk:
                            full_response += chunk["token"]
                            yield {"chunk": chunk["token"], "done": False}

                yield {"chunk": "", "done": True}
            else:
                response_data = response.json()
                full_response = response_data.get("generated_text", "")

            resume, cover_letter = self._parse_response(full_response)

            return {"resume": resume, "cover_letter": cover_letter}

        except Exception as e:
            return {
                "resume": f"Error generating resume: {str(e)}",
                "cover_letter": f"Error generating cover letter: {str(e)}",
            }

    def _parse_response(self, response_text: str) -> tuple:
        """
        Parse LLM response into resume and cover letter.

        Args:
            response_text: Full LLM response

        Returns:
            Tuple of (resume_text, cover_letter_text)
        """
        # Look for section markers
        resume_start = response_text.find("**Tailored Resume**")
        cover_letter_start = response_text.find("**Cover Letter**")

        if resume_start == -1:
            resume_start = response_text.find("### Resume")
        if cover_letter_start == -1:
            cover_letter_start = response_text.find("### Cover Letter")

        # Extract sections
        if resume_start != -1 and cover_letter_start != -1:
            resume = response_text[resume_start:cover_letter_start].strip()
            cover_letter = response_text[cover_letter_start:].strip()
        elif resume_start != -1:
            resume = response_text[resume_start:].strip()
            cover_letter = (
                "Cover letter not generated. Please try again with a clearer prompt."
            )
        else:
            # Fallback: split by newlines
            sections = response_text.split("\n\n")
            resume = "\n\n".join(sections[: len(sections) // 2])
            cover_letter = "\n\n".join(sections[len(sections) // 2 :])

        return resume, cover_letter

    def list_available_models(self) -> List[str]:
        """List available models on Ollama"""
        if self.backend != "ollama":
            return []

        try:
            import requests

            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
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
    agent = get_llm_agent()
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
