# hyred

**Local-first CV & Cover Letter Generator**

> Everything runs on your machine. No cloud APIs. No tracking. No data leaves your network.

Paste a job URL or description, let hyred scrape it, parse it, score it against your work history, and generate a tailored resume and cover letter — all via a local Ollama model running on your hardware.

---

## ✨ Features

### Core Generation
- **RAG-powered tailoring** — your documents are chunked, embedded, and stored in LanceDB; the top 10 most relevant chunks are retrieved per generation
- **Local LLM inference** — Ollama backend (llama3.2, mistral, qwen2.5, or any model you have pulled); MLX-LM supported as alternative
- **Strict anti-hallucination prompt** — LLM is instructed to use only facts from your actual work history
- **DOCX + Markdown export** — download as `.md` or a properly formatted `.docx` (headings, bold, bullets, page margins)
- **Tone slider** — maps 0 → formal (temp 0.3) through 100 → conversational (temp 0.85)

### ATS Keyword Scorer
- Frequency-weighted keyword extraction from the JD
- Scores generated output 0–100 against top 50 JD terms
- Displays matched keywords (green pills) and missing keywords (red pills) post-generation

### Cover Letter Config
- Persisted preferences in `hyred_data/cover_letter_config.json`
- Opening style: hook / direct / question / achievement
- Enthusiasm slider: Measured → Professional → Balanced → Enthusiastic → Passionate
- Forbidden phrases list, max word count, custom sign-off, optional P.S.
- Config injected as a system prompt addendum on every generation

### Refinement Loop
- After generation, a "Refine" expander lets you give targeted feedback
- Prior output is fed back into the LLM with your notes: *"Shorten by 20%, drop Cerberus project, more emphasis on Rust"*
- Each refinement is saved as a new version in history

### Version History
- Every generation auto-saved to SQLite (`hyred_data/version_history.db`)
- Stores: company, role, ATS score, tone, model, full markdown content, timestamp
- Browse, compare, reload any past version into session for further refinement

### Job Queue & Comparison Pipeline
- Bulk-import job URLs (one per line) or raw JD blocks separated by `---`
- Each entry is scraped → structured-parsed → ATS pre-scored → salary-annotated → ghost-checked
- Sort by ATS pre-score, seniority, location, or date
- Filter by remote policy or hide stale/ghost listings
- Location clustering (Remote, NYC, SF, London, etc.)
- Select jobs for generation; selected queue pre-fills main page

### Structured JD Parsing
- Calls local Ollama to extract a typed object from each JD: required skills, nice-to-have, tech stack, seniority, remote policy, salary range, posted date
- Regex heuristic fallback if the model doesn't return valid JSON
- Parsed data feeds the ATS pre-scorer in the Job Queue

### Salary Intelligence
- Scrapes `levels.fyi` for market comp data (title + location)
- Extracts stated salary range from JD text as fallback
- Displays p25 / median / p75 as an info banner before generation

### Ghost Job Detector
- Parses posting date from JD text and URL patterns
- Detects evergreen / talent-pool signals in the description
- Verdicts: fresh (≤7d) / aging (≤45d) / stale (≤90d) / ghost (>90d or evergreen)
- Warning banner shown when staleness is detected

### Job Scraper — Site-Specific Extractors
- LinkedIn, Indeed, ZipRecruiter, Glassdoor: dedicated parsers with JSON-LD `JobPosting` extraction
- Greenhouse, Lever, Workday: generic extractor with multi-selector fallback
- Auto-detects site from URL; routes accordingly
- Auto-fills Company and Role fields from scraped data

### Application Tracker
- Full lifecycle: drafted → submitted → phone screen → technical → final round → offer / rejected / withdrawn
- Kanban board grouped by stage
- Per-application notes, follow-up reminders, URL link
- Stats tab: total applied, response rate, offers, in-progress count

### Interview Prep
- Generates role-specific questions: behavioral (STAR), technical, situational, culture fit, "why us"
- Answer by voice (Whisper) or text
- Whisper transcription via `whisper.cpp` (Apple Silicon native, fastest) or `openai-whisper` Python package
- Each answer scored by Ollama: relevance, specificity, JD alignment, structure
- Score + critique + one improvement suggestion displayed per question

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt

# Playwright browsers (for local scraping)
playwright install chromium
```

### 2. Start Ollama

```bash
ollama serve

