# Product Requirements Document — HYRED: Neural Resume Engine

| Field | Value |
|---|---|
| **Project Name** | HYRED — Neural Resume Engine |
| **Subdomain** | `hyred.bitandmortar.com` |
| **Version** | 1.0.0 |
| **Status** | Draft |
| **Date** | April 5, 2026 |
| **Author** | OMNI_01 Product Team |
| **Last Updated** | 2026-04-05 |

---

## 1. Overview

HYRED is a locally-hosted, AI-powered resume engineering platform that combines computer-vision-based resume parsing with large-language-model resume generation. The system ingests uploaded resumes (PDF or image), extracts structured professional data using an on-device vision model (Qwen2.5-VL-3B via M1 Vision), and then generates targeted resumes and cover letters aligned to user-supplied job descriptions — all running on a local M1 workstation with zero cloud dependency.

The application provides a kinetic, cyber-green branded interface built with React 18, Vite, TypeScript, and Tailwind CSS, backed by a FastAPI service on port 8020. Users can upload documents, analyze their professional profiles, generate tailored application materials via streaming responses, and export results as Markdown files.

---

## 2. Objectives

| ID | Objective | Priority |
|---|---|---|
| O1 | Enable resume text extraction from PDF/image in under 30 seconds | P0 |
| O2 | Generate targeted resumes and cover letters via streaming in under 60 seconds | P0 |
| O3 | Provide accurate ATS (Applicant Tracking System) compatibility scoring | P0 |
| O4 | Operate entirely on local hardware with zero cloud API dependencies | P0 |
| O5 | Support document repository management (upload, list, delete) | P1 |
| O6 | Deliver a polished, performant UI with kinetic animations and clear visual hierarchy | P1 |
| O7 | Allow tone customization via a casual-to-formal slider (0–100) | P2 |

---

## 3. Target Audience

| Segment | Description | Primary Use Case |
|---|---|---|
| **Job Seekers** | Active or passive candidates looking to optimize their application materials | Upload existing resume, target a job description, generate tailored resume + cover letter |
| **Career Coaches** | Professionals who advise clients on resume strategy | Analyze client resumes at scale, identify gaps, produce polished deliverables |
| **HR Professionals** | Internal talent acquisition and HR teams | Benchmark candidate resumes, generate role-specific application materials |
| **Recruiters** | Agency and corporate recruiters | Rapidly reformat candidate resumes for specific client roles |

---

## 4. Features

### 4.1 Resume Upload & Vision Extraction (P0)

- Upload PDF or image files via drag-and-drop or file picker.
- M1 Vision (Qwen2.5-VL-3B) processes the document to extract structured text.
- PDF parsing via `pdftoppm` with `pymupdf` fallback.
- File size limits enforced server-side.
- Extracted text stored in `my_documents/` repository.

### 4.2 Document Repository (P0)

- List all uploaded documents with metadata (name, upload date, file type, size).
- Upload new documents to the repository.
- Delete documents from the repository.
- Repository backed by local `my_documents/` directory.

### 4.3 Resume Analysis (P0)

- Analyze uploaded resumes and return structured JSON with the following fields:

  | Field | Type | Description |
  |---|---|---|
  | `name` | string | Extracted candidate name |
  | `title` | string | Current or most recent job title |
  | `top_skills` | string[] | Top 5–10 skills identified |
  | `experience_years` | number | Estimated years of professional experience |
  | `achievements` | string[] | Key accomplishments and metrics |
  | `gaps` | string[] | Identified gaps or areas for improvement |
  | `strengths` | string[] | Notable strengths in the resume |
  | `ats_score` | number (0–100) | ATS compatibility score |

### 4.4 Job Description Input (P0)

- Free-text input for users to paste or upload a target job description.
- Used as context for targeted resume and cover letter generation.

### 4.5 Profile Management (P1)

- User profile fields:
  - **Name**: Display name for generated documents.
  - **Target Role**: Desired job title or role.
  - **Tone Slider**: 0–100 scale from casual to formal writing style.
