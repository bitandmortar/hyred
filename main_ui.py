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
from cover_letter_config import (
    load_config as load_cl_config, save_config as save_cl_config,
    build_system_addendum, OPENING_STYLE_PROMPTS,
)
from jd_parser import parse_jd
from salary_scraper import get_salary_intel, format_salary_display
from ghost_detector import detect_ghost_job
from version_history import save_generation

try:
    from notebooklm_integration import NotebookLMIntegration, upload_generated_application
    _NOTEBOOKLM_AVAILABLE = True
except ImportError:
    _NOTEBOOKLM_AVAILABLE = False


# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="hyred", page_icon="📄", layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://github.com/bitandmortar/hyred",
        "Report a bug": "https://github.com/bitandmortar/hyred/issues",
        "About": "# hyred\nLocal-first CV & Cover Letter Generator.",
    },
)

st.markdown("""
<style>
    /* Anthropic Variable Fonts */
    @font-face {
        font-family: 'Anthropic Sans';
        src: url('file:///Volumes/OMNI_01/10_SOURCE/50_Ops/FONTS/AnthropicSans-Romans-Variable-25x258.ttf') format('truetype');
        font-weight: 100 900;
        font-style: normal;
    }
    @font-face {
        font-family: 'Anthropic Serif';
        src: url('file:///Volumes/OMNI_01/10_SOURCE/50_Ops/FONTS/AnthropicSerif-Romans-Variable-25x258.ttf') format('truetype');
        font-weight: 100 900;
        font-style: normal;
    }

    /* Fallback / Optional Fonts */
    @font-face { font-family:'Barlow'; src:local('Barlow'),
        url('file:///Volumes/OMNI_01/10_SOURCE/50_Ops/FONTS/Barlow-Regular.ttf') format('truetype');
        font-weight:400; }
    @font-face { font-family:'Barlow'; src:local('Barlow Bold'),
        url('file:///Volumes/OMNI_01/10_SOURCE/50_Ops/FONTS/Barlow-Bold.ttf') format('truetype');
        font-weight:700; }
    @font-face { font-family:'Inclusive Sans'; src:local('Inclusive Sans'),
        url('file:///Volumes/OMNI_01/10_SOURCE/50_Ops/FONTS/InclusiveSans-Regular.ttf') format('truetype'); }
    @font-face { font-family:'Korolev'; src:local('Korolev'),
        url('file:///Volumes/OMNI_01/10_SOURCE/50_Ops/FONTS/Korolev Bold.otf') format('opentype');
        font-weight:700; }

    /* Default UI Priority: Anthropic */
    .main-header {
        font-family: 'Anthropic Serif', 'Korolev', 'Barlow', serif !important;
        font-weight: 900 !important;
        font-size: 3rem !important;
        letter-spacing: -0.01em !important;
        background: linear-gradient(90deg, #fff, #94a3b8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    [data-testid="stHeading"], [data-testid="stSubheader"] {
        font-family: 'Anthropic Sans', 'Barlow', -apple-system, sans-serif !important;
        font-weight: 700 !important;
    }
    
    [data-testid="stMarkdown"], p, li, span, div {
        font-family: 'Anthropic Sans', 'Inclusive Sans', 'Barlow', sans-serif !important;
        font-weight: 400 !important;
        line-height: 1.62 !important;
    }
    
    [data-testid="stButton"]>button {
        font-family: 'Anthropic Sans', 'Barlow', sans-serif !important;
        font-weight: 600 !important;
        letter-spacing: 0.01em !important;
        border-radius: 8px !important;
    }

    .ats-pill-match { display:inline-block; background:#d1fae5; color:#065f46;
        border-radius:9999px; padding:2px 10px; margin:2px; font-size:.78rem; font-weight:600; }
    .ats-pill-miss  { display:inline-block; background:#fee2e2; color:#991b1b;
        border-radius:9999px; padding:2px 10px; margin:2px; font-size:.78rem; font-weight:600; }
    .ats-score-big  { font-size:3rem; font-weight:900; line-height:1; }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
def initialize_session_state():
    defaults = {
        "rag_engine": None, "llm_agent": None, "notebooklm": None,
        "watcher_status": "starting", "indexed_files": 0, "total_chunks": 0,
        "generation_result": None, "job_description": "", "company_name": "",
        "role_name": "", "profile_name": "", "profile_title": "",
        "selected_model": "llama3.2", "tone": 50, "use_notebooklm": False,
        "cl_config": None, "parsed_jd": None, "salary_intel": None,
        "ghost_result": None, "last_saved_version_id": None, "refinement_prompt": "",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
def render_sidebar():
    with st.sidebar:
        st.markdown("## 👤 Profile")
        st.session_state.profile_name = st.text_input(
            "Your Name", value=st.session_state.profile_name, placeholder="First Last")
        st.session_state.profile_title = st.text_input(
            "Target Title", value=st.session_state.profile_title,
            placeholder="e.g. Senior Software Engineer")

        st.divider()
        st.markdown("## 🤖 LLM Settings")
        available_models = ["llama3.2", "llama3.1", "mistral", "qwen2.5", "phi3", "gemma2"]
        if st.session_state.llm_agent and st.session_state.llm_agent.available:
            try:
                live = st.session_state.llm_agent.list_available_models()
                if live:
                    available_models = live
            except Exception:
                pass
        idx = available_models.index(st.session_state.selected_model) \
            if st.session_state.selected_model in available_models else 0
        st.session_state.selected_model = st.selectbox("Ollama Model", available_models, index=idx)
        st.session_state.tone = st.slider("Cover Letter Tone", 0, 100, st.session_state.tone,
            help="0 = Formal & precise  |  100 = Warm & conversational")
        tone_label = "Formal" if st.session_state.tone < 35 else \
            ("Conversational" if st.session_state.tone > 65 else "Balanced")
        st.caption(f"Current: **{tone_label}**")

        st.divider()
        st.markdown("## ✉️ Cover Letter Style")
        cl_cfg = load_cl_config()
        with st.expander("Configure", expanded=False):
            cl_cfg["opening_style"] = st.selectbox(
                "Opening style", list(OPENING_STYLE_PROMPTS.keys()),
                index=list(OPENING_STYLE_PROMPTS.keys()).index(cl_cfg.get("opening_style", "hook")),
                help=OPENING_STYLE_PROMPTS.get(cl_cfg.get("opening_style", "hook"), ""))
            cl_cfg["enthusiasm"] = st.select_slider(
                "Enthusiasm", options=[0, 25, 50, 75, 100], value=cl_cfg.get("enthusiasm", 50),
                format_func=lambda v: {0:"Measured",25:"Professional",50:"Balanced",
                                       75:"Enthusiastic",100:"Passionate"}[v])
            cl_cfg["max_words"] = st.number_input("Max words", 150, 600,
                cl_cfg.get("max_words", 350), step=25)
            cl_cfg["sign_off"] = st.text_input("Sign-off", cl_cfg.get("sign_off", "Best regards"))
            cl_cfg["include_ps"] = st.checkbox("Include P.S.", cl_cfg.get("include_ps", False))
            if cl_cfg["include_ps"]:
                cl_cfg["ps_text"] = st.text_input("P.S. text", cl_cfg.get("ps_text", ""))
            forbidden_raw = st.text_area("Forbidden phrases (one per line)",
                "\n".join(cl_cfg.get("forbidden_phrases", [])), height=80)
            cl_cfg["forbidden_phrases"] = [l.strip() for l in forbidden_raw.splitlines() if l.strip()]
            cl_cfg["custom_instructions"] = st.text_area(
                "Extra instructions", cl_cfg.get("custom_instructions", ""), height=60)
            if st.button("💾 Save cover letter config"):
                save_cl_config(cl_cfg)
                st.session_state.cl_config = cl_cfg
                st.success("Saved!")
        st.session_state.cl_config = cl_cfg

        if _NOTEBOOKLM_AVAILABLE:
            st.divider()
            st.markdown("## 🔧 Integrations")
            st.session_state.use_notebooklm = st.toggle(
                "NotebookLM (optional)", value=st.session_state.use_notebooklm,
                help="Requires Google authentication.")

        st.divider()
        st.markdown("## 📚 Document Library")
        docs_dir = Path("./my_documents")
        if docs_dir.exists():
            files = [f for f in docs_dir.rglob("*")
                     if f.is_file() and f.suffix in [".pdf", ".docx", ".md", ".txt", ".pages"]]
            st.metric("Indexed Files", len(files))
            for f in sorted(files, key=lambda x: x.stat().st_mtime, reverse=True)[:6]:
                st.markdown(f"📄 {f.name}")
        else:
            st.warning("No `my_documents` folder found")


# ---------------------------------------------------------------------------
# Services
# ---------------------------------------------------------------------------
def setup_local_services():
    c1, c2, c3 = st.columns(3)
    with c1:
        with st.spinner("🧠 Loading RAG Engine..."):
            try:
                st.session_state.rag_engine = get_rag_engine()
                stats = st.session_state.rag_engine.get_stats()
                st.session_state.indexed_files = stats.get("total_files", 0)
                st.session_state.total_chunks = stats.get("total_chunks", 0)
                st.success("✅ RAG Engine Ready")
            except Exception as e:
                st.error(f"❌ RAG Engine: {e}")
    with c2:
        with st.spinner("🤖 Loading LLM Agent..."):
            try:
                st.session_state.llm_agent = get_llm_agent()
                st.success("✅ LLM Agent Ready") if st.session_state.llm_agent.available \
                    else st.warning("⚠️ LLM not available — is Ollama running?")
            except Exception as e:
                st.error(f"❌ LLM Agent: {e}")
    with c3:
        with st.spinner("👁️ Starting File Watcher..."):
            try:
                def on_change(fp):
                    if st.session_state.rag_engine:
                        st.session_state.rag_engine.index_file(Path(fp))
                        s = st.session_state.rag_engine.get_stats()
                        st.session_state.indexed_files = s.get("total_files", 0)
                        st.session_state.total_chunks = s.get("total_chunks", 0)
                start_file_watcher("./my_documents", on_change)
                st.session_state.watcher_status = "running"
                st.success("✅ File Watcher Active")
            except Exception as e:
                st.error(f"❌ File Watcher: {e}")
    if _NOTEBOOKLM_AVAILABLE and st.session_state.use_notebooklm:
        with st.spinner("📓 Connecting NotebookLM..."):
            try:
                st.session_state.notebooklm = NotebookLMIntegration()
                if not st.session_state.notebooklm.authenticated:
                    st.warning("⚠️ NotebookLM not authenticated")
            except Exception as e:
                st.error(f"❌ NotebookLM: {e}")


def display_status_bar():
    ws = get_watcher_status()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📁 Indexed Files", st.session_state.indexed_files)
    c2.metric("📊 Chunks", st.session_state.total_chunks)
    c3.metric("👁️ File Watcher", ws["status"].title(),
              "✅ Active" if ws["status"] == "running" else "⚠️ Inactive")
    llm_ok = st.session_state.llm_agent and st.session_state.llm_agent.available
    c4.metric("🤖 LLM Backend", "✅ Ready" if llm_ok else "⚠️ Offline")


# ---------------------------------------------------------------------------
# ATS panel
# ---------------------------------------------------------------------------
def render_ats_panel(job_description: str, generated_text: str):
    r = score_ats_match(job_description, generated_text)
    score = r["score"]
    color = "#10b981" if score >= 70 else ("#f59e0b" if score >= 45 else "#ef4444")
    label = "Strong match" if score >= 70 else ("Decent match" if score >= 45 else "Needs work")
    st.markdown(
        f'<div style="border:1px solid {color};border-radius:12px;padding:16px 20px;margin-bottom:8px">'
        f'<span class="ats-score-big" style="color:{color}">{score}</span>'
        f'<span style="font-size:1.1rem;color:{color};margin-left:8px">/ 100 — {label}</span>'
        f'<div style="font-size:.8rem;color:#6b7280;margin-top:4px">'
        f'{r["matched_count"]} of {r["total_jd_keywords"]} key JD terms found</div></div>',
        unsafe_allow_html=True)
    cm, cx = st.columns(2)
    with cm:
        st.markdown("**✅ Matched**")
        st.markdown(" ".join(f'<span class="ats-pill-match">{k}</span>' for k in r["matched"]) or "_none_",
                    unsafe_allow_html=True)
    with cx:
        st.markdown("**❌ Missing**")
        st.markdown(" ".join(f'<span class="ats-pill-miss">{k}</span>' for k in r["missing"])
                    or "🎉 All top terms covered!", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Export helpers
# ---------------------------------------------------------------------------
def export_buttons(label: str, content: str, slug: str, profile_name: str):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe = (profile_name or "resume").replace(" ", "_")
    base = f"{safe}_{slug}_{ts}"
    c1, c2 = st.columns(2)
    with c1:
        st.download_button(f"📥 {label} (.md)", data=content,
            file_name=f"{base}.md", mime="text/markdown", use_container_width=True)
    with c2:
        try:
            st.download_button(f"📄 {label} (.docx)",
                data=markdown_to_docx_bytes(content, title=label),
                file_name=f"{base}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True)
        except ImportError:
            st.info("Install `python-docx` for DOCX export.")


# ---------------------------------------------------------------------------
# Job input
# ---------------------------------------------------------------------------
def render_job_input() -> str:
    st.subheader("🎯 Job Description")
    pasted = st.text_area(
        "Paste a job URL **or** the full description here",
        value=st.session_state.job_description, height=60,
        placeholder="https://boards.greenhouse.io/… — or paste the full JD text directly",
        help="Supports LinkedIn, Indeed, ZipRecruiter, Glassdoor, Greenhouse, Lever, Workday.",
        key="jd_paste_area")

    job_description = ""
    if pasted:
        pasted = pasted.strip()
        if pasted.startswith("http://") or pasted.startswith("https://"):
            scrape_col, _ = st.columns([1, 3])
            with scrape_col:
                scrape_btn = st.button("🔍 Scrape job posting", use_container_width=True)
            if scrape_btn or st.session_state.get("_last_scraped_url") == pasted:
                if st.session_state.get("_last_scraped_url") != pasted:
                    st.session_state["_last_scraped_url"] = pasted
                    with st.spinner("Scraping locally…"):
                        result = LocalJobScraper().scrape_url(pasted)
                    if result.get("error"):
                        st.warning(f"⚠️ {result['error']}")
                        st.session_state["_scraped_jd"] = ""
                    else:
                        parts = []
                        for field, prefix in [("job_title","**Job Title:**"),("company","**Company:**"),
                                              ("job_description","\n**Description:**\n"),
                                              ("requirements","\n**Requirements:**\n")]:
                            if result.get(field):
                                parts.append(f"{prefix} {result[field]}")
                        st.session_state["_scraped_jd"] = "\n\n".join(parts)
                        if result.get("company") and not st.session_state.company_name:
                            st.session_state.company_name = result["company"]
                        if result.get("job_title") and not st.session_state.role_name:
                            st.session_state.role_name = result["job_title"]
                        st.success("✅ Scraped!")
                job_description = st.session_state.get("_scraped_jd", "")
                if job_description:
                    with st.expander("📋 Scraped preview"):
                        st.text(job_description[:800] + ("…" if len(job_description) > 800 else ""))
        else:
            job_description = pasted
            st.session_state.job_description = pasted
            st.caption(f"✏️ Using pasted description ({len(pasted):,} chars)")

    cc, cr = st.columns(2)
    with cc:
        st.session_state.company_name = st.text_input(
            "🏢 Company", value=st.session_state.company_name, placeholder="E Corp")
    with cr:
        st.session_state.role_name = st.text_input(
            "🎯 Role", value=st.session_state.role_name, placeholder="Chief Technology Officer")
    return job_description


# ---------------------------------------------------------------------------
# Generate
# ---------------------------------------------------------------------------
def render_generate_section(job_description: str):
    llm_ready = st.session_state.llm_agent and st.session_state.llm_agent.available
    st.divider()
    generate_clicked = st.button("✨ Generate Tailored Resume & Cover Letter",
        type="primary", disabled=not job_description or not llm_ready,
        use_container_width=True)
    if not llm_ready:
        st.caption("⚠️ LLM offline — start Ollama with `ollama serve` then refresh.")
    if not (generate_clicked and job_description):
        return

    if st.session_state.llm_agent:
        st.session_state.llm_agent.model = st.session_state.selected_model

    with st.spinner("🔍 Searching document library…"):
        rag_results = st.session_state.rag_engine.search(job_description, k=10)
        st.info(f"📊 Retrieved {len(rag_results)} relevant chunks")
        with st.expander(f"🔍 Context ({len(rag_results)} chunks)"):
            for i, chunk in enumerate(rag_results, 1):
                st.markdown(f"**{i}** (Score: {chunk['score']:.3f})  \n"
                    f"📁 `{Path(chunk['file_path']).name}` · {chunk['metadata']['section']}\n\n"
                    f"{chunk['text'][:280]}…")
                st.divider()

    with st.spinner("🧩 Parsing job structure…"):
        parsed_jd = parse_jd(job_description, model=st.session_state.selected_model)
        st.session_state.parsed_jd = parsed_jd
        salary_intel = get_salary_intel(
            parsed_jd.get("job_title") or st.session_state.role_name,
            parsed_jd.get("location") or "", job_description)
        st.session_state.salary_intel = salary_intel
        ghost_result = detect_ghost_job(job_description=job_description,
                                        parsed_date=parsed_jd.get("posted_date"))
        st.session_state.ghost_result = ghost_result
        if ghost_result.get("warning"):
            st.warning(ghost_result["verdict"])
        sd = format_salary_display(salary_intel)
        if sd:
            st.info(sd)

    cl_cfg = st.session_state.get("cl_config") or load_cl_config()
    cl_addendum = build_system_addendum(cl_cfg)
    orig_prompt = st.session_state.llm_agent.system_prompt
    st.session_state.llm_agent.system_prompt = orig_prompt + cl_addendum

    with st.spinner("🤖 Generating documents…"):
        result = st.session_state.llm_agent.generate_resume_and_cover_letter(
            job_description, rag_results, tone=st.session_state.tone)
        st.session_state.llm_agent.system_prompt = orig_prompt
        st.session_state.generation_result = result
        st.session_state.refinement_prompt = ""
        st.success("✅ Generation complete!")
        combined = result.get("resume","") + " " + result.get("cover_letter","")
        ats = score_ats_match(job_description, combined)["score"]
        vid = save_generation(
            company=st.session_state.company_name, role=st.session_state.role_name,
            resume_md=result.get("resume",""), cover_letter_md=result.get("cover_letter",""),
            ats_score=ats, tone=st.session_state.tone, model=st.session_state.selected_model,
            job_description=job_description,
            location=(st.session_state.parsed_jd or {}).get("location",""),
            profile_name=st.session_state.profile_name)
        st.session_state.last_saved_version_id = vid
        st.caption(f"💾 Auto-saved as version #{vid}")

    if (_NOTEBOOKLM_AVAILABLE and st.session_state.use_notebooklm
            and st.session_state.notebooklm
            and st.session_state.notebooklm.authenticated
            and st.session_state.company_name and st.session_state.role_name):
        with st.spinner("📓 Uploading to NotebookLM…"):
            ts = datetime.now().strftime("%m%d%y")
            safe = (st.session_state.profile_name or "applicant").replace(" ", "_")
            co = st.session_state.company_name.replace(" ", "_")
            out = Path("./my_documents/cv_applications")
            out.mkdir(parents=True, exist_ok=True)
            rf = out / f"{safe}_{co}_{ts}_cv.rtf"
            cf = out / f"{safe}_{co}_{ts}_cover_letter.rtf"
            rf.write_text(result.get("resume",""))
            cf.write_text(result.get("cover_letter",""))
            up = upload_generated_application(company=st.session_state.company_name,
                role=st.session_state.role_name, resume_path=rf, cover_letter_path=cf,
                job_description=job_description)
            if up.get("resume_uploaded") and up.get("cover_letter_uploaded"):
                st.success("✅ Uploaded to NotebookLM!")
            else:
                st.warning("⚠️ NotebookLM upload failed — docs saved locally.")


# ---------------------------------------------------------------------------
# Results + refinement loop
# ---------------------------------------------------------------------------
def render_results(job_description: str):
    result = st.session_state.generation_result
    if not result:
        return

    st.divider()
    st.subheader("📝 Generated Documents")

    combined = result.get("resume","") + " " + result.get("cover_letter","")
    if job_description and combined.strip():
        with st.expander("📊 ATS Keyword Match Score", expanded=True):
            render_ats_panel(job_description, combined)

    with st.expander("🔁 Refine — give feedback and re-generate", expanded=False):
        refinement = st.text_area("What to change?",
            value=st.session_state.get("refinement_prompt",""), height=80,
            placeholder="e.g. 'Shorten by 20%, drop Cerberus project, more emphasis on Rust. Bolder CL opening.'",
            key="refinement_input")
        refine_clicked = st.button("♻️ Re-generate with feedback", type="secondary",
            disabled=not refinement or not (
                st.session_state.llm_agent and st.session_state.llm_agent.available))
        if refine_clicked and refinement:
            refinement_jd = (
                f"CURRENT RESUME:\n{result.get('resume','')}\n\n"
                f"CURRENT COVER LETTER:\n{result.get('cover_letter','')}\n\n"
                f"USER FEEDBACK (apply these changes):\n{refinement}\n\n"
                f"ORIGINAL JOB DESCRIPTION:\n{job_description}"
            )
            with st.spinner("♻️ Re-generating…"):
                cl_cfg = st.session_state.get("cl_config") or load_cl_config()
                orig = st.session_state.llm_agent.system_prompt
                st.session_state.llm_agent.system_prompt = orig + build_system_addendum(cl_cfg)
                new_result = st.session_state.llm_agent.generate_resume_and_cover_letter(
                    refinement_jd, [], tone=st.session_state.tone)
                st.session_state.llm_agent.system_prompt = orig
                st.session_state.generation_result = new_result
                st.session_state.refinement_prompt = refinement
                combined_new = new_result.get("resume","") + " " + new_result.get("cover_letter","")
                ats_new = score_ats_match(job_description, combined_new)["score"]
                vid = save_generation(
                    company=st.session_state.company_name, role=st.session_state.role_name,
                    resume_md=new_result.get("resume",""),
                    cover_letter_md=new_result.get("cover_letter",""),
                    ats_score=ats_new, tone=st.session_state.tone,
                    model=st.session_state.selected_model,
                    job_description=job_description,
                    profile_name=st.session_state.profile_name,
                    notes=f"Refinement: {refinement[:120]}")
                st.success(f"✅ Refined! Saved as version #{vid}")
                st.rerun()

    tab1, tab2 = st.tabs(["📄 Resume", "✉️ Cover Letter"])
    with tab1:
        st.markdown(result.get("resume","_No resume generated._"))
        export_buttons("Resume", result.get("resume",""), "resume", st.session_state.profile_name)
    with tab2:
        st.markdown(result.get("cover_letter","_No cover letter generated._"))
        export_buttons("Cover_Letter", result.get("cover_letter",""), "cover_letter",
                       st.session_state.profile_name)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    initialize_session_state()
    render_sidebar()

    st.markdown('<h1 class="main-header">hyred</h1>', unsafe_allow_html=True)
    st.caption("Local-first CV & Cover Letter Generator — all processing on-device via Ollama")

    uploaded_files = st.file_uploader(
        "Drop your CV / resume files here",
        type=["pdf", "md", "txt", "docx", "pages"], accept_multiple_files=True,
        label_visibility="collapsed", help="Auto-indexed to LanceDB for RAG retrieval")
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
            s = st.session_state.rag_engine.get_stats()
            st.session_state.indexed_files = s.get("total_files", 0)
            st.session_state.total_chunks = s.get("total_chunks", 0)

    if st.session_state.rag_engine is None:
        setup_local_services()

    display_status_bar()
    st.divider()

    job_description = render_job_input()
    render_generate_section(job_description)
    render_results(job_description)


if __name__ == "__main__":
    main()