# Pull a model (if not already done)
ollama pull llama3.2
```

### 3. Add Your Documents

```bash
mkdir -p ./my_documents
cp ~/Documents/resume.pdf ./my_documents/
cp ~/Documents/cv.docx ./my_documents/
# Add any: PDF, DOCX, MD, TXT — all auto-indexed on startup
```

### 4. Run

```bash
streamlit run main_ui.py --server.port=8501 --server.address=0.0.0.0
```

Open **http://localhost:8501**

### 5. First Run Checklist

1. Enter your name in the sidebar **Profile** section
2. Confirm the Ollama model you want to use
3. Drop your resume/CV files into the upload zone or place them in `./my_documents/`
4. Wait for the RAG engine to index them (status bar shows chunk count)
5. Paste a job URL or description and click **Generate**

---

## 📁 File Structure

```
hyred/
│
├── main_ui.py                  # Main Streamlit app
├── rag_engine.py               # Document ingestion & vector search (LanceDB)
├── llm_agent.py                # Ollama / MLX-LM generation
├── job_scraper.py              # Site-specific + generic job scraper
├── file_watcher.py             # Watchdog auto-reindex on file change
├── ats_scorer.py               # Frequency-weighted ATS keyword scorer
├── export_utils.py             # Markdown → DOCX converter
├── cover_letter_config.py      # CL preferences (persisted JSON)
├── jd_parser.py                # Structured JD extraction via Ollama
├── salary_scraper.py           # levels.fyi scraper + JD salary extraction
├── ghost_detector.py           # Job posting staleness detector
├── job_queue.py                # Batch job pipeline (SQLite)
├── version_history.py          # Generation log (SQLite)
│
├── pages/
│   ├── 01_Import_Documents.py
│   ├── 02_Resume_Tools.py
│   ├── 03_Auto_Generate.py
│   ├── 04_Application_Tracker.py   # Kanban lifecycle tracker
│   ├── 05_Interview_Prep.py        # Whisper + Ollama Q&A loop
│   ├── 06_Skills_Gap.py
│   ├── 07_CV_Versioning.py
│   ├── 08_Job_Archive.py
│   ├── 09_Job_Queue.py             # Bulk import & comparison pipeline
│   └── 10_Version_History.py       # All saved generations
│
├── my_documents/               # Your resume/CV files (never exposed)
├── lancedb_data/               # Local vector database (auto-generated)
├── hyred_data/                 # App data
│   ├── version_history.db      # SQLite — generation log
│   ├── job_queue.db            # SQLite — job pipeline
│   ├── applications.db         # SQLite — application tracker
│   └── cover_letter_config.json
│
└── requirements.txt
```

---

## 🔄 Typical Workflow

### Single Job
1. Paste a URL or job description into the main input
2. If URL: click **Scrape** — company and role auto-fill
3. Review the ghost job warning and salary banner (if data found)
4. Click **Generate** — RAG retrieves relevant chunks, LLM generates
5. Review the ATS score panel — note any missing keywords
6. Use the **Refine** expander to give feedback and re-generate
7. Download as `.md` or `.docx`

### Batch Mode (Job Queue)
1. Go to **🗂️ Job Queue → ➕ Add Jobs**
2. Paste multiple URLs (one per line) and click **Process**
3. Each job is scraped, parsed, ATS pre-scored, salary-annotated, and ghost-checked
4. Go to **📊 Compare All** — sort by ATS score, filter by remote policy
5. Select the jobs worth applying to
6. Open each from **✅ Selected Queue** — it pre-fills the main page
7. Generate, refine, download, track in **📋 Application Tracker**

### Interview Prep
1. Go to **🎙️ Interview Prep** (page 05)
2. The JD from your last session is pre-loaded, or paste a new one
3. Click **Generate Questions**
4. Answer each question by voice (upload `.wav`/`.mp3`) or text
5. Click **Score** — Ollama gives you a rating, critique, and one improvement suggestion

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Streamlit App                            │
│                        main_ui.py  :8501                        │
└──────┬──────────┬──────────┬──────────┬──────────┬─────────────┘
       │          │          │          │          │
       ▼          ▼          ▼          ▼          ▼
  ┌─────────┐ ┌────────┐ ┌───────┐ ┌───────┐ ┌──────────┐
  │   RAG   │ │  LLM   │ │Scraper│ │ ATS   │ │ SQLite   │
  │ Engine  │ │ Agent  │ │       │ │Scorer │ │ (3 DBs)  │
  └────┬────┘ └───┬────┘ └───┬───┘ └───────┘ └──────────┘
       │          │          │
       ▼          ▼          ▼
  ┌─────────┐ ┌────────┐ ┌──────────────────────────────┐
  │ LanceDB │ │ Ollama │ │ LinkedIn / Indeed / Glassdoor │
  │ (local) │ │ :11434 │ │ ZipRecruiter / Greenhouse     │
  └─────────┘ └────────┘ │ Lever / Workday / Generic     │
                          └──────────────────────────────┘
```