- Profile persisted locally between sessions.

### 4.6 Streaming Resume Generation (P0)

- Resume generated via streaming JSONL response from FastAPI.
- Live token-by-token display in the UI as tokens arrive.
- Generation powered by Ollama (`llama3.2:3b` by default).
- Model selector allows switching between available Ollama models.

### 4.7 Cover Letter Generation (P0)

- Cover letter generated aligned with the user's resume and the target job description.
- Respects the user's tone slider setting.
- Streaming response with live token display.

### 4.8 Export (P1)

- Export generated resume and cover letter as downloadable Markdown (`.md`) files.
- Files named with candidate name and date for easy identification.

### 4.9 HUD Interface (P1)

- Real-time dashboard displaying:
  - LLM model status and availability.
  - Document count in repository.
  - RAG indexing status.
  - System health indicators.

### 4.10 Three-View State Machine (P0)

| View | Trigger | Content |
|---|---|---|
| **Landing (Input)** | Initial load | Upload resume, paste job description, configure profile |
| **Generating (Streaming)** | Generation started | Live token stream with progress indicator |
| **Results** | Generation complete | Rendered resume + cover letter with export options |

---

## 5. User Stories

| ID | As a… | I want to… | So that… |
|---|---|---|---|
| US-1 | Job seeker | Upload my existing resume PDF | The system can extract and understand my professional background |
| US-2 | Job seeker | Paste a job description | The generated resume is targeted to that specific role |
| US-3 | Job seeker | See my resume analyzed as structured JSON | I understand my strengths, gaps, and ATS score |
| US-4 | Job seeker | Generate a tailored resume via streaming | I can watch the content build in real-time and verify quality |
| US-5 | Job seeker | Generate a matching cover letter | My application materials are cohesive and aligned |
| US-6 | Job seeker | Export my resume as a Markdown file | I can use it in other applications or share it |
| US-7 | Career coach | Manage a repository of client resumes | I can organize and access documents efficiently |
| US-8 | Recruiter | Select different LLM models | I can balance speed vs. quality for different use cases |
| US-9 | User | Adjust the tone slider | The output matches the formality level of the target company |
| US-10 | User | View the HUD | I know the system status and whether models are available |
| US-11 | User | Delete old documents | I keep my repository clean and relevant |

---

## 6. Functional Requirements

### 6.1 API Endpoints

| Endpoint | Method | Description | Request | Response |
|---|---|---|---|---|
| `/status` | GET | System health and model status | — | JSON with LLM status, document count, RAG status |
| `/documents` | GET | List all documents in repository | — | JSON array of document metadata |
| `/documents/upload` | POST | Upload a new document | `multipart/form-data` with file | JSON with document metadata |
| `/documents/{name}/analyze` | POST | Analyze a specific document | Path param `name` | JSON with analysis fields (see 4.3) |
| `/generate` | POST (SSE/JSONL) | Generate targeted resume + cover letter | JSON with job description, profile, model | Streaming JSONL tokens |
| `/export` | POST | Export generated content as Markdown | JSON with resume and cover letter content | Downloadable `.md` file |

### 6.2 Frontend Requirements

- **FR-1**: React 18 application with Vite build system and TypeScript.
- **FR-2**: Tailwind CSS for styling with cyber-green accent (`#00ffca`).
- **FR-3**: Framer Motion for kinetic animations and transitions between views.
- **FR-4**: Space Grotesk font family for all text.
- **FR-5**: Three-view state machine: landing, generating, results.
- **FR-6**: Live streaming token display during generation.
- **FR-7**: File drag-and-drop upload zone.
- **FR-8**: Model selector dropdown populated from `/status` endpoint.
- **FR-9**: Tone slider (0–100) with visual indicator.
- **FR-10**: HUD component with system status badges.
- **FR-11**: Downloadable Markdown export button on results view.
- **FR-12**: Error toast notifications for failed operations.

