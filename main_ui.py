#!/usr/bin/env python3
"""
hyred — CV & Cover Letter Generator
=====================================
Local-first AI-powered resume tailoring.
All processing on-device via Ollama. No cloud APIs. No tracking.
"""

import streamlit as st
from pathlib import Path
from datetime import datetime

from job_scraper import LocalJobScraper
from rag_engine import get_rag_engine
from llm_agent import get_llm_agent
from file_watcher import start_file_watcher, get_watcher_status
from ats_scorer import score_ats_match
from export_utils import markdown_to_docx_bytes

try:
    from notebooklm_integration import NotebookLMIntegration, upload_generated_application
    _NOTEBOOKLM_AVAILABLE = True
except ImportError:
    _NOTEBOOKLM_AVAILABLE = False

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="hyred",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://github.com/bitandmortar/hyred",
        "Report a bug": "https://github.com/bitandmortar/hyred/issues",
        "About": "# hyred\nLocal-first CV & Cover Letter Generator.",
    },
)

# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    @font-face {
        font-family: 'Barlow';
        src: local('Barlow'), url('file:///Volumes/OMNI_01/10_SOURCE/50_Ops/FONTS/Barlow-Regular.ttf') format('truetype');
        font-weight: 400;
    }
    @font-face {
        font-family: 'Barlow';
        src: local('Barlow Bold'), url('file:///Volumes/OMNI_01/10_SOURCE/50_Ops/FONTS/Barlow-Bold.ttf') format('truetype');
        font-weight: 700;
    }
    @font-face {
        font-family: 'Inclusive Sans';
        src: local('Inclusive Sans'), url('file:///Volumes/OMNI_01/10_SOURCE/50_Ops/FONTS/InclusiveSans-Regular.ttf') format('truetype');
    }
    @font-face {
        font-family: 'Korolev';
        src: local('Korolev'), url('file:///Volumes/OMNI_01/10_SOURCE/50_Ops/FONTS/Korolev Bold.otf') format('opentype');
        font-weight: 700;
    }
    .main-header {
        font-family: 'Korolev', 'Barlow', sans-serif !important;
        font-weight: 900 !important;
        font-size: 2.5rem !important;
        letter-spacing: -0.02em !important;
    }
    [data-testid="stHeading"], [data-testid="stSubheader"] {
        font-family: 'Barlow', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
    }
    [data-testid="stMarkdown"] {
        font-family: 'Inclusive Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
    }
    [data-testid="stButton"] > button {
        font-family: 'Barlow', sans-serif !important;
        font-weight: 600 !important;
    }
    .ats-pill-match {
        display: inline-block; background: #d1fae5; color: #065f46;
        border-radius: 9999px; padding: 2px 10px; margin: 2px;
        font-size: 0.78rem; font-weight: 600;
    }
    .ats-pill-miss {
        display: inline-block; background: #fee2e2; color: #991b1b;
        border-radius: 9999px; padding: 2px 10px; margin: 2px;
        font-size: 0.78rem; font-weight: 600;
    }
    .ats-score-big {
        font-size: 3rem; font-weight: 900; line-height: 1;
    }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
