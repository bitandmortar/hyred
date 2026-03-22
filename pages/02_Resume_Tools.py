#!/usr/bin/env python3
"""
Resume Tools Integration Page
Integrates Reactive Resume and RenderCV into the Local Resume Builder
"""

import streamlit as st
from pathlib import Path
import subprocess

# Tool paths
REACTIVE_RESUME_PATH = Path("/Volumes/OMNI_01/70_CLONED_REPOS/reactive-resume")
RENDERCV_PATH = Path("/Volumes/OMNI_01/70_CLONED_REPOS/rendercv")

st.set_page_config(
    page_title="Resume Tools - Local Resume Builder", page_icon="🛠️", layout="wide"
)

# Custom CSS with fonts
st.markdown(
    """
<style>
    @import url('file:///Volumes/OMNI_01/10_SOURCE/50_Ops/FONTS/');
    
    .tool-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 15px;
        padding: 2rem;
        margin: 1rem 0;
        color: white;
    }
    
    .tool-title {
        font-size: 2rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    
    .tool-description {
        font-size: 1.1rem;
        opacity: 0.9;
        margin-bottom: 1rem;
    }
    
    .tool-status {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.875rem;
        font-weight: 600;
        margin-right: 0.5rem;
    }
    
    .status-running {
        background: rgba(16, 185, 129, 0.3);
        color: #6ee7b7;
    }
    
    .status-stopped {
        background: rgba(239, 68, 68, 0.3);
        color: #fca5a5;
    }
    
    .feature-list {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""",
    unsafe_allow_html=True,
)

# Header
st.title("🛠️ Resume Tools Integration")
st.markdown("""
**Additional resume building tools** integrated with your Local Resume Builder.
These tools complement the AI-powered tailoring with professional templates and formats.
""")

st.divider()

# Tool 1: Reactive Resume
st.subheader("🌐 Reactive Resume")

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("""
    **Open-source resume builder** with a focus on privacy and customization.
    
    **Key Features:**
    - 🎨 20+ professional templates
    - 📝 Real-time preview
    - 🌍 Multi-language support
    - 🔒 Self-hosted (your data stays local)
    - 📤 Export to PDF, JSON, PNG
    - 🎯 ATS-friendly templates
    - ✨ Drag-and-drop sections
    - 🎨 Custom color themes
    
    **Best For:** Creating visually stunning resumes with professional templates
    """)

    # Feature checklist
    st.markdown(
        """
    <div class="feature-list">
    <strong>✅ What it does better than AI tailoring:</strong>
    <ul>
        <li>Professional template designs</li>
        <li>Visual layout customization</li>
        <li>Multi-page resume support</li>
        <li>Print-ready PDF export</li>
        <li>Section reordering</li>
    </ul>
    </div>
    """,
        unsafe_allow_html=True,
    )

