# hyred

**CV & Cover Letter Generator**

> git + hyred = Get Hired

Everything runs natively on your machine. No external APIs. Complete privacy.

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Navigate to app directory
cd /Volumes/OMNI_01/10_SOURCE/10_Front_Gate/public/apps/local-resume-builder

# Install Python packages
pip install -r requirements.txt

# Install Playwright browsers (for local scraping)
playwright install
```

### 2. Start Ollama (Local LLM Backend)

```bash
# Start Ollama server
ollama serve

# In another terminal, pull a model (if not already installed)
ollama pull llama3.2
```

### 3. Create Your Documents Directory

```bash
# Create directory for your resume/CV files
mkdir -p ./my_documents

# Add your documents:
# - Current resume (PDF, DOCX, or MD)
# - Past project descriptions
# - Performance reviews
# - Any work history documents
cp ~/Documents/resume.pdf ./my_documents/
cp ~/Documents/cv.docx ./my_documents/
```

### 4. Run the Application

```bash
# Start Streamlit app on localhost:8501
streamlit run main_ui.py --server.port=8501 --server.address=0.0.0.0
```

### 5. Access the App

Open your browser to: **http://localhost:8501**

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                 Cloudflare Tunnel                        │
│            (cloudflared on your network)                │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
        ┌────────────────────────┐
        │   resume.yourdomain.com │
        └───────────┬────────────┘
                    │
                    ▼
    ┌───────────────────────────────┐
    │   Streamlit App (localhost:8501) │
    │   - main_ui.py                 │
    └───────────┬───────────────────┘
                │
        ┌───────┼───────┬───────────┐
        │       │       │           │
        ▼       ▼       ▼           ▼
   ┌────────┐ ┌──────┐ ┌────────┐ ┌──────────┐
   │  RAG   │ │ LLM  │ │ Scraper│ │ Watcher  │
   │ Engine │ │Agent │ │ Local  │ │ File     │
   └───┬────┘ └──┬───┘ └───┬────┘ └────┬─────┘
       │         │         │           │
       ▼         ▼         ▼           ▼
   ┌────────┐ ┌──────┐ ┌────────┐ ┌──────────┐
   │LanceDB │ │Ollama│ │Playwright│ │watchdog │
   │(local) │ │local │ │ (local) │ │ (local) │
   └────────┘ └──────┘ └────────┘ └──────────┘
```

---

## 📁 Directory Structure

```
/Local-App-Builder
│
├── /my_documents/          # Your resume files (NEVER exposed publicly)
│   ├── resume.pdf
│   ├── cv.docx
│   ├── projects.md
│   └── work_history.xlsx
│
├── /lancedb_data/          # Local vector database (auto-generated)
│   ├── resume_chunks.lance
│   └── index_metadata.json
│
├── main_ui.py              # Streamlit frontend (localhost:8501)
├── rag_engine.py           # Document ingestion & vector search
├── job_scraper.py          # Local Playwright scraper
├── llm_agent.py            # Ollama/MLX-LM integration
├── file_watcher.py         # Watchdog for auto-reindex
└── requirements.txt        # Python dependencies
```

---

## 🔧 Component Details

### 1. `job_scraper.py` - Local HTML Parser

**Purpose:** Extract job descriptions from URLs without external APIs

**Features:**
- Uses local Playwright instance (headless Chromium)
- Bypasses JavaScript-heavy sites (Greenhouse, Lever, LinkedIn)
- BeautifulSoup4 for HTML parsing
- Fallback to manual paste if scraping fails

**Usage:**
```python
from job_scraper import LocalJobScraper

scraper = LocalJobScraper()
result = scraper.scrape_url("https://company.greenhouse.io/jobs/123")

print(result["job_title"])
print(result["job_description"])
```

### 2. `rag_engine.py` - Local Knowledge Base

**Purpose:** Convert documents to embeddings, store in LanceDB, retrieve relevant chunks

**Features:**
- MarkItDown for universal document conversion (PDF, DOCX, XLSX → Markdown)
- sentence-transformers for local embeddings (all-MiniLM-L6-v2)
- LanceDB for fast vector storage (Apache Arrow-based)
- Automatic chunking with overlap (~500 words/chunk)
- Section detection (experience, education, skills, projects)

**Usage:**
```python
from rag_engine import get_rag_engine

engine = get_rag_engine()
engine.index_all_documents()  # Index ./my_documents/

# Search for relevant chunks
results = engine.search("Python data engineering", k=10)
```

### 3. `file_watcher.py` - Hot Reload

**Purpose:** Automatically re-index documents when they change

**Features:**
- Watchdog library for file system monitoring
- Debouncing to avoid rapid re-indexing
- Supports: PDF, DOCX, XLSX, PPTX, HTML, MD, TXT
- Runs in background thread (non-blocking)

**Usage:**
```python
from file_watcher import start_file_watcher

def on_change(file_path):
    print(f"File changed: {file_path}")
    # Re-index automatically

start_file_watcher("./my_documents", on_change)
```

### 4. `llm_agent.py` - Local Generation

**Purpose:** Generate tailored resume/cover letter using local LLM

**Features:**
- Ollama backend (llama3.2, mistral) or MLX-LM
- Strict system prompt: NO hallucination, use ONLY RAG facts
- ATS-friendly formatting
- Quantified achievements from actual history

