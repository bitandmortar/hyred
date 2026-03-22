#!/usr/bin/env python3
"""
HYRED — NEURAL MIRROR (v4.4)
=====================================
Local-first AI-powered resume tailoring.
All processing on-device via Ollama + LanceDB.
"""

import streamlit as st
from datetime import datetime

from rag_engine import get_rag_engine
from llm_agent import get_llm_agent
from file_watcher import start_file_watcher
from ats_scorer import score_ats_match

# Dynamic NotebookLM detect
try:
    import notebooklm_integration as nblm
    _NOTEBOOKLM_AVAILABLE = True
except ImportError:
    _NOTEBOOKLM_AVAILABLE = False


# ---------------------------------------------------------------------------
# Page Config & Styles
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="HYRED | Neural Mirror", page_icon="👔", layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    /* ── OMNI-CORE DESIGN SYSTEM: HYRED NEURAL MIRROR ───── */
    :root {
        --bg: #030407;
        --panel: rgba(10, 12, 18, 0.7);
        --border: rgba(0, 255, 202, 0.15);
        --accent: #00ffca;
        --accent-glow: rgba(0, 255, 202, 0.4);
        --text: #f0f4f8;
        --dim: #64748b;
    }

    .stApp {
        background-color: var(--bg) !important;
        background-image: 
            radial-gradient(circle at 10% 10%, rgba(0, 255, 202, 0.08) 0%, transparent 40%),
            radial-gradient(circle at 90% 90%, rgba(168, 85, 247, 0.08) 0%, transparent 40%) !important;
        color: var(--text) !important;
    }

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

    [data-testid="stMarkdown"], p, li, span, div, label {
        font-family: 'Anthropic Sans', sans-serif !important;
        line-height: 1.6 !important;
    }

    .main-header {
        font-family: 'Anthropic Serif', serif !important;
        font-weight: 900 !important;
        font-size: 3.5rem !important;
        letter-spacing: -0.02em !important;
        margin-bottom: -0.5rem;
        background: linear-gradient(135deg, #fff 30%, #475569);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
    }

    .sub-brand {
        font-family: 'Anthropic Sans', sans-serif !important;
        text-transform: uppercase;
        letter-spacing: 0.4em;
        font-size: 0.7rem;
        color: var(--accent);
        opacity: 0.8;
        text-align: center;
        margin-bottom: 2rem;
        text-shadow: 0 0 10px var(--accent-glow);
    }

    /* GLASSMORPHISM CONTAINER WRAPPER */
    .st-emotion-cache-12w0qpk { gap: 0rem !important; }
    [data-testid="stVerticalBlock"] > [data-testid="stVerticalBlock"] {
        background: var(--panel);
        backdrop-filter: blur(30px);
        border: 1px solid var(--border);
        border-radius: 20px;
        padding: 2rem;
        box-shadow: 0 8px 48px rgba(0, 0, 0, 0.5);
        margin-bottom: 2rem;
    }

    /* NEURAL CONNECTORS SVG */
    .neural-bridge-container {
        position: absolute;
        top: 0; left: 0; width: 100%; height: 100%;
        pointer-events: none; z-index: -1; opacity: 0.6;
    }
    .neural-path {
        fill: none; stroke: var(--accent); stroke-width: 1.5;
        stroke-linecap: round; stroke-dasharray: 10, 20;
        animation: flow 3s linear infinite; opacity: 0.3;
    }
    @keyframes flow { from { stroke-dashoffset: 60; } to { stroke-dashoffset: 0; } }

    /* STATUS HUD (Horizontal) */
    .status-hud {
        display: flex; gap: 1rem; justify-content: center; margin-bottom: 1.5rem;
    }
    .status-pill {
        background: rgba(0, 255, 202, 0.05);
        border: 1px solid var(--border);
        padding: 4px 12px;
        border-radius: 999px;
        font-size: 0.65rem;
        font-weight: 700;
        letter-spacing: 0.05em;
        color: var(--accent);
    }

    /* ATS GAUGE */
    .ats-score-container {
        background: radial-gradient(circle at center, rgba(0, 255, 202, 0.1) 0%, transparent 70%);
        padding: 2rem; border-radius: 50%; width: 180px; height: 180px;
        display: flex; flex-direction: column; justify-content: center; align-items: center;
        margin: 0 auto 1.5rem; border: 2px solid var(--border);
    }
    .ats-score-big { font-size: 4rem !important; font-weight: 900 !important; line-height: 1 !important; margin: 0 !important; }

    /* Hide Streamlit elements */
    header[data-testid="stHeader"], footer, div[data-testid="stStatusWidget"] { visibility: hidden !important; height: 0; }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Logic Components
# ---------------------------------------------------------------------------
def initialize_session_state():
    defaults = {
        "rag_engine": None, "llm_agent": None, "watcher_status": "starting",
        "indexed_files": 0, "total_chunks": 0, "generation_result": None,
        "profile_name": "", "profile_title": "", "selected_model": "llama3.2",
        "tone": 50, "use_notebooklm": False, "company_name": "", "role_name": "",
        "job_description": ""
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

def setup_local_services():
    try:
        if not st.session_state.rag_engine:
            st.session_state.rag_engine = get_rag_engine()
        if not st.session_state.llm_agent:
            st.session_state.llm_agent = get_llm_agent()
        start_file_watcher("./my_documents", lambda fp: None)
    except Exception as e:
        st.error(f"Service Init Error: {e}")

def render_ats_panel(jd, gen):
    r = score_ats_match(jd, gen)
    score = r["score"]
    color = "#00ffca" if score >= 70 else ("#facc15" if score >= 45 else "#f47067")
    st.markdown(f"""
        <div style="text-align: center;">
            <div class="ats-score-container" style="border-color: {color};">
                <div style="font-size: 0.6rem; color: #64748b;">HYRED SCORE</div>
                <div class="ats-score-big" style="color: {color};">{score}</div>
                <div style="font-size: 0.6rem; color: {color}; font-weight: 800; letter-spacing: 0.1em;">ATS MATCH</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    with c1:
        st.caption("✅ OPTIMIZED")
        for k in r["matched"][:9]:
            st.markdown(f'<div class="status-pill" style="font-size:0.5rem; margin-bottom:4px">{k}</div>', unsafe_allow_html=True)
    with c2:
        st.caption("⚠️ GAPS")
        for k in r["missing"][:9]:
            st.markdown(f'<div class="status-pill" style="color:#f47067; border-color:rgba(244,112,103,0.2); font-size:0.5rem; margin-bottom:4px">{k}</div>', unsafe_allow_html=True)

def export_buttons(label, content, slug, profile):
    safe = (profile or "resume").replace(" ", "_")
    ts = datetime.now().strftime("%y%m%d")
    st.download_button(f"📥 Export {label}", data=content, file_name=f"{safe}_{slug}_{ts}.md", use_container_width=True)


# ---------------------------------------------------------------------------
# Main Interface (Neural Mirror)
# ---------------------------------------------------------------------------
def main():
    initialize_session_state()
    setup_local_services()

    # SIDEBAR
    with st.sidebar:
        st.markdown("## 👤 IDENTITY")
        st.session_state.profile_name = st.text_input("Full Name", st.session_state.profile_name)
        st.session_state.profile_title = st.text_input("Target Role", st.session_state.profile_title)
        st.divider()
        st.markdown("## ⚙️ ENGINE")
        st.session_state.selected_model = st.selectbox("Local Model", ["llama3.2", "llama3.1", "mistral"])
        st.session_state.tone = st.slider("Tone", 0, 100, st.session_state.tone)
        if _NOTEBOOKLM_AVAILABLE:
            st.divider()
            st.session_state.use_notebooklm = st.toggle("NotebookLM Sync", st.session_state.use_notebooklm)

    # HEADER
    st.markdown('<h1 class="main-header">HYRED</h1>', unsafe_allow_html=True)
    st.markdown('<div class="sub-brand">NEURAL MIRROR // LOCAL-FIRST INTELLIGENCE</div>', unsafe_allow_html=True)

    # STATUS HUD
    llm_ok = st.session_state.llm_agent and st.session_state.llm_agent.available
    st.markdown(f"""
        <div class="status-hud">
            <div class="status-pill">RAG: ACTIVE</div>
            <div class="status-pill" style="color: {'#00ffca' if llm_ok else '#f47067'}">LLM: {'READY' if llm_ok else 'OFFLINE'}</div>
            <div class="status-pill">WATCHER: RUNNING</div>
        </div>
    """, unsafe_allow_html=True)

    # LANDING / INPUT
    if not st.session_state.generation_result:
        with st.container():
            st.file_uploader("Drop CV/Knowledge pieces here", type=["pdf", "md", "docx"], label_visibility="collapsed")
            jd_input = st.text_area("Paste Job Description / URL", height=120, value=st.session_state.job_description, placeholder="Target role requirements...", key="jd_input_area")
            
            if st.button("✨ GENERATE NEURAL MATCH", use_container_width=True, type="primary"):
                if not jd_input:
                    st.warning("Please provide a Job Description.")
                else:
                    st.session_state.job_description = jd_input
                    with st.spinner("Analyzing neural alignment..."):
                       res = st.session_state.llm_agent.generate_resume_and_cover_letter(jd_input, [])
                       st.session_state.generation_result = res
                       st.rerun()

    # RESULTS (MIRROR SPLIT)
    else:
        st.markdown("""<div class="neural-bridge-container"><svg width="100%" height="100%" viewBox="0 0 1200 1000" xmlns="http://www.w3.org/2000/svg">
            <path class="neural-path" d="M300,300 Q600,200 900,450" style="animation-delay: 0s;" />
            <path class="neural-path" d="M300,550 Q650,500 850,700" style="animation-delay: 1.2s;" />
            <circle cx="900" cy="450" r="4" fill="var(--accent)" /></svg></div>""", unsafe_allow_html=True)
        
        c_left, c_right = st.columns([1.2, 0.8], gap="large")
        
        with c_left:
            with st.container():
                st.subheader("📄 TAILORED RESUME")
                st.markdown(st.session_state.generation_result.get("resume", ""))
                export_buttons("Resume", st.session_state.generation_result.get("resume", ""), "cv", st.session_state.profile_name)
                if st.button("⬅️ New Generation"):
                    st.session_state.generation_result = None
                    st.rerun()

        with c_right:
            with st.container():
                st.subheader("🎯 OPTIMIZATION")
                render_ats_panel(st.session_state.job_description, st.session_state.generation_result.get("resume", ""))
            
            with st.container():
                st.subheader("✉️ COVER LETTER")
                st.markdown(st.session_state.generation_result.get("cover_letter", ""))
                export_buttons("Letter", st.session_state.generation_result.get("cover_letter", ""), "cl", st.session_state.profile_name)

if __name__ == "__main__":
    main()