with col2:
    # Check if Reactive Resume is running
    reactive_running = False
    try:
        result = subprocess.run(
            [
                "docker",
                "ps",
                "--filter",
                "name=reactive-resume",
                "--format",
                "{{.Status}}",
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )
        reactive_running = "Up" in result.stdout
    except Exception:
        pass

    if reactive_running:
        st.markdown(
            '<span class="tool-status status-running">● Running</span>',
            unsafe_allow_html=True,
        )
        st.success("Access at: http://localhost:3000")
    else:
        st.markdown(
            '<span class="tool-status status-stopped">● Stopped</span>',
            unsafe_allow_html=True,
        )
        if st.button("🚀 Start Reactive Resume", key="start_reactive"):
            st.info("Starting Reactive Resume via Docker...")
            st.code("""
cd /Volumes/OMNI_01/70_CLONED_REPOS/reactive-resume
docker compose -f compose.dev.yml up -d
            """)

    st.markdown("---")
    st.markdown("**Quick Actions:**")
    st.button(
        "🌐 Open Web Interface", key="open_reactive_web", use_container_width=True
    )
    st.button(
        "📖 View Documentation", key="open_reactive_docs", use_container_width=True
    )
    st.button("⚙️ Configuration", key="config_reactive", use_container_width=True)

st.divider()

# Tool 2: RenderCV
st.subheader("📄 RenderCV")

col3, col4 = st.columns([2, 1])

with col3:
    st.markdown("""
    **LaTeX-based resume generator** that converts YAML/JSON to beautifully formatted PDFs.
    
    **Key Features:**
    - 🎓 Academic & industry templates
    - 📝 YAML/JSON input (version control friendly)
    - 🎨 LaTeX-quality typesetting
    - 📚 Bibliography support
    - 🔬 Publication lists
    - 🎯 ATS-optimized templates
    - 🌐 Multiple languages
    - 📦 Command-line interface
    
    **Best For:** Academic resumes, CVs with publications, technical roles
    """)

    # Feature checklist
    st.markdown(
        """
    <div class="feature-list">
    <strong>✅ What it does better than AI tailoring:</strong>
    <ul>
        <li>LaTeX-quality typesetting</li>
        <li>Publication/bibliography support</li>
        <li>Version control friendly (YAML/JSON)</li>
        <li>Academic CV templates</li>
        <li>Consistent formatting</li>
    </ul>
    </div>
    """,
        unsafe_allow_html=True,
    )

with col4:
    # Check if RenderCV is installed
    rendercv_installed = False
    try:
        result = subprocess.run(
            ["rendercv", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
            cwd=str(RENDERCV_PATH),
        )
        rendercv_installed = result.returncode == 0
    except Exception:
        pass

    if rendercv_installed:
        st.markdown(
            '<span class="tool-status status-running">● Installed</span>',
            unsafe_allow_html=True,
        )
        st.success("Ready to use")
    else:
        st.markdown(
            '<span class="tool-status status-stopped">● Not Installed</span>',
            unsafe_allow_html=True,
        )
        if st.button(
            "📦 Install RenderCV", key="install_rendercv", use_container_width=True
        ):
            st.info("Installing RenderCV via pip...")
            st.code("""
cd /Volumes/OMNI_01/70_CLONED_REPOS/rendercv
pip install -e .
            """)

    st.markdown("---")
    st.markdown("**Quick Actions:**")
    st.button(
        "📖 View Examples", key="open_rendercv_examples", use_container_width=True
    )
    st.button("📝 Create New CV", key="create_rendercv", use_container_width=True)
    st.button("⚙️ Settings", key="config_rendercv", use_container_width=True)

st.divider()

# Integration Workflow
st.subheader("🔄 How These Tools Work Together")

st.markdown("""
### Recommended Workflow:

1. **AI Tailoring (This App)** → Generate tailored content for specific job
   - Use RAG to extract relevant experience
   - Match job requirements
   - Generate custom cover letter

2. **Reactive Resume** → Apply professional template
   - Import tailored content
   - Choose visual template
   - Customize layout & colors
   - Export print-ready PDF

3. **RenderCV** → Create academic/technical CV
   - Convert to YAML format
   - Add publications/citations
   - Generate LaTeX-quality PDF
   - Version control friendly

### When to Use Each:

| Tool | Best For | Output Format |
|------|----------|---------------|
| **AI Tailoring** | Content customization | Markdown (.md) |
| **Reactive Resume** | Industry resumes | PDF, PNG, JSON |
| **RenderCV** | Academic CVs | PDF (LaTeX) |
""")

st.divider()

# Local Tools Status
st.subheader("🖥️ Local Installation Status")

col5, col6, col7 = st.columns(3)

with col5:
    st.metric(label="Reactive Resume", value="Docker Compose", delta="compose.dev.yml")

with col6:
    st.metric(label="RenderCV", value="Python Package", delta="pip installable")

with col7:
    st.metric(
        label="Custom Fonts",
        value="5 Families",
        delta="Barlow, Inclusive, Korolev, Anthropic",
    )

# Font preview
st.markdown("---")
st.subheader("🎨 Custom Fonts Available")

st.markdown(
    """
<style>
    .font-barlow { font-family: 'Barlow', sans-serif; }
    .font-inclusive { font-family: 'Inclusive Sans', sans-serif; }
    .font-korolev { font-family: 'Korolev', sans-serif; }
    .font-anthropic { font-family: 'Anthropic Sans', sans-serif; }
</style>

<div class="font-barlow" style="font-size: 1.5rem;">Barlow - Modern, clean, professional</div>
<div class="font-inclusive" style="font-size: 1.5rem;">Inclusive Sans - Accessible, friendly</div>
<div class="font-korolev" style="font-size: 1.5rem;">Korolev - Geometric, technical</div>
<div class="font-anthropic" style="font-size: 1.5rem;">Anthropic Sans - Contemporary, versatile</div>
""",
    unsafe_allow_html=True,
)

st.info("""
**Font Location:** `/Volumes/OMNI_01/10_SOURCE/50_Ops/FONTS/`

These fonts are automatically applied to the Local Resume Builder UI for a consistent, professional appearance.
""")
