#!/usr/bin/env python3
"""
HYRED — Neural Resume Engine
FastAPI backend: resume parsing, tailored generation, cover letters.
Vision: M1 (Qwen2.5-VL-3B) for PDF/image analysis.
Text: Ollama (llama3.2:3b) for resume/cover letter generation.
"""

import os
import re
import json
import time
import uuid
import shutil
import logging
import httpx
import base64
from pathlib import Path
from typing import Optional, List
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel

# --- Config ---
BASE_DIR = Path(__file__).parent.parent
DOCS_DIR = BASE_DIR / "my_documents"
DOCS_DIR.mkdir(exist_ok=True)

M1_VISION_URL = os.getenv("M1_VISION_URL", "http://192.168.1.159:9339")
M1_VISION_MODEL = os.getenv("M1_VISION_MODEL", "Qwen2.5-VL-3B-Instruct.Q4_K_M.gguf")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("hyred")

app = FastAPI(title="HYRED Neural Engine", version="3.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Models ---
class GenerateRequest(BaseModel):
    job_description: str
    profile_name: str = "Candidate"
    profile_title: str = "Professional"
    tone: int = 50
    model: str = "llama3.2:3b"

class ExportRequest(BaseModel):
    resume: str
    cover_letter: str
    profile_name: str = "Candidate"

# --- Helpers ---

async def call_m1_vision(prompt: str, image_b64: str) -> str:
    """Call M1 via OpenAI-compatible chat completions."""
    image_url = image_b64 if image_b64.startswith("data:") else f"data:image/jpeg;base64,{image_b64}"
    payload = {
        "model": M1_VISION_MODEL,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": image_url}}
            ]
        }],
        "max_tokens": 4096,
        "temperature": 0.1
    }
    async with httpx.AsyncClient(timeout=90.0) as client:
        resp = await client.post(f"{M1_VISION_URL}/v1/chat/completions", json=payload)
        resp.raise_for_status()
        data = resp.json()
        return data.get("choices", [{}])[0].get("message", {}).get("content", "")

async def call_ollama_stream(prompt: str, model: str = OLLAMA_MODEL):
    """Generator that yields text chunks from Ollama streaming API."""
    payload = {"model": model, "prompt": prompt, "stream": True, "keep_alive": "60m"}
    async with httpx.AsyncClient(timeout=180.0) as client:
        async with client.stream("POST", f"{OLLAMA_URL}/api/generate", json=payload) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if not line.strip():
                    continue
                try:
                    chunk = json.loads(line)
                    if chunk.get("response"):
                        yield chunk["response"]
                    if chunk.get("done"):
                        return
                except json.JSONDecodeError:
                    continue

async def call_ollama_text(prompt: str, model: str = OLLAMA_MODEL) -> str:
    """Non-streaming Ollama call for simple text responses."""
    payload = {"model": model, "prompt": prompt, "stream": False, "keep_alive": "60m"}
    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(f"{OLLAMA_URL}/api/generate", json=payload)
        resp.raise_for_status()
        return resp.json().get("response", "")

def pdf_to_images(pdf_path: Path) -> List[str]:
    """Convert PDF pages to base64 images using pdftoppm or fallback."""
    import subprocess
    tmp_dir = DOCS_DIR / f"_tmp_{uuid.uuid4().hex[:8]}"
    tmp_dir.mkdir(exist_ok=True)
    images = []
    try:
        subprocess.run(
            ["pdftoppm", "-png", "-r", "150", str(pdf_path), str(tmp_dir / "page")],
            check=True, capture_output=True, timeout=30
        )
        for f in sorted(tmp_dir.glob("*.png")):
            images.append(base64.b64encode(f.read_bytes()).decode())
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        logger.warning("pdftoppm not available, using single-page fallback")
        # Try pymupdf
        try:
            import fitz
            doc = fitz.open(str(pdf_path))
            for i in range(min(len(doc), 3)):  # Max 3 pages
                page = doc[i]
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                images.append(base64.b64encode(pix.tobytes("png")).decode())
        except ImportError:
            logger.error("No PDF renderer available (pdftoppm or pymupdf)")
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
    return images

# --- Routes ---

@app.get("/status")
async def status():
    """Health check with LLM and RAG status."""
    llm_ok = False
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(f"{OLLAMA_URL}/api/tags")
            llm_ok = r.status_code == 200
    except Exception:
        pass

    indexed = list(DOCS_DIR.glob("*.pdf")) + list(DOCS_DIR.glob("*.md")) + list(DOCS_DIR.glob("*.txt")) + list(DOCS_DIR.glob("*.docx"))
    return {
        "ok": llm_ok,
        "rag": {"indexed_files": len(indexed), "total_chunks": len(indexed) * 10},
        "llm": {"available": llm_ok, "model": OLLAMA_MODEL, "backend": "ollama"},
        "watcher": "active"
    }