### 6.3 Backend Requirements

- **BR-1**: FastAPI application serving on port 8020.
- **BR-2**: M1 Vision integration with Qwen2.5-VL-3B for PDF/image parsing.
- **BR-3**: Ollama integration with `llama3.2:3b` (default) for text generation.
- **BR-4**: PDF parsing via `pdftoppm` with `pymupdf` fallback.
- **BR-5**: Streaming JSONL response for `/generate` endpoint.
- **BR-6**: Local file storage in `my_documents/` directory.
- **BR-7**: Filename sanitization on upload.
- **BR-8**: File size limits enforced via FastAPI middleware.
- **BR-9**: CORS configured to allow all origins.
- **BR-10**: Graceful error handling for PDF parsing failures.

---

## 7. Non-Functional Requirements

| ID | Requirement | Target |
|---|---|---|
| NFR-1 | Resume extraction latency | < 30 seconds for PDF/image |
| NFR-2 | Resume generation latency | < 60 seconds end-to-end (streaming) |
| NFR-3 | ATS score accuracy | Correlation >= 0.8 with industry ATS tools |
| NFR-4 | Cloud dependency | Zero — all processing local to M1 workstation |
| NFR-5 | File size limit | Configurable, default 25 MB per file |
| NFR-6 | Concurrent users | Single-user (local workstation) |
| NFR-7 | UI responsiveness | 60 FPS animations, < 100ms interaction feedback |
| NFR-8 | Availability | 99% during local system uptime |
| NFR-9 | Data persistence | Documents persist across restarts in `my_documents/` |
| NFR-10 | Model flexibility | Support any Ollama-hosted model via selector |

---

## 8. Technical Architecture

### 8.1 System Diagram

```mermaid
graph TB
    subgraph Frontend["Frontend — hyred.bitandmortar.com"]
        UI[React 18 App]
        Vite[Vite Dev Server]
        TS[TypeScript]
        Tailwind[Tailwind CSS]
        Motion[Framer Motion]
        Font[Space Grotesk]

        UI --> Vite
        UI --> TS
        UI --> Tailwind
        UI --> Motion
        UI --> Font
    end

    subgraph Backend["Backend — FastAPI :8020"]
        API[FastAPI Server]
        CORS[CORS Middleware]
        Sanitizer[Filename Sanitizer]
        SizeLimit[File Size Limiter]
        Status[/status]
        Documents[/documents/*]
        Analyze[/documents/{name}/analyze]
        Generate[/generate]
        Export[/export]

        API --> CORS
        API --> Sanitizer
        API --> SizeLimit
        API --> Status
        API --> Documents
        API --> Analyze
        API --> Generate
        API --> Export
    end

    subgraph Vision["M1 Vision Engine"]
        QwenVL[Qwen2.5-VL-3B]
        PDFParser[PDF Parser]
        pdftoppm[pdftoppm]
        pymupdf[PyMuPDF Fallback]

        PDFParser --> pdftoppm
        pdftoppm -.fail.-> pymupdf
        PDFParser --> QwenVL
    end

    subtext Text["LLM Text Engine"]
        Ollama[Ollama]
        Llama[llama3.2:3b]
        Models[Other Ollama Models]

        Ollama --> Llama
        Ollama --> Models
    end

    subgraph Storage["Local Storage"]
        MyDocs[my_documents/]
        Profile[user_profile.json]

    end

    UI -->|HTTP| API
    API -->|Parse PDF/Image| PDFParser
    API -->|Generate Text| Ollama
    API -->|Store| MyDocs
    API -->|Store| Profile

    classDef frontend fill:#1a1a2e,stroke:#00ffca,color:#e0e0e0
    classDef backend fill:#16213e,stroke:#00ffca,color:#e0e0e0
    classDef vision fill:#0f3460,stroke:#00ffca,color:#e0e0e0
    classDef text fill:#533483,stroke:#00ffca,color:#e0e0e0
    classDef storage fill:#1a1a2e,stroke:#555,color:#e0e0e0

    class Frontend,Vite,UI,TS,Tailwind,Motion,Font frontend
    class Backend,API,CORS,Sanitizer,SizeLimit,Status,Documents,Analyze,Generate,Export backend
    class Vision,QwenVL,PDFParser,pdftoppm,pymupdf vision
    subgraph Text["LLM Text Engine"]
    end
    class Text,Ollama,Llama,Models text
    class Storage,MyDocs,Profile storage
```

