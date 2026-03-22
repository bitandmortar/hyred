# 🚀 Local Resume Builder - Complete Setup Guide

**Zero-Data-Leak Resume & Cover Letter Tailoring for M2 Mac**

---

## 📋 Pre-Flight Checklist

Before starting, ensure you have:

- [ ] M2 Mac (Apple Silicon) - optimized for MLX/Ollama
- [ ] Python 3.11+ installed
- [ ] Homebrew installed
- [ ] Ollama installed (`brew install ollama`)
- [ ] At least 8GB RAM (16GB recommended for larger models)
- [ ] At least 10GB free disk space

---

## 🔧 Step-by-Step Setup

### Step 1: Install System Dependencies

```bash
# Install Ollama (local LLM runtime)
brew install ollama

# Install Playwright (local browser automation)
brew install playwright-cli

# Install Python dependencies (if not already)
brew install python@3.11
```

### Step 2: Navigate to App Directory

```bash
cd /Volumes/OMNI_01/10_SOURCE/10_Front_Gate/public/apps/local-resume-builder
```

### Step 3: Install Python Packages

```bash
pip install -r requirements.txt
```

**Expected output:**
```
Successfully installed streamlit-1.32.0 lancedb-0.5.1 sentence-transformers-2.3.1 ...
```

### Step 4: Install Playwright Browsers

```bash
playwright install
```

This installs Chromium for local web scraping (no external APIs needed).

### Step 5: Pull Ollama Model

```bash
# Pull llama3.2 (3B parameters - fast on M2)
ollama pull llama3.2

# Alternative: Pull mistral (7B parameters - better quality, slower)
# ollama pull mistral
```

**Expected output:**
```
pulling manifest
pulling llama3.2... 100%
success
```

### Step 6: Create Documents Directory

```bash
mkdir -p ./my_documents

# Add your resume/CV files
cp ~/Documents/resume.pdf ./my_documents/
cp ~/Documents/cv.docx ./my_documents/
cp ~/Documents/projects.md ./my_documents/
```

**Supported file types:**
- `.pdf` - PDF resumes/CVs
- `.docx` - Word documents
- `.xlsx` - Excel spreadsheets (project lists, etc.)
- `.pptx` - PowerPoint presentations
- `.md` - Markdown files
- `.txt` - Plain text
- `.html` - Web pages

### Step 7: Start the Application

**Option A: Use the startup script (recommended)**

```bash
./start.sh
```

**Option B: Manual start**

```bash
# Start Ollama (if not already running)
ollama serve &

# Start Streamlit
streamlit run main_ui.py --server.port=8501 --server.address=0.0.0.0
```

### Step 8: Access the App

Open your browser to: **http://localhost:8501**

You should see:
- ✅ RAG Engine Ready
- ✅ LLM Agent Ready
- ✅ File Watcher Active
- 📊 Indexed Files: (your document count)
- 📊 Total Chunks: (chunk count)

---

## 🎯 First Use Workflow

### 1. Wait for Initial Indexing

When you first start the app, it will automatically index all files in `./my_documents/`.

**Watch the status:**
- 📁 Indexed Files: 3
- 📊 Total Chunks: 45
- 👁️ File Watcher: Running

**This takes ~5-10 seconds per document.**

### 2. Enter a Job Description

**Option A: Scrape from URL**
1. Select "🔗 Scrape from URL"
2. Paste job posting URL (Greenhouse, Lever, LinkedIn, etc.)
3. Wait for scraping (~3 seconds)
4. Preview scraped content

**Option B: Manual Paste**
1. Select "📋 Paste Job Description"
2. Copy/paste full job description
3. Include: title, company, requirements, responsibilities

### 3. Generate Tailored Documents

1. Click "✨ Generate Tailored Resume & Cover Letter"
2. Watch the workflow:
   - 🔍 Searching your resume database... (shows retrieved chunks)
   - 🤖 Generating tailored documents... (15-30 seconds)
3. Review generated documents in tabs:
   - 📄 Resume tab
   - ✉️ Cover Letter tab
4. Download as .md files

### 4. Review & Edit

**Important:** The LLM uses ONLY facts from your actual work history. Review to ensure:
- ✅ All claims match your actual experience
- ✅ Numbers/metrics are accurate
- ✅ Skills listed are ones you actually have
- ✅ No hallucinated experiences

**Edit as needed** before submitting to employers.

---

## 🔒 Cloudflare Tunnel Setup (Optional)

To access the app securely from outside your local network:

### 1. Edit Cloudflare Tunnel Config

```bash
# Edit your cloudflared config
nano /Volumes/OMNI_01/50_Ops/06_CLOUDFLARED/cloudflared/config.yml
```

Add this ingress rule:

```yaml
ingress:
  - hostname: resume.yourdomain.com
    service: http://localhost:8501
  
  # ... your other routes ...
  
  - service: http_status:404
```

### 2. Restart Cloudflare Tunnel

```bash
supervisorctl -s unix:///tmp/pastyche_supervisor.sock restart cloudflared
```

### 3. Access Securely

Your app is now accessible at: **https://resume.yourdomain.com**

**Security guarantees:**
- ✅ All processing still happens locally
- ✅ Cloudflare Tunnel provides encryption in transit
- ✅ No data stored on Cloudflare servers
- ✅ No external API calls from the app

---

## 🛠️ Troubleshooting

### Issue: "Ollama not available"

**Solution:**
```bash
# Check if Ollama is running
ollama list

# If not running, start it
ollama serve

# If model not installed
ollama pull llama3.2
```

### Issue: "Playwright scraping failed"

**Solution:**
```bash
# Reinstall Playwright browsers
playwright install

# Test scraping
python job_scraper.py
```

