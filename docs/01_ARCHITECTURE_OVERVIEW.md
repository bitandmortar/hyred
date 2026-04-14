# 01 Architecture Overview: Hyred

This document outlines the architecture, security posture, and active technology stack of Hyred based on rigorous inspection of the application state.

## C4 Model

### 1. Context
Hyred acts as a standalone local node for a job seeker. The User interacts with the web interface to submit documents and job descriptions. Hyred uses the host machine's resources exclusively, leveraging Ollama for text AI and a local MLX/OpenAI-compatible server for Vision AI. 

### 2. Container
The system consists of two primary active containers:
- **Hyred Frontend (UI):** Built on React 18 & Vite, running locally on port 3015. It handles document drag-and-drop, parameter configuration (tune/profile), rendering streaming responses, and displaying an ATS score gauge.
- **Hyred Backend (API API):** A FastAPI server running locally on port 8020. Exposes REST endpoints (`/status`, `/documents/upload`, `/generate`, `/export`). Serves as the orchestration layer between the UI, LanceDB, Ollama, and M1 Vision servers.

### 3. Component (Backend Breakdown)
- **FastAPI Core (`server.py`):** Accepts HTTP requests and delegates internal processing.
- **RAG Engine (`rag_engine.py`):** Ingests uploaded documents into the `my_documents` directory, calculates SHA256 hashes, splits texts into overlapping chunks, generates embeddings using `sentence-transformers`, and upserts vectors to `lancedb_data`.
- **LLM Agent (`llm_agent.py`):** Interfaces with Ollama locally, wrapping calls inside specific prompts mapped to the job description and user history. Enforces extreme hallucination limits.
- **Vision Service Link (`call_m1_vision`):** Calls to `http://192.168.1.159:9339` utilizing `Qwen2.5-VL-3B` to decode PDFs when `pdftoppm` fails or image interpretation is heavily favored.

### 4. Deployment
Hyred runs bare-metal on local Apple Silicon devices.
Dependencies include:
- Ollama CLI natively running on the host system.
- Node.js runtime natively executing Vite.
- Python 3.10+ virtual environment housing dependencies: `markitdown`, `lancedb`, `sentence-transformers`, `fastapi`, `httpx`.

## Security Posture
Hyred is structurally airgapped from the public cloud (when properly configured).
- All requests target `127.0.0.1` (Ollama) or local network endpoints `192.168.1.159` (M1 Vision node).
- Documents are never offloaded outside the local filesystem or local database.
- CORS policy is broadly permissive (`allow_origins=["*"]`) but scoped for entirely trusted execution on local isolated networking.

## Actual Technology Stack
*Derived directly from `package.json` and `server.py` imports:*
- **Backend:** Python + FastAPI + Uvicorn + httpx.
- **Database:** LanceDB + pyarrow (local embedded vector).
- **ML & AI:** 
   - `sentence-transformers` for offline embeddings.
   - Ollama for `llama3.2:3b`.
   - Optional local MLX endpoints.
- **Frontend:** React (`^18.2.0`), Vite (`^4.4.5`), TailwindCSS (`^3.3.3`), React DOM, React Markdown.