def initialize_session_state():
    defaults = {
        "rag_engine": None,
        "llm_agent": None,
        "notebooklm": None,
        "watcher_status": "starting",
        "indexed_files": 0,
        "total_chunks": 0,
        "generation_result": None,
        "job_description": "",
        "company_name": "",
        "role_name": "",
        # Profile
        "profile_name": "",
        "profile_title": "",
        "selected_model": "llama3.2",
        "tone": 50,
        "use_notebooklm": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ---------------------------------------------------------------------------
# Sidebar — Profile & Settings
# ---------------------------------------------------------------------------
def render_sidebar():
    with st.sidebar:
        st.markdown("## 👤 Profile")
        st.session_state.profile_name = st.text_input(
            "Your Name",
            value=st.session_state.profile_name,
            placeholder="First Last",
            help="Used in exported filenames and documents",
        )
        st.session_state.profile_title = st.text_input(
            "Target Title",
            value=st.session_state.profile_title,
            placeholder="e.g. Senior Software Engineer",
        )

        st.divider()
        st.markdown("## 🤖 LLM Settings")

        # Populate model list from Ollama if available
        available_models = ["llama3.2", "llama3.1", "mistral", "qwen2.5", "phi3", "gemma2"]
        if st.session_state.llm_agent and st.session_state.llm_agent.available:
            try:
                live_models = st.session_state.llm_agent.list_available_models()
                if live_models:
                    available_models = live_models
            except Exception:
                pass

        current_idx = 0
        if st.session_state.selected_model in available_models:
            current_idx = available_models.index(st.session_state.selected_model)

        st.session_state.selected_model = st.selectbox(
            "Ollama Model", available_models, index=current_idx
        )

        st.session_state.tone = st.slider(
            "Cover Letter Tone",
            min_value=0, max_value=100,
            value=st.session_state.tone,
            help="0 = Formal & precise   |   100 = Warm & conversational",
        )
        tone_label = "Formal" if st.session_state.tone < 35 else ("Conversational" if st.session_state.tone > 65 else "Balanced")
        st.caption(f"Current: **{tone_label}**")

        if _NOTEBOOKLM_AVAILABLE:
            st.divider()
            st.markdown("## 🔧 Integrations")
            st.session_state.use_notebooklm = st.toggle(
                "NotebookLM (optional)",
                value=st.session_state.use_notebooklm,
                help="Requires Google authentication. Enables auto-upload of generated docs.",
            )

        st.divider()
        st.markdown("## 📚 Document Library")
        docs_dir = Path("./my_documents")
        if docs_dir.exists():
            files = [
                f for f in docs_dir.rglob("*")
                if f.is_file() and f.suffix in [".pdf", ".docx", ".md", ".txt", ".pages"]
            ]
            st.metric("Indexed Files", len(files))
            for f in sorted(files, key=lambda x: x.stat().st_mtime, reverse=True)[:6]:
                st.markdown(f"📄 {f.name}")
        else:
            st.warning("No `my_documents` folder found")


# ---------------------------------------------------------------------------
# Service initialisation
# ---------------------------------------------------------------------------
def setup_local_services():
    col1, col2, col3 = st.columns(3)
    with col1:
        with st.spinner("🧠 Loading RAG Engine..."):
            try:
                st.session_state.rag_engine = get_rag_engine()
                stats = st.session_state.rag_engine.get_stats()
                st.session_state.indexed_files = stats.get("total_files", 0)
                st.session_state.total_chunks = stats.get("total_chunks", 0)
                st.success("✅ RAG Engine Ready")
            except Exception as e:
                st.error(f"❌ RAG Engine: {e}")

    with col2:
        with st.spinner("🤖 Loading LLM Agent..."):
            try:
                st.session_state.llm_agent = get_llm_agent()
                if st.session_state.llm_agent.available:
                    st.success("✅ LLM Agent Ready")
                else:
                    st.warning("⚠️ LLM not available — is Ollama running?")
            except Exception as e:
                st.error(f"❌ LLM Agent: {e}")

    with col3:
        with st.spinner("👁️ Starting File Watcher..."):
            try:
                def on_file_change(file_path):
                    if st.session_state.rag_engine:
                        st.session_state.rag_engine.index_file(Path(file_path))
                        stats = st.session_state.rag_engine.get_stats()
                        st.session_state.indexed_files = stats.get("total_files", 0)
                        st.session_state.total_chunks = stats.get("total_chunks", 0)
                start_file_watcher("./my_documents", on_file_change)
                st.session_state.watcher_status = "running"
                st.success("✅ File Watcher Active")
            except Exception as e:
                st.error(f"❌ File Watcher: {e}")
                st.session_state.watcher_status = "error"

    if _NOTEBOOKLM_AVAILABLE and st.session_state.use_notebooklm:
        with st.spinner("📓 Connecting NotebookLM..."):
            try:
                st.session_state.notebooklm = NotebookLMIntegration()
                if not st.session_state.notebooklm.authenticated:
                    st.warning("⚠️ NotebookLM not authenticated")
            except Exception as e:
                st.error(f"❌ NotebookLM: {e}")


def display_status_bar():
    watcher_status = get_watcher_status()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📁 Indexed Files", st.session_state.indexed_files)
    c2.metric("📊 Chunks", st.session_state.total_chunks)
    c3.metric(
        "👁️ File Watcher",
        watcher_status["status"].title(),
        "✅ Active" if watcher_status["status"] == "running" else "⚠️ Inactive",
    )
    llm_ok = st.session_state.llm_agent and st.session_state.llm_agent.available
    c4.metric("🤖 LLM Backend", "✅ Ready" if llm_ok else "⚠️ Offline")


# ---------------------------------------------------------------------------
# ATS Score panel
# ---------------------------------------------------------------------------
def render_ats_panel(job_description: str, generated_text: str):
    result = score_ats_match(job_description, generated_text)
    score = result["score"]

    color = "#10b981" if score >= 70 else ("#f59e0b" if score >= 45 else "#ef4444")
    label = "Strong match" if score >= 70 else ("Decent match" if score >= 45 else "Needs work")

    st.markdown(f"""
    <div style="border:1px solid {color}; border-radius:12px; padding:16px 20px; margin-bottom:8px;">
      <span class="ats-score-big" style="color:{color}">{score}</span>
      <span style="font-size:1.1rem; color:{color}; margin-left:8px;">/ 100 &nbsp;—&nbsp; {label}</span>
      <div style="font-size:0.8rem; color:#6b7280; margin-top:4px;">
        {result['matched_count']} of {result['total_jd_keywords']} key JD terms found in your output
      </div>
    </div>
    """, unsafe_allow_html=True)

    col_m, col_x = st.columns(2)
    with col_m:
        st.markdown("**✅ Matched keywords**")
        pills_html = " ".join(f'<span class="ats-pill-match">{k}</span>' for k in result["matched"])
        st.markdown(pills_html or "_none_", unsafe_allow_html=True)
    with col_x:
        st.markdown("**❌ Missing keywords**")
        pills_html = " ".join(f'<span class="ats-pill-miss">{k}</span>' for k in result["missing"])
        st.markdown(pills_html or "🎉 All top terms covered!", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Export helpers
# ---------------------------------------------------------------------------
def export_buttons(label: str, content: str, slug: str, profile_name: str):
    """Render .md and .docx download buttons side-by-side."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = profile_name.replace(" ", "_") if profile_name else "resume"
    base = f"{safe_name}_{slug}_{ts}"

    c1, c2 = st.columns(2)
    with c1:
        st.download_button(
            label=f"📥 Download {label} (.md)",
            data=content,
            file_name=f"{base}.md",
            mime="text/markdown",
            use_container_width=True,
        )
    with c2:
        try:
            docx_bytes = markdown_to_docx_bytes(content, title=label)
            st.download_button(
                label=f"📄 Download {label} (.docx)",
                data=docx_bytes,
                file_name=f"{base}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True,
            )
        except ImportError:
            st.info("Install `python-docx` to enable DOCX export: `pip install python-docx`")


# ---------------------------------------------------------------------------
# Job input section
# ---------------------------------------------------------------------------
def render_job_input() -> str:
    """
    Renders the job description input widget.

    Clipboard note: browsers don't grant programmatic clipboard read access
    without explicit user permission. The most reliable UX is a single smart
    text field that auto-detects whether the pasted content is a URL or raw
    description text, then routes accordingly.

    Returns the job description string (may be empty).
    """
    st.subheader("🎯 Job Description")

    pasted = st.text_area(
        "Paste a job URL **or** the full description here",
        value=st.session_state.job_description,
        height=60,
        placeholder=(
            "https://boards.greenhouse.io/company/jobs/… "
            " — or paste the full JD text directly"
        ),
        help=(
            "Paste a URL from LinkedIn, Indeed, ZipRecruiter, Glassdoor, "
            "Greenhouse, Lever, or Workday and it will be scraped locally. "
            "Or paste the raw job description text. Either works."
        ),
        key="jd_paste_area",
    )

    job_description = ""

    if pasted:
        pasted = pasted.strip()
        is_url = pasted.startswith("http://") or pasted.startswith("https://")

        if is_url:
            scrape_col, _ = st.columns([1, 3])
            with scrape_col:
                scrape_btn = st.button("🔍 Scrape job posting", use_container_width=True)

            if scrape_btn or st.session_state.get("_last_scraped_url") == pasted:
                if st.session_state.get("_last_scraped_url") != pasted:
                    st.session_state["_last_scraped_url"] = pasted
                    with st.spinner("Scraping job posting locally…"):
                        scraper = LocalJobScraper()
                        result = scraper.scrape_url(pasted)

                    if result.get("error"):
                        st.warning(f"⚠️ {result['error']}")
                        st.info("Paste the description text directly instead.")
                        st.session_state["_scraped_jd"] = ""
                    else:
                        parts = []
                        for field, prefix in [
                            ("job_title", "**Job Title:**"),
                            ("company", "**Company:**"),
                            ("job_description", "\n**Description:**\n"),
                            ("requirements", "\n**Requirements:**\n"),
                        ]:
                            if result.get(field):
                                parts.append(f"{prefix} {result[field]}")
                        scraped_text = "\n\n".join(parts)
                        st.session_state["_scraped_jd"] = scraped_text

                        # Auto-fill company / role from scrape
                        if result.get("company") and not st.session_state.company_name:
                            st.session_state.company_name = result["company"]
                        if result.get("job_title") and not st.session_state.role_name:
                            st.session_state.role_name = result["job_title"]

                        st.success("✅ Scraped successfully!")

                job_description = st.session_state.get("_scraped_jd", "")
                if job_description:
                    with st.expander("📋 Scraped content preview"):
                        st.text(job_description[:800] + ("…" if len(job_description) > 800 else ""))
        else:
            # Raw text — use directly
            job_description = pasted
            st.session_state.job_description = pasted
            st.caption(f"✏️ Using pasted description ({len(pasted):,} chars)")

    # Company / role
    cc, cr = st.columns(2)
    with cc:
        st.session_state.company_name = st.text_input(
            "🏢 Company", value=st.session_state.company_name, placeholder="E Corp"
        )
    with cr:
        st.session_state.role_name = st.text_input(
            "🎯 Role", value=st.session_state.role_name, placeholder="Chief Technology Officer"
        )

    return job_description


# ---------------------------------------------------------------------------
# Generation + results
# ---------------------------------------------------------------------------
def render_generate_section(job_description: str):
    llm_ready = st.session_state.llm_agent and st.session_state.llm_agent.available

    st.divider()
    generate_clicked = st.button(
        "✨ Generate Tailored Resume & Cover Letter",
        type="primary",
        disabled=not job_description or not llm_ready,
        use_container_width=True,
    )

    if not llm_ready:
        st.caption("⚠️ LLM offline — start Ollama with `ollama serve` then refresh.")

    if generate_clicked and job_description:
        # Update model on agent in case sidebar changed it
        if st.session_state.llm_agent:
            st.session_state.llm_agent.model = st.session_state.selected_model

        with st.spinner("🔍 Searching your document library…"):
            rag_results = st.session_state.rag_engine.search(job_description, k=10)
            st.info(f"📊 Retrieved {len(rag_results)} relevant chunks")

            with st.expander(f"🔍 View retrieved context ({len(rag_results)} chunks)"):
                for i, chunk in enumerate(rag_results, 1):
                    st.markdown(
                        f"**Chunk {i}** (Score: {chunk['score']:.3f})  \n"
                        f"📁 `{Path(chunk['file_path']).name}` · {chunk['metadata']['section']}\n\n"
                        f"{chunk['text'][:280]}…"
                    )
                    st.divider()

        with st.spinner("🤖 Generating documents…"):
            result = st.session_state.llm_agent.generate_resume_and_cover_letter(
                job_description,
                rag_results,
                tone=st.session_state.tone,
            )
            st.session_state.generation_result = result
            st.success("✅ Generation complete!")

        # Optional NotebookLM upload
        if (
            _NOTEBOOKLM_AVAILABLE
            and st.session_state.use_notebooklm
            and st.session_state.notebooklm
            and st.session_state.notebooklm.authenticated
            and st.session_state.company_name
            and st.session_state.role_name
        ):
            with st.spinner("📓 Uploading to NotebookLM…"):
                ts = datetime.now().strftime("%m%d%y")
                safe_name = st.session_state.profile_name.replace(" ", "_") if st.session_state.profile_name else "applicant"
                company_slug = st.session_state.company_name.replace(" ", "_")

                out_dir = Path("./my_documents/cv_applications")
                out_dir.mkdir(parents=True, exist_ok=True)
                resume_file = out_dir / f"{safe_name}_{company_slug}_{ts}_cv.rtf"
                cl_file = out_dir / f"{safe_name}_{company_slug}_{ts}_cover_letter.rtf"
                resume_file.write_text(result.get("resume", ""))
                cl_file.write_text(result.get("cover_letter", ""))

                upload_result = upload_generated_application(
                    company=st.session_state.company_name,
                    role=st.session_state.role_name,
                    resume_path=resume_file,
                    cover_letter_path=cl_file,
                    job_description=job_description,
                )
                if upload_result.get("resume_uploaded") and upload_result.get("cover_letter_uploaded"):
                    st.success("✅ Uploaded to NotebookLM!")
                else:
                    st.warning("⚠️ NotebookLM upload failed — docs saved locally.")


def render_results(job_description: str):
    result = st.session_state.generation_result
    if not result:
        return

    st.divider()
    st.subheader("📝 Generated Documents")

    # ATS Score panel — full width at top
    combined = (result.get("resume", "") + " " + result.get("cover_letter", ""))
    if job_description and combined.strip():
        with st.expander("📊 ATS Keyword Match Score", expanded=True):
            render_ats_panel(job_description, combined)

    tab1, tab2 = st.tabs(["📄 Resume", "✉️ Cover Letter"])

    with tab1:
        st.markdown(result.get("resume", "_No resume generated._"))
        export_buttons("Resume", result.get("resume", ""), "resume", st.session_state.profile_name)

    with tab2:
        st.markdown(result.get("cover_letter", "_No cover letter generated._"))
        export_buttons("Cover_Letter", result.get("cover_letter", ""), "cover_letter", st.session_state.profile_name)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    initialize_session_state()
    render_sidebar()

    # Header
    st.markdown('<h1 class="main-header">hyred</h1>', unsafe_allow_html=True)
    st.caption("Local-first CV & Cover Letter Generator — all processing on-device via Ollama")

    # File upload drop zone
    uploaded_files = st.file_uploader(
        "Drop your CV / resume files here",
        type=["pdf", "md", "txt", "docx", "pages"],
        accept_multiple_files=True,
        label_visibility="collapsed",
        help="PDF, MD, TXT, DOCX — auto-indexed to LanceDB for RAG retrieval",
    )
    if uploaded_files:
        docs_dir = Path("./my_documents")
        docs_dir.mkdir(parents=True, exist_ok=True)
        for uf in uploaded_files:
            dest = docs_dir / uf.name
            if dest.exists():
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                dest = docs_dir / f"{dest.stem}_{ts}{dest.suffix}"
            dest.write_bytes(uf.getbuffer())
            if st.session_state.rag_engine:
                try:
                    chunks = st.session_state.rag_engine.index_file(dest)
                    st.success(f"✅ {uf.name} → {chunks} chunks indexed")
                except Exception as e:
                    st.error(f"❌ {uf.name}: {e}")
        if st.session_state.rag_engine:
            stats = st.session_state.rag_engine.get_stats()
            st.session_state.indexed_files = stats.get("total_files", 0)
            st.session_state.total_chunks = stats.get("total_chunks", 0)

    # Boot services once
    if st.session_state.rag_engine is None:
        setup_local_services()

    display_status_bar()
    st.divider()

    # Job input
    job_description = render_job_input()

    # Generate + results
    render_generate_section(job_description)
    render_results(job_description)


if __name__ == "__main__":
    main()