### Issue: "Port 8501 already in use"

**Solution:**
```bash
# Find process using port 8501
lsof -i :8501

# Kill the process
kill -9 <PID>

# Or use different port
streamlit run main_ui.py --server.port=8502
```

### Issue: "No chunks retrieved from RAG"

**Solution:**
```bash
# Check if documents are indexed
ls -la ./my_documents/

# Check LanceDB data
ls -la ./lancedb_data/

# Re-index manually
python rag_engine.py
```

### Issue: "Generation takes too long"

**Solutions:**
1. Use smaller model: `ollama pull llama3.2:1b`
2. Reduce max_tokens in `.env`: `LLM_MAX_TOKENS="1024"`
3. Close other applications (free up RAM)

---

## 📊 Performance Optimization

### For Faster Generation:

```bash
# Use smaller, faster model
ollama pull llama3.2:1b

# Edit .env
LLM_MODEL="llama3.2:1b"
LLM_TEMPERATURE="0.5"  # Lower = faster, less creative
LLM_MAX_TOKENS="1024"  # Limit output length
```

### For Better Quality:

```bash
# Use larger model
ollama pull mistral

# Edit .env
LLM_MODEL="mistral"
LLM_TEMPERATURE="0.7"  # Balanced creativity/accuracy
LLM_MAX_TOKENS="2048"  # Allow longer output
```

### For More Accurate Matching:

```bash
# Increase RAG retrieval
# Edit rag_engine.py
k=15  # Instead of k=10 (retrieve more context)

# Use better embedding model
# Edit .env
EMBEDDING_MODEL="all-mpnet-base-v2"  # Better quality, slightly slower
```

---

## 📝 Best Practices

### Document Organization:

```
./my_documents/
├── resume_current.pdf      # Your current resume
├── cv_detailed.docx        # Full CV with all details
├── projects_2024.md        # Recent projects
├── projects_2023.md        # Older projects
├── performance_reviews/    # Performance review PDFs
│   ├── review_2024.pdf
│   └── review_2023.pdf
└── certifications/         # Certifications
    ├── aws_solutions_architect.pdf
    └── kubernetes_admin.pdf
```

### For Best Resume Matching:

1. **Quantify everything:**
   - ✅ "Built ETL pipelines processing 10TB+ daily"
   - ❌ "Built ETL pipelines"

2. **List specific tools:**
   - ✅ "Python, Apache Spark, AWS S3, Redshift"
   - ❌ "Various programming languages and cloud tools"

3. **Include project context:**
   - ✅ "Led team of 5 engineers to migrate legacy system to microservices"
   - ❌ "Worked on system migration"

4. **Update regularly:**
   - Add new projects monthly
   - Update metrics as they improve
   - Remove outdated technologies

### For Best Generation Results:

1. **Provide detailed job descriptions:**
   - Include full requirements section
   - Include "nice to have" qualifications
   - Include company description if available

2. **Review RAG chunks before generating:**
   - Click "View retrieved context"
   - Ensure relevant experience was found
   - Add more documents if key skills are missing

3. **Edit generated output:**
   - LLM provides first draft
   - You refine for authenticity
   - Add personal voice/tone

---

## 🎓 Advanced Usage

### Custom Embedding Model

```bash
# Edit .env
EMBEDDING_MODEL="BAAI/bge-small-en-v1.5"  # Faster, good quality
# or
EMBEDDING_MODEL="sentence-transformers/all-mpnet-base-v2"  # Best quality
```

### Multiple LLM Backends

```bash
# Ollama (recommended)
LLM_BACKEND="ollama"
LLM_MODEL="llama3.2"

# Or MLX-LM (native Apple Silicon)
LLM_BACKEND="mlx"
LLM_MODEL="mistral-7b-v0.1"
```

### Custom Chunking

```bash
# For very long documents
CHUNK_SIZE="1000"  # Larger chunks
CHUNK_OVERLAP="100"  # More overlap

# For very precise retrieval
CHUNK_SIZE="250"  # Smaller chunks
CHUNK_OVERLAP="25"  # Less overlap
```

---

## 📄 File Reference

| File | Purpose |
|------|---------|
| `main_ui.py` | Streamlit frontend UI |
| `rag_engine.py` | Document ingestion, embedding, vector search |
| `job_scraper.py` | Local Playwright web scraper |
| `llm_agent.py` | Ollama/MLX-LM integration |
| `file_watcher.py` | Watchdog for auto-reindex |
| `requirements.txt` | Python dependencies |
| `start.sh` | Startup script |
| `.env.example` | Environment configuration template |
| `README.md` | This documentation |

---

## 🔐 Privacy & Security

### What NEVER Leaves Your Network:

- ❌ Document content
- ❌ Embedding vectors
- ❌ Job descriptions
- ❌ Generated resumes
- ❌ Search queries
- ❌ Browsing history

### What Runs 100% Locally:

- ✅ MarkItDown (document conversion)
- ✅ sentence-transformers (embeddings)
- ✅ LanceDB (vector storage)
- ✅ Ollama/MLX-LM (LLM)
- ✅ Playwright (scraping)
- ✅ Watchdog (file monitoring)

### Data Storage:

- **Documents:** `./my_documents/` (your files)
- **Vectors:** `./lancedb_data/` (embeddings)
- **Metadata:** `./lancedb_data/index_metadata.json` (file hashes)
- **No cloud storage** - everything on your local disk

---

## 🙏 Support

**Issues:** File on GitHub (if applicable)  
**Documentation:** See `README.md`  
**Privacy Policy:** No data collected, ever  

---

**Built with ❤️ on M2 Mac - Your Data Stays Local**