**Data stores:**
- `lancedb_data/` — vector embeddings for RAG (Apache Arrow)
- `hyred_data/version_history.db` — every generation, auto-saved
- `hyred_data/job_queue.db` — batch job pipeline
- `hyred_data/applications.db` — application lifecycle tracker
- `hyred_data/cover_letter_config.json` — persisted CL preferences

---

## ⚙️ Configuration

### Sidebar Settings (persisted per session)
| Setting | Description |
|---|---|
| Your Name | Used in exported filenames |
| Target Title | Informational — helps frame prompts |
| Ollama Model | Populated live from `ollama list`; default `llama3.2` |
| Cover Letter Tone | 0 = Formal (temp 0.3) → 100 = Conversational (temp 0.85) |
| Cover Letter Style | Opening hook style, enthusiasm, max words, forbidden phrases |
| NotebookLM toggle | Optional — requires Google authentication |

### Cover Letter Config (persisted to JSON)
| Option | Values |
|---|---|
| Opening style | `hook` / `direct` / `question` / `achievement` |
| Enthusiasm | 0 Measured → 25 Professional → 50 Balanced → 75 Enthusiastic → 100 Passionate |
| Max words | 150–600 (default 350) |
| Sign-off | Any string (default "Best regards") |
| Forbidden phrases | One per line — LLM will never use these |
| Custom instructions | Free-form additional directives |

---

## 🔧 Optional Enhancements

### Better PDF Ingestion (docling)
IBM's `docling` library does layout-aware PDF extraction — preserves table structure, section headers, bullet hierarchy. Recommended if you have complex PDF CVs.
```bash
pip install docling
```
Then swap `MarkItDown` for `docling` in `rag_engine.py`.

### Voice Interview Prep (Whisper)
```bash
# Option 1: Apple Silicon native (fastest)
brew install whisper-cpp

# Option 2: Python package
pip install openai-whisper
```
Both are auto-detected by `pages/05_Interview_Prep.py`.

### Cloudflare Tunnel (expose to a custom domain)
```bash
# Add to your cloudflared config.yml
ingress:
  - hostname: hyred.yourdomain.com
    service: http://localhost:8501

# Restart tunnel
supervisorctl -s unix:///tmp/pastyche_supervisor.sock restart cloudflared
```

---

## 🔧 Troubleshooting

### Ollama not connecting
```bash
ollama serve
ollama pull llama3.2   # if no model pulled yet
```

### Playwright scraping fails
```bash
playwright install chromium
python job_scraper.py  # test scrape
```

### LanceDB errors / stale index
```bash
rm -rf ./lancedb_data
# Re-index on next startup, or click refresh in the UI
```

### Port 8501 already in use
```bash
lsof -ti :8501 | xargs kill -9
streamlit run main_ui.py --server.port=8501
```

### Whisper not found
```bash
# Fast (Apple Silicon):
brew install whisper-cpp

# Or Python:
pip install openai-whisper
```

---

## 📊 Performance (Apple Silicon M-series)

| Operation | Approx. time |
|---|---|
| Document indexing (10 pages) | ~5s |
| Embedding generation (500 words) | ~0.5s |
| Vector search (10K chunks) | ~50ms |
| JD structured parse (llama3.2) | ~8s |
| Resume + CL generation (llama3.2) | ~15–30s |
| Whisper transcription (base, 1 min audio) | ~3s |
| Job scraping (Greenhouse/Lever) | ~3s |
| Job scraping (LinkedIn/Glassdoor) | partial — login required |

---

## 🛡️ Privacy

All of the following run entirely on-device:

- Document conversion (MarkItDown)
- Text embedding (sentence-transformers / all-MiniLM-L6-v2)
- Vector storage (LanceDB)
- LLM inference (Ollama)
- Job scraping (Playwright / requests + BeautifulSoup)
- File monitoring (watchdog)
- All SQLite databases

The optional NotebookLM integration is the only feature that touches an external service, and it is **off by default** with an explicit toggle in the sidebar.

---

## 📦 Dependencies

| Package | Purpose |
|---|---|
| `streamlit` | Frontend UI |
| `lancedb` + `pyarrow` | Local vector database |
| `sentence-transformers` + `torch` | Local embeddings |
| `markitdown` | Universal document → Markdown converter |
| `playwright` + `beautifulsoup4` + `requests` | Job scraping |
| `watchdog` | File system monitoring |
| `python-docx` | DOCX export |
| `python-dotenv` | Environment config |

**Optional:**
- `openai-whisper` — interview prep voice transcription
- `whisper-cpp` (brew) — faster Apple Silicon native alternative
- `docling` — better layout-aware PDF ingestion

---

## 📄 License

MIT — build your own private job search engine.

---

*Built by [bitandmortar](https://github.com/bitandmortar)*