### 8.2 Component Breakdown

| Component | Technology | Responsibility |
|---|---|---|
| Frontend SPA | React 18 + Vite + TypeScript | UI rendering, state management, streaming consumption |
| Styling | Tailwind CSS + Space Grotesk + `#00ffca` | Visual design system |
| Animation | Framer Motion | View transitions, kinetic effects |
| API Server | FastAPI (Python) | HTTP routing, request validation, orchestration |
| Vision Parser | Qwen2.5-VL-3B (MLX) | PDF/image to text extraction |
| PDF Engine | pdftoppm / PyMuPDF | PDF page rendering to images for vision model |
| Text LLM | Ollama (llama3.2:3b default) | Resume and cover letter generation |
| Storage | Local filesystem (`my_documents/`) | Document persistence |
| Streaming | JSONL over HTTP SSE | Real-time token delivery to frontend |

### 8.3 Data Flow

```
User uploads PDF/Image
  -> Frontend sends to POST /documents/upload
    -> Backend sanitizes filename, validates size
      -> pdftoppm converts PDF pages to images (or PyMuPDF fallback)
        -> Qwen2.5-VL-3B extracts text and structure
          -> Document saved to my_documents/
            -> Metadata returned to frontend

User requests analysis
  -> Frontend sends to POST /documents/{name}/analyze
    -> Backend loads document text
      -> LLM analyzes and returns structured JSON
        -> Frontend renders analysis fields

User pastes job description and clicks Generate
  -> Frontend sends to POST /generate
    -> Backend streams JSONL tokens from Ollama
      -> Frontend displays tokens in real-time
        -> Resume + cover letter assembled on completion

User clicks Export
  -> Frontend sends to POST /export
    -> Backend returns Markdown file for download
```

---

## 9. Security

| ID | Control | Implementation |
|---|---|---|
| SEC-1 | CORS | Allow all origins (`*`) for local development; restrict in production |
| SEC-2 | Filename Sanitization | Strip special characters, path traversal sequences, and null bytes from uploaded filenames |
| SEC-3 | File Size Limits | FastAPI middleware enforces configurable max upload size (default 25 MB) |
| SEC-4 | Input Validation | Pydantic models validate all request bodies |
| SEC-5 | Error Handling | Graceful degradation on PDF parsing failure; no stack traces exposed to client |
| SEC-6 | Local-Only | No data leaves the local machine; no cloud API calls |
| SEC-7 | Path Traversal Prevention | Document names validated against `my_documents/` base path |
| SEC-8 | Model Access Control | Only whitelisted Ollama models accessible via selector |

---

## 10. Success Metrics

| Metric | Target | Measurement Method |
|---|---|---|
| Resume extraction time (PDF) | < 30 seconds | Backend instrumentation on `/documents/upload` |
| Resume generation time (streaming) | < 60 seconds | Time from generation start to final token |
| ATS score accuracy | >= 0.8 correlation with industry tools | Manual comparison against known ATS scorers |
| Cloud dependency | Zero | Architecture audit — no external API calls |
| UI interaction latency | < 100ms | Frontend performance profiling |
| Document repository operations | 100% success rate | Integration test coverage |
| Streaming reliability | No dropped tokens during generation | Frontend token count vs. backend token count |

---

## 11. Risks and Mitigations

