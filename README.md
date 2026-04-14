# Hyred (formerly local-resume-builder)

## Overview
**Hyred** (Neural Resume Engine) is a local-first AI-powered application designed for tailoring resumes and cover letters with extreme privacy. It performs all processing on-device using a local LLM backend. The application matches a user's skills and prior experience against a job description, using RAG techniques to index background documents (like existing resumes or PDFs), ensuring honest and accurate, non-hallucinated tailored output.

## Problem Addressed
Job seekers need to tailor their resumes and cover letters to stand out against Applicant Tracking Systems (ATS). However, sending highly personal work histories or resumes to online cloud LLM providers (e.g., OpenAI, Anthropic) poses a data privacy risk. Hyred addresses this by running offline on Apple Silicon, generating professional output with zero data leakage.

## Approach & Capabilities
Hyred fuses a React/Vite-based frontend with a FastAPI backend.
- **Vision Parsing (M1 Vision):** Extracts content from uploaded resume PDFs/images using Qwen2.5-VL-3B-Instruct hosted locally.
- **RAG & Tailoring (Ollama):** Embeds and queries the user's extracted documents locally, feeding only factual work history alongside a job description into a local LLaMA 3.2 (3B) model.
- **ATS Optimization:** Scores the generated resume against the target job description and highlights keyword match gaps. 
- **Exporting:** Results are exported as markdown files.

## Installation & Setup Ensure you have Node.js and Python installed. 

### Backend Setup
1. Validate Ollama is installed and running locally with `llama3.2:3b`.
2. Validate M1 Vision endpoint is running (optional but required for PDF parsing).
3. From the `server/` directory:
```bash
pip install -r requirements.txt # (or install identical deps manually)
uvicorn server:app --host 0.0.0.0 --port 8020
```

### Frontend Setup
1. From the root directory:
```bash
npm install
npm run dev
```
2. The UI will stream LLM responses and ATS scores locally at `http://localhost:3015`.

## Usage
- Drag and drop your baseline documents (PDF/docx/Markdown) onto the UI to upload.
- Paste the description of the target role.
- Specify your preferred LLM and the desired tone (e.g., formal or conversational).
- Click **Generate Neural Match** to receive a tailored, ATS-ready markdown resume and a custom cover letter.
