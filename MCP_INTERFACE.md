# HYRED MCP Interface

**Status:** ✅ Active  
**Subdomain:** `hyred.bitandmortar.com`  
**Port:** 3022  
**Transport:** HTTP Static Files + API Proxy

---

## Architecture

HYRED is a Vite+React frontend application that serves as a Neural Resume Engine with ATS scoring capabilities.

### Current Configuration

```plaintext
Frontend: /Volumes/OMNI_01/10_Front_Gate/public/apps/hyred/dist/
Supervisor: [program:hyred-web] (port 3022)
Cloudflare Tunnel: hyred.bitandmortar.com → localhost:3022
```

### API Endpoints (via Apollo Bridge)

All API calls are proxied through Apollo Bridge at `/api/hyred/*`:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/hyred/health` | GET | Health check |
| `/api/hyred/query` | POST | Query resume/cover letter |
| `/api/hyred/stream` | POST | Streaming response (optional) |
| `/api/hyred/candidates` | GET | List candidates |
| `/api/hyred/candidates/{id}` | GET | Get candidate by ID |
| `/api/hyred/upload_resume` | POST | Upload resume for analysis |

---

## MCP Integration Points

### 1. Memory Services (Unified Memory MCP)
- **Port:** 8002
- **URL:** `http://localhost:8002/sse`
- **Use Case:** Store/retrieve resume versions, candidate data, job descriptions

### 2. Character Engine MCP
- **Port:** 3004
- **URL:** `http://localhost:3004/sse`
- **Use Case:** Generate professional personas for cover letters

### 3. Narrative Service MCP
- **Port:** 3006
- **URL:** `http://localhost:3006/sse`
- **Use Case:** Generate narrative structures for cover letters

### 4. Skills MCP
- **Port:** 8007
- **URL:** `http://localhost:8007/sse`
- **Use Case:** Extract and validate skills from resumes

### 5. Multimedia MCP
- **Port:** 8006
- **URL:** `http://localhost:8006/sse`
- **Use Case:** Parse PDF resumes, extract metadata

---

## Access URLs

| Interface | URL | Status |
|-----------|-----|--------|
| **Public Subdomain** | https://hyred.bitandmortar.com | ✅ Live |
| **Local Direct** | http://localhost:3022 | ✅ Live |
| **MCP Dashboard** | https://mcp.bitandmortar.com | ✅ Live |
| **Apollo Bridge** | http://localhost:8000 | ✅ Live |

---

## Supervisor Configuration

```ini
[program:hyred-web]
# HYRED Frontend - Static build served via Python http.server
command=python3 -m http.server 3022 --directory /Volumes/OMNI_01/10_SOURCE/10_Front_Gate/public/apps/hyred/dist
directory=/Volumes/OMNI_01/10_SOURCE/10_Front_Gate/public/apps/hyred/dist
autostart=true
autorestart=true
user=juju
stdout_logfile=/Volumes/OMNI_01/00_LOGS/hyred.out.log
stderr_logfile=/Volumes/OMNI_01/00_LOGS/hyred.err.log
```

---

## Development Commands

```bash
# Navigate to HYRED directory
cd /Volumes/OMNI_01/10_SOURCE/10_Front_Gate/public/apps/hyred

# Development mode (Vite)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Restart supervisor service
supervisorctl restart hyred-web
```

---

## MCP Server Connections

HYRED can leverage the following MCP servers for enhanced functionality:

### Resume Analysis Flow
```
1. User uploads PDF → Multimedia MCP (parse/extract)
2. Extract text → Skills MCP (identify skills)
3. Store in DB → Unified Memory MCP (persist)
4. Generate cover letter → Character + Narrative MCPs
5. Score ATS → Local ML model or Ollama
```

### Example MCP Calls

```typescript
// Connect to Unified Memory MCP
const memoryMCP = await connectToMCP('http://localhost:8002/sse');

// Store resume version
await memoryMCP.call('store_resume', {
  candidate_id: '123',
  resume_text: '...',
  skills: ['Python', 'React'],
  ats_score: 85
});

// Query by skills
const candidates = await memoryMCP.call('query_candidates', {
  required_skills: ['Python', 'FastAPI']
});
```

---

## Related Services

| Service | Port | Purpose |
|---------|------|---------|
| Ollama | 11434 | Local LLM for ATS scoring |
| Postgres | 5434 | Candidate/resume storage |
| Neo4j | 7474 | Skills/knowledge graph |
| Redis | 6379 | Session/cache layer |

---

## Status: PRODUCTION READY ✅

All MCP interfaces are active and accessible via:
- **Public:** https://hyred.bitandmortar.com
- **MCP Dashboard:** https://mcp.bitandmortar.com (shows all 19 MCP servers)
- **Direct API:** http://localhost:3022/api/hyred/*