| ID | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R-1 | Vision model fails to parse complex PDF layouts | Medium | High | PyMuPDF fallback; user can manually paste text |
| R-2 | Ollama model not available or not running | Medium | High | `/status` endpoint checks availability; HUD shows model status; clear error messaging |
| R-3 | Generated resume contains hallucinated information | Medium | High | Analysis step grounds generation in extracted facts; user reviews before export |
| R-4 | Large PDF files cause memory pressure | Low | Medium | File size limits; page-by-page processing |
| R-5 | Streaming connection drops mid-generation | Low | Medium | Frontend retry logic; partial content preserved |
| R-6 | ATS score lacks accuracy without ground truth | Medium | Medium | Benchmark against open-source ATS tools; document confidence intervals |
| R-7 | M1 thermal throttling under sustained load | Medium | Low | Model quantization; request queuing; user notification during extended operations |

---

## 12. Future Enhancements

| ID | Enhancement | Description | Priority |
|---|---|---|---|
| FE-1 | RAG-Powered Knowledge Base | Index industry-specific terminology and job market data to enrich generated resumes | P1 |
| FE-2 | Multi-Resume Comparison | Analyze and compare multiple uploaded resumes to identify progression and gaps | P2 |
| FE-3 | LinkedIn Profile Import | Parse LinkedIn profile URLs or exports as an alternative data source | P2 |
| FE-4 | ATS Simulator | Simulate how the generated resume would perform in real ATS platforms (Greenhouse, Lever, Workday) | P1 |
| FE-5 | Batch Generation | Generate multiple resume variants for A/B testing across different job types | P2 |
| FE-6 | Cover Letter Templates | Provide user-selectable cover letter templates and structures | P2 |
| FE-7 | Team Workspaces | Multi-user document management for career coaching agencies | P3 |
| FE-8 | Interview Prep Generator | Generate tailored interview talking points from the resume and job description | P3 |
| FE-9 | Portfolio Integration | Link GitHub, Dribbble, or personal website URLs for enriched professional profiles | P3 |
| FE-10 | Model Fine-Tuning | Fine-tune llama3.2:3b on high-performing resumes for domain-specific generation | P2 |
| FE-11 | Export to PDF/DOCX | Additional export formats beyond Markdown | P1 |
| FE-12 | Resume Versioning | Track and compare different versions of generated resumes over time | P2 |

---

## 13. Appendix

### 13.1 Technology Stack Summary

| Layer | Technology |
|---|---|
| Frontend Framework | React 18 + TypeScript |
| Build Tool | Vite |
| CSS Framework | Tailwind CSS |
| Animation Library | Framer Motion |
| Typography | Space Grotesk |
| Accent Color | `#00ffca` (cyber-green) |
| Backend Framework | FastAPI (Python) |
| Vision Model | Qwen2.5-VL-3B (MLX on M1) |
| Text LLM | Ollama (llama3.2:3b default) |
| PDF Parser | pdftoppm + PyMuPDF fallback |
| Streaming Protocol | JSONL over HTTP SSE |
| Document Storage | Local filesystem (`my_documents/`) |
| Server Port | 8020 |
| Subdomain | `hyred.bitandmortar.com` |

### 13.2 Glossary

| Term | Definition |
|---|---|
| ATS | Applicant Tracking System — software used by employers to filter and rank resumes |
| JSONL | JSON Lines — a format where each line is a valid JSON object, used for streaming |
| RAG | Retrieval-Augmented Generation — technique combining LLM generation with external knowledge retrieval |
| Vision Model | A multimodal AI that can process images and PDFs as visual input |
| Streaming | Delivering response tokens incrementally as they are generated, rather than waiting for completion |
| HUD | Heads-Up Display — the system status panel showing model, document, and indexing information |
| Tone Slider | A 0–100 control that adjusts the formality of generated text from casual (0) to formal (100) |

### 13.3 Document History

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0.0 | 2026-04-05 | OMNI_01 Product Team | Initial PRD creation |

---

*End of Document*