**Usage:**
```python
from llm_agent import get_llm_agent

agent = get_llm_agent()
result = agent.generate_resume_and_cover_letter(
    job_description,
    rag_chunks
)

print(result["resume"])
print(result["cover_letter"])
```

### 5. `main_ui.py` - Streamlit Dashboard

**Purpose:** User interface for the entire workflow

**Features:**
- Dual input: URL scraping OR manual paste
- Real-time status bar (indexed files, chunks, watcher status)
- RAG context preview (see what chunks were retrieved)
- Tabbed output (Resume / Cover Letter)
- Download buttons (.md format)

---

## 🔒 Cloudflare Tunnel Configuration

### Secure Exposure via Cloudflare Tunnel

**IMPORTANT:** This app is designed to run locally and be exposed securely via your existing Cloudflare Tunnel.

#### Step 1: Ensure Streamlit Binds Correctly

```bash
# Run Streamlit with correct binding
streamlit run main_ui.py \
  --server.port=8501 \
  --server.address=0.0.0.0 \
  --server.headless=true \
  --browser.gatherUsageStats=false
```

#### Step 2: Add to Cloudflare Tunnel Config

Edit your cloudflared config (`/Volumes/OMNI_01/50_Ops/06_CLOUDFLARED/cloudflared/config.yml`):

```yaml
ingress:
  - hostname: resume.yourdomain.com
    service: http://localhost:8501
  
  - hostname: your-other-apps.yourdomain.com
    service: http://localhost:8080
  
  - service: http_status:404  # Catch-all
```

#### Step 3: Restart Cloudflare Tunnel

```bash
# Restart cloudflared via supervisorctl
supervisorctl -s unix:///tmp/pastyche_supervisor.sock restart cloudflared
```

#### Step 4: Access Securely

Your app is now accessible at: **https://resume.yourdomain.com**

**Security Notes:**
- ✅ All data stays on your local network
- ✅ Cloudflare Tunnel provides encryption in transit
- ✅ No public CORS permissions needed
- ✅ Streamlit's built-in XSRF protection is active
- ✅ No external API calls from the app

---

## 🛡️ Security & Privacy Guarantees

### What NEVER Leaves Your Network:
- ❌ No document content sent to cloud
- ❌ No embeddings generated externally
- ❌ No job descriptions sent to APIs
- ❌ No generated resumes stored externally
- ❌ No browsing history tracked

### What Runs 100% Locally:
- ✅ MarkItDown (document conversion)
- ✅ sentence-transformers (embeddings)
- ✅ LanceDB (vector storage)
- ✅ Ollama/MLX-LM (LLM inference)
- ✅ Playwright (web scraping)
- ✅ Watchdog (file monitoring)

---

## 📊 Performance Benchmarks (M2 Mac)

| Operation | Time |
|-----------|------|
| Document indexing (10 pages) | ~5 seconds |
| Embedding generation (500 words) | ~0.5 seconds |
| Vector search (10K chunks) | ~50ms |
| Resume generation (llama3.2) | ~15 seconds |
| Job scraping (Greenhouse) | ~3 seconds |

---

## 🔧 Troubleshooting

### Ollama Not Connecting

```bash
# Check if Ollama is running
ollama list

# If not running, start it
ollama serve

# Pull a model if needed
ollama pull llama3.2
```

### Playwright Scraping Fails

```bash
# Install Playwright browsers
playwright install

# Test scraping
python job_scraper.py
```

### LanceDB Errors

```bash
# Clear and rebuild vector database
rm -rf ./lancedb_data
python rag_engine.py  # Re-index all documents
```

### Streamlit Port Already in Use

```bash
# Find process using port 8501
lsof -i :8501

# Kill the process
kill -9 <PID>

# Or use a different port
streamlit run main_ui.py --server.port=8502
```

---

## 📝 Example Workflow

1. **Add your documents** to `./my_documents/`
   - Current resume (PDF/DOCX)
   - Project descriptions (MD)
   - Performance reviews (PDF)

2. **Wait for auto-indexing** (or refresh in UI)
   - File Watcher detects new files
   - RAG Engine converts → chunks → embeds → stores

3. **Enter job description**
   - Paste URL (auto-scraped) OR
   - Paste full job description

4. **Click Generate**
   - RAG searches for relevant chunks (top 10)
   - LLM generates tailored resume + cover letter
   - Uses ONLY facts from your actual history

5. **Download & Apply**
   - Download as .md files
   - Convert to PDF if needed
   - Apply to job!

---

## 🎯 Best Practices

### For Best Resume Matching:
1. **Quantify your work:** Include numbers, metrics, scale
2. **Be specific:** List exact tools, technologies, frameworks
3. **Update regularly:** Add new projects as you complete them
4. **Include context:** Project goals, your role, outcomes

### For Best Generation Results:
1. **Provide detailed job descriptions:** More context = better matching
2. **Review RAG chunks:** Ensure relevant experience was retrieved
3. **Edit generated output:** LLM provides draft, you refine
4. **Verify facts:** Double-check all claims match your actual history

---

## 📄 License

MIT License - Build your private resume builder, modify as needed.

---

## 🙏 Credits

Built with:
- **Streamlit** - Frontend UI
- **LanceDB** - Local vector database
- **sentence-transformers** - Local embeddings
- **MarkItDown** - Microsoft's universal document converter
- **Playwright** - Local browser automation
- **Ollama** - Local LLM runtime
- **Watchdog** - File system monitoring

---

**Made with ❤️**
