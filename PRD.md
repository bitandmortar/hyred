# Hyred Product Requirements Document (PRD)

## 1. Product Goals
Hyred is a local-first, privacy-respecting AI resume and cover letter builder. It uses on-device LLMs (Ollama) and local document parsing/RAG (LanceDB, Qwen2.5-VL) to analyze a candidate's background and tailor their professional documents to match specific job descriptions. The primary goal is to empower users to generate optimized, ATS-friendly applications without exposing personal data to remote cloud processors.

## 2. User Stories
- **As a privacy-focused job seeker**, I want to upload my baseline resume and get it parsed without my data leaving my machine, so I can keep my information secure.
- **As an applicant adapting to ATS**, I want to provide a job description and receive a tailored resume and cover letter that intelligently emphasize my relevant real-world experiences.
- **As a user running Apple Silicon**, I want the tool to utilize my local hardware smoothly for both vision tasks (extracting PDF data) and text generation.
- **As a job seeker**, I want to be immediately notified of ATS gaps so I can see what keywords I am lacking compared to the target role.

## 3. Key Features
- **Local Document Ingestion:** Supports `.pdf`, `.docx`, `.png`, `.jpg`, `.txt`, and `.md` file drops.
- **Vision-based Extraction:** Uses an M1 Vision node (`Qwen2.5-VL-3B`) to extract clean markdown from uploaded PDF/image resumes.
- **Semantic RAG Engine:** Chunks uploaded documents and stores them in a local LanceDB instance using semantic embeddings, allowing dynamic sampling of the user's history.
- **Neural Mirror Generation:** Streams tailored resumes and cover letters straight to the UI, strictly grounded in the factual context stored in LanceDB.
- **ATS Analytics:** Instantly runs rule-based checks scoring the matching keywords between the parsed job constraints and the generated resume.
- **Markdown Exports:** One-click markdown export of both the customized resume and the cover letter.

## 4. Technical Requirements
- **Frontend:** React 18, Vite 4, TailwindCSS for styling and Glassmorphism design elements. Connects to the backend at port `8020`.
- **Backend:** Python + FastAPI. Requires `uvicorn`.
- **LLM Integrations:**
  - `httpx` asynchronous calls targeting Ollama running at `127.0.0.1:11434`. Model: `llama3.2:3b`.
  - `httpx` asynchronous calls targeting M1 Vision node at `192.168.1.159:9339`.
- **Database:** Local LanceDB mapping in the `lancedb_data/` folder.
- **File Watcher:** Must observe `my_documents/` folder.

## 5. Non-Functional Requirements
- **Privacy:** 100% on-device local network execution. Zero cloud ingress/egress for PII.
- **Performance:** UI updates must stream cleanly using Server-Sent Events (SSE) or JSONL streaming to reduce perceived latency.
- **Aesthetics:** The UI should embody a "Neural Mirror" aesthetic, employing Anthropic fonts, smooth visual feedback loops, and an intuitive HUD layout.

## 6. Success Metrics
- Average generation time of < 2 minutes (depending on local hardware limitations).
- High relevance and ATS pass rate using the internal heuristic scoring scale.
- Zero external data leaks.
