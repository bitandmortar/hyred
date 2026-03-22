#!/usr/bin/env python3
"""
Compact Document Import Page - Minimal scrolling
Supports: PDF, MD, TXT, DOCX, PAGES
"""

import streamlit as st
from pathlib import Path
from datetime import datetime
from rag_engine import get_rag_engine

st.set_page_config(
    page_title="Import",
    page_icon="📁",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# Minimal CSS
st.markdown(
    """
<style>
    .block-container { padding-top: 1rem; padding-bottom: 1rem; }
    .stFileUploader { min-height: 80px; }
    h1 { font-size: 1.5rem; margin-bottom: 0.5rem; }
    h2 { font-size: 1.1rem; margin-top: 0.5rem; }
    .format-badge { 
        display: inline-block; 
        background: #3b82f6; 
        color: white; 
        padding: 0.25rem 0.5rem; 
        border-radius: 12px; 
        font-size: 0.75rem; 
        margin: 0.1rem; 
        font-weight: 600;
    }
</style>
""",
    unsafe_allow_html=True,
)

# Header
st.title("📁 Import Documents")

# Formats (compact)
st.markdown(
    """
<span class="format-badge">PDF</span>
<span class="format-badge">MD</span>
<span class="format-badge">TXT</span>
<span class="format-badge">DOCX</span>
<span class="format-badge">PAGES</span>
<span class="format-badge">RTF</span>
<span class="format-badge">ODT</span>
""",
    unsafe_allow_html=True,
)

st.divider()

# Initialize RAG engine
if "rag_engine" not in st.session_state:
    try:
        st.session_state.rag_engine = get_rag_engine()
    except Exception as e:
        st.error(f"❌ RAG Engine: {str(e)}")
        st.stop()

# File uploader (compact)
uploaded_files = st.file_uploader(
    "Drop files here or click to browse",
    type=["pdf", "md", "txt", "docx", "pages", "rtf", "odt"],
    accept_multiple_files=True,
    label_visibility="collapsed",
)

if uploaded_files:
    docs_dir = Path("./my_documents")
    docs_dir.mkdir(parents=True, exist_ok=True)

    # Process files
    for uploaded_file in uploaded_files:
        col1, col2 = st.columns([4, 1])

        with col1:
            st.markdown(f"**{uploaded_file.name}**")

        with col2:
            file_path = docs_dir / uploaded_file.name
            if file_path.exists():
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                file_path = docs_dir / f"{file_path.stem}_{timestamp}{file_path.suffix}"

            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            st.success("✅")

        # Index
        try:
            chunks = st.session_state.rag_engine.index_file(file_path)
            st.caption(f"📊 {chunks} chunks")
        except Exception as e:
            st.error(f"❌ {str(e)}")

        st.divider()

    # Summary (compact)
    stats = st.session_state.rag_engine.get_stats()
    st.info(
        f"✅ **{stats.get('total_files', 0)} files** • **{stats.get('total_chunks', 0)} chunks** • Ready!"
    )

# Recent files (compact)
st.divider()
st.subheader("Recent")

docs_dir = Path("./my_documents")
if docs_dir.exists():
    files = list(docs_dir.glob("*"))
    files = [
        f
        for f in files
        if f.is_file()
        and f.suffix.lower()
        in [".pdf", ".md", ".txt", ".docx", ".pages", ".rtf", ".odt"]
    ]

    if files:
        files = sorted(files, key=lambda x: x.stat().st_mtime, reverse=True)[:5]

        for file in files:
            col3, col4, col5 = st.columns([3, 1, 1])

            with col3:
                st.markdown(f"{file.name}")

            with col4:
                st.caption(f"{file.stat().st_size / 1024:.0f} KB")

            with col5:
                if st.button("🗑️", key=f"del_{file.name}"):
                    try:
                        st.session_state.rag_engine._delete_old_chunks(file)
                        file.unlink()
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ {str(e)}")
    else:
        st.caption("No files yet")
else:
    st.caption("No documents directory")

# Sidebar stats
with st.sidebar:
    if st.session_state.rag_engine:
        stats = st.session_state.rag_engine.get_stats()
        st.metric("Files", stats.get("total_files", 0))
        st.metric("Chunks", stats.get("total_chunks", 0))