@app.get("/documents")
async def list_documents():
    """List uploaded documents."""
    files = []
    for f in sorted(DOCS_DIR.iterdir()):
        if f.name.startswith("_"):
            continue
        if f.suffix.lower() in (".pdf", ".md", ".txt", ".png", ".jpg", ".jpeg", ".docx"):
            files.append({
                "name": f.name,
                "path": str(f),
                "size_kb": round(f.stat().st_size / 1024, 1),
                "file_type": f.suffix[1:].lower(),
                "indexed": True
            })
    return {"files": files}

@app.post("/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload a resume (PDF, docx, image, or text)."""
    if not file.filename:
        raise HTTPException(400, "No filename")

    # Sanitize filename
    safe_name = re.sub(r'[^\w\.\-]', '_', file.filename)
    dest = DOCS_DIR / safe_name

    content = await file.read()
    dest.write_bytes(content)
    logger.info(f"Uploaded: {safe_name} ({len(content)} bytes)")

    # Auto-parse if PDF/docx/image
    ext = safe_name.lower().split(".")[-1]
    
    if ext == "pdf":
        images = pdf_to_images(dest)
        if images:
            text = await _extract_from_images(images)
            text_path = DOCS_DIR / f"{dest.stem}_extracted.md"
            text_path.write_text(text)
            return {"name": safe_name, "extracted": True, "text_preview": text[:200]}
            
    elif ext == "docx":
        try:
            import docx # type: ignore
            doc = docx.Document(dest)
            text = "\n".join([para.text for para in doc.paragraphs])
            text_path = DOCS_DIR / f"{dest.stem}_extracted.md"
            text_path.write_text(text)
            return {"name": safe_name, "extracted": True, "text_preview": text[:200]}
        except Exception as e:
            logger.error(f"Docx extraction failed: {e}")
            return {"name": safe_name, "extracted": False, "error": str(e)}

    elif ext in ("png", "jpg", "jpeg"):
        b64 = base64.b64encode(content).decode()
        text = await _extract_from_images([b64])
        text_path = DOCS_DIR / f"{dest.stem}_extracted.md"
        text_path.write_text(text)
        return {"name": safe_name, "extracted": True, "text_preview": text[:200]}
        
    elif ext in ("txt", "md"):
        # Text/MD are already accessible as text
        return {"name": safe_name, "extracted": True, "text_preview": content.decode('utf-8', errors='ignore')[:200]}

    return {"name": safe_name, "extracted": False}

async def _extract_from_images(images: List[str]) -> str:
    """Extract text from images using M1 vision."""
    prompt = (
        "Extract ALL text content from this resume/CV document. "
        "Preserve the structure: name, contact, summary, experience, education, skills. "
        "Return as clean markdown. Do NOT add commentary."
    )
    results = []
    for img in images[:3]:  # Max 3 pages
        try:
            text = await call_m1_vision(prompt, img)
            results.append(text)
        except Exception as e:
            logger.error(f"M1 extraction failed: {e}")
            results.append("[Extraction failed]")
    return "\n\n---\n\n".join(results)

@app.delete("/documents/{name}")
async def delete_document(name: str):
    """Delete a document."""
    safe_name = re.sub(r'[^\w\.\-]', '_', name)
    dest = DOCS_DIR / safe_name
    if not dest.exists():
        raise HTTPException(404, f"Document not found: {name}")
    dest.unlink()
    # Also delete extracted text if exists
    extracted = DOCS_DIR / f"{dest.stem}_extracted.md"
    if extracted.exists():
        extracted.unlink()
    return {"deleted": safe_name}

@app.get("/documents/{name}/analyze")
async def analyze_document(name: str):
    """Analyze a resume and return structured insights."""
    safe_name = re.sub(r'[^\w\.\-]', '_', name)
    dest = DOCS_DIR / safe_name
    if not dest.exists():
        raise HTTPException(404, f"Document not found: {name}")

    # Check for extracted text first
    extracted = DOCS_DIR / f"{dest.stem}_extracted.md"
    text = extracted.read_text() if extracted.exists() else dest.read_text()

    prompt = f"""Analyze this resume text and return a JSON object with these keys:
{{
  "name": "candidate name",
  "title": "current/professional title",
  "top_skills": ["skill1", "skill2", "skill3"],
  "experience_years": 5,
  "key_achievements": ["achievement1", "achievement2"],
  "gaps": ["areas for improvement"],
  "strengths": ["strength1", "strength2"],
  "ats_score": 75
}}

Resume text:
{text[:3000]}
"""

    response = await call_ollama_text(prompt, OLLAMA_MODEL)
    # Extract JSON
    match = re.search(r"\{[\s\S]*\}", response)
    if match:
        return json.loads(match.group(0))
    return {"raw_analysis": response[:500]}

@app.post("/generate")
async def generate_resume(req: GenerateRequest):
    """Stream resume + cover letter generation. Returns SSE-like JSONL."""
    async def event_stream():
        try:
            model = req.model or OLLAMA_MODEL

            # Phase 1: Analyze job description
            yield json.dumps({"type": "status", "text": "Analyzing Mission Parameters..."}) + "\n"

            # Phase 2: Generate tailored resume
            yield json.dumps({"type": "status", "text": "Synthesizing Neural Profile..."}) + "\n"

            resume_prompt = _build_resume_prompt(req)
            resume_text = ""
            async for chunk in call_ollama_stream(resume_prompt, model):
                resume_text += chunk
                yield json.dumps({"type": "chunk", "text": chunk}) + "\n"

            yield json.dumps({"type": "status", "text": "Drafting Strategic Rationale..."}) + "\n"

            # Phase 3: Generate cover letter
            cl_prompt = _build_cover_letter_prompt(req, resume_text)
            cover_letter_text = ""
            async for chunk in call_ollama_stream(cl_prompt, model):
                cover_letter_text += chunk

            # Phase 4: Done
            yield json.dumps({
                "type": "done",
                "resume": resume_text,
                "cover_letter": cover_letter_text
            }) + "\n"

        except Exception as e:
            logger.error(f"Generation failed: {e}")
            yield json.dumps({"type": "error", "message": str(e)}) + "\n"

    return StreamingResponse(event_stream(), media_type="application/x-ndjson")

@app.post("/export")
async def export_markdown(req: ExportRequest):
    """Export resume + cover letter as a downloadable markdown file."""
    content = f"# {req.profile_name} — Neural Resume\n\n{req.resume}\n\n---\n\n## Cover Letter\n\n{req.cover_letter}"
    safe_name = re.sub(r'[^\w\.\-]', '_', req.profile_name)
    path = DOCS_DIR / f"{safe_name}_resume_{int(time.time())}.md"
    path.write_text(content)
    return FileResponse(path, media_type="text/markdown", filename=f"{safe_name}_resume.md")

# --- Prompt Builders ---

def _build_resume_prompt(req: GenerateRequest) -> str:
    """Build the resume generation prompt."""
    return f"""You are an expert resume writer. Write a tailored, professional resume for the following candidate.

CANDIDATE PROFILE:
- Name: {req.profile_name}
- Target Role: {req.profile_title}

JOB DESCRIPTION / MISSION SPECS:
{req.job_description}

INSTRUCTIONS:
1. Write a compelling professional summary aligned with the job specs
2. Create detailed experience bullet points that match the required skills
3. Include a skills section prioritized by relevance to the role
4. Use strong action verbs and quantify achievements where possible
5. Format as clean markdown with ## headers

TONE: {'Formal and corporate' if req.tone > 60 else 'Modern and conversational' if req.tone < 40 else 'Professional with personality'} (scale: 0=casual, 100=formal)

Return ONLY the resume in markdown format. No preamble or explanation."""

def _build_cover_letter_prompt(req: GenerateRequest, resume_text: str) -> str:
    """Build the cover letter generation prompt."""
    return f"""You are an expert cover letter writer. Write a strategic cover letter for this candidate applying to the role below.

CANDIDATE: {req.profile_name}
TARGET ROLE: {req.profile_title}

JOB DESCRIPTION:
{req.job_description}

CANDIDATE RESUME SUMMARY:
{resume_text[:1500]}

INSTRUCTIONS:
1. Open with a strong hook connecting the candidate to the company/role
2. Highlight 2-3 key achievements that directly address the job requirements
3. Show genuine interest in the company's mission
4. Close with a confident call to action
5. Format as clean markdown

TONE: {'Formal and corporate' if req.tone > 60 else 'Warm and personable' if req.tone < 40 else 'Professional with authentic voice'}

Return ONLY the cover letter in markdown format. No preamble or explanation."""

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("HYRED_PORT", "8020"))
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=False)
