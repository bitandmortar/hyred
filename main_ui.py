#!/usr/bin/env python3
"""
Local Resume Builder - Main UI (Streamlit)
===========================================
Zero-data-leak resume and cover letter tailoring application.
Runs entirely locally on M2 Mac with no external API calls.

All processing: Local (Ollama, sentence-transformers, LanceDB, MarkItDown)
No cloud APIs: No OpenAI, Anthropic, NotebookLM, Firecrawl
Privacy: All data stays within local network
"""

import streamlit as st
from pathlib import Path
from datetime import datetime

# Import local modules
from job_scraper import LocalJobScraper
from rag_engine import get_rag_engine
from llm_agent import get_llm_agent
from file_watcher import start_file_watcher, get_watcher_status
from notebooklm_integration import NotebookLMIntegration, upload_generated_application

# Page configuration
st.set_page_config(
    page_title="hyred",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://github.com/hyred",
        "Report a bug": "https://github.com/hyred/issues",
        "About": "# hyred\nAI-powered resume tailoring.",
    },
)

# Custom CSS with OMNI fonts
st.markdown(
    """
<style>
    /* Barlow Font */
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
    
    /* Inclusive Sans */
    @font-face {
        font-family: 'Inclusive Sans';
        src: local('Inclusive Sans'), url('file:///Volumes/OMNI_01/10_SOURCE/50_Ops/FONTS/InclusiveSans-Regular.ttf') format('truetype');
    }
    
    /* Korolev */
    @font-face {
        font-family: 'Korolev';
        src: local('Korolev'), url('file:///Volumes/OMNI_01/10_SOURCE/50_Ops/FONTS/Korolev Bold.otf') format('opentype');
        font-weight: 700;
    }
    
    /* Apply fonts */
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
    
    .status-badge {
        font-family: 'Inclusive Sans', sans-serif !important;
        font-weight: 600 !important;
    }
</style>
""",
    unsafe_allow_html=True,
)


def initialize_session_state():
    """Initialize Streamlit session state"""
    if "rag_engine" not in st.session_state:
        st.session_state.rag_engine = None
    if "llm_agent" not in st.session_state:
        st.session_state.llm_agent = None
    if "notebooklm" not in st.session_state:
        st.session_state.notebooklm = None
    if "watcher_status" not in st.session_state:
        st.session_state.watcher_status = "starting"
    if "indexed_files" not in st.session_state:
        st.session_state.indexed_files = 0
    if "total_chunks" not in st.session_state:
        st.session_state.total_chunks = 0
    if "generation_result" not in st.session_state:
        st.session_state.generation_result = None
    if "job_description" not in st.session_state:
        st.session_state.job_description = ""
    if "company_name" not in st.session_state:
        st.session_state.company_name = ""
    if "role_name" not in st.session_state:
        st.session_state.role_name = ""


def setup_local_services():
    """Initialize all local services (RAG, LLM, File Watcher, NotebookLM)"""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        with st.spinner("🧠 Loading RAG Engine..."):
            try:
                st.session_state.rag_engine = get_rag_engine()
                stats = st.session_state.rag_engine.get_stats()
                st.session_state.indexed_files = stats.get("total_files", 0)
                st.session_state.total_chunks = stats.get("total_chunks", 0)
                st.success("✅ RAG Engine Ready")
            except Exception as e:
                st.error(f"❌ RAG Engine: {str(e)}")

    with col2:
        with st.spinner("🤖 Loading LLM Agent..."):
            try:
                st.session_state.llm_agent = get_llm_agent()
                if st.session_state.llm_agent.available:
                    st.success("✅ LLM Agent Ready")
                else:
                    st.warning("⚠️ LLM not available")
            except Exception as e:
                st.error(f"❌ LLM Agent: {str(e)}")

    with col3:
        with st.spinner("👁️  Starting File Watcher..."):
            try:

                def on_file_change(file_path):
                    # Re-index changed file
                    if st.session_state.rag_engine:
                        st.session_state.rag_engine.index_file(Path(file_path))
                        # Update stats
                        stats = st.session_state.rag_engine.get_stats()
                        st.session_state.indexed_files = stats.get("total_files", 0)
                        st.session_state.total_chunks = stats.get("total_chunks", 0)

                start_file_watcher("./my_documents", on_file_change)
                st.session_state.watcher_status = "running"
                st.success("✅ File Watcher Active")
            except Exception as e:
                st.error(f"❌ File Watcher: {str(e)}")
                st.session_state.watcher_status = "error"

    with col4:
        with st.spinner("📓 Connecting NotebookLM..."):
            try:
                st.session_state.notebooklm = NotebookLMIntegration()
                if st.session_state.notebooklm.authenticated:
                    st.success("✅ NotebookLM Ready")
                else:
                    st.warning("⚠️ NotebookLM not authenticated")
            except Exception as e:
                st.error(f"❌ NotebookLM: {str(e)}")


def display_status_bar():
    """Display status bar with system health"""
    watcher_status = get_watcher_status()

    status_cols = st.columns(4)

    with status_cols[0]:
        st.metric(
            label="📁 Indexed Files", value=st.session_state.indexed_files, delta=None
        )

    with status_cols[1]:
        st.metric(
            label="📊 Total Chunks", value=st.session_state.total_chunks, delta=None
        )

    with status_cols[2]:
        st.metric(
            label="👁️  File Watcher",
            value=watcher_status["status"].title(),
            delta=(
                "✅ Active" if watcher_status["status"] == "running" else "⚠️ Inactive"
            ),
        )

    with status_cols[3]:
        llm_status = (
            "✅ Ready"
            if st.session_state.llm_agent and st.session_state.llm_agent.available
            else "⚠️ Offline"
        )
        st.metric(label="🤖 LLM Backend", value=llm_status, delta=None)


def main():
    """Main application"""

    # Compact header with drag & drop
    st.markdown('<h1 class="main-header">hyred</h1>', unsafe_allow_html=True)
    st.caption("AI-powered resume tailoring")

    # Quick action: Auto-import from NotebookLM
    col_import1, col_import2 = st.columns([4, 1])
    with col_import1:
        st.caption(
            "🤖 Have CV in NotebookLM? Auto-import from notebooks with 'Julian Mackler' in title"
        )
    with col_import2:
        if st.button("🤖 Auto-Import CV", use_container_width=True, key="quick_import"):
            st.switch_page("pages/03_Auto_Generate.py")

    # Drag & drop zone (compact)
    uploaded_files = st.file_uploader(
        "Drop resumes here or click to browse",
        type=["pdf", "md", "txt", "docx", "pages"],
        accept_multiple_files=True,
        label_visibility="collapsed",
        help="PDF, MD, TXT, DOCX, PAGES - Auto-indexed to LanceDB",
    )

    if uploaded_files:
        docs_dir = Path("./my_documents")
        docs_dir.mkdir(parents=True, exist_ok=True)

        for uploaded_file in uploaded_files:
            file_path = docs_dir / uploaded_file.name
            if file_path.exists():
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                file_path = docs_dir / f"{file_path.stem}_{timestamp}{file_path.suffix}"

            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            # Index file
            try:
                if st.session_state.rag_engine:
                    chunks = st.session_state.rag_engine.index_file(file_path)
                    st.success(f"✅ {uploaded_file.name} → {chunks} chunks")
            except Exception as e:
                st.error(f"❌ {str(e)}")

        # Update stats
        if st.session_state.rag_engine:
            stats = st.session_state.rag_engine.get_stats()
            st.session_state.indexed_files = stats.get("total_files", 0)
            st.session_state.total_chunks = stats.get("total_chunks", 0)

    # Auto-detect clipboard (show notification if clipboard likely has job info)
    if "clipboard_checked" not in st.session_state:
        st.session_state.clipboard_checked = False

    if not st.session_state.clipboard_checked:
        # Show clipboard paste helper
        st.info(
            """
        💡 **Clipboard Detection:** If you have a job URL or description copied, paste it below!
        
        Press **⌘V** (Mac) or **Ctrl+V** (Windows) in the input fields below.
        """,
            icon="📋",
        )
        st.session_state.clipboard_checked = True

    # Initialize session state
    initialize_session_state()

    # Setup services (only once)
    if st.session_state.rag_engine is None:
        setup_local_services()

    # Display status bar
    display_status_bar()

    # Main content area
    st.divider()

    # Two-column layout
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("🎯 Job Description Input")

        # Dual input method: URL or manual paste
        input_method = st.radio(
            "Choose input method:",
            ["🔗 Scrape from URL", "📋 Paste Job Description"],
            horizontal=True,
            label_visibility="collapsed",
        )

        job_description = ""

        if input_method == "🔗 Scrape from URL":
            url_input = st.text_input(
                "Job Posting URL",
                placeholder="https://company.greenhouse.io/jobs/123456 or paste description below",
                help="We'll scrape the job description locally using Playwright (no external APIs). Tip: If you have a URL copied, just press ⌘V/Ctrl+V here!",
            )

            # Auto-detect if pasted text is URL or description
            if url_input:
                if url_input.startswith("http://") or url_input.startswith("https://"):
                    # It's a URL, scrape it
                    with st.spinner("🔍 Scraping job description..."):
                        scraper = LocalJobScraper()
                        result = scraper.scrape_url(url_input)

                        if result.get("error"):
                            st.warning(f"⚠️ {result['error']}")
                            st.info(
                                "💡 Please paste the job description manually instead."
                            )
                        else:
                            # Build job description from scraped data
                            job_parts = []
                            if result.get("job_title"):
                                job_parts.append(
                                    f"**Job Title:** {result['job_title']}"
                                )
                            if result.get("company"):
                                job_parts.append(f"**Company:** {result['company']}")
                            if result.get("job_description"):
                                job_parts.append(
                                    f"\n**Description:**\n{result['job_description']}"
                                )
                            if result.get("requirements"):
                                job_parts.append(
                                    f"\n**Requirements:**\n{result['requirements']}"
                                )

                            job_description = "\n\n".join(job_parts)
                            st.success("✅ Job description scraped successfully!")
                else:
                    # It's probably a job description, switch to paste mode
                    st.info(
                        "💡 Detected job description text. Switching to paste mode..."
                    )
                    input_method = "📋 Paste Job Description"
                    st.session_state.job_description = url_input
                    st.rerun()

        else:  # Manual paste
            job_description = st.text_area(
                "Paste Job Description",
                value=st.session_state.job_description,
                height=400,
                placeholder="Paste the full job description here...",
                help="Include job title, company, requirements, and responsibilities",
            )

            st.session_state.job_description = job_description

        # Company and Role input (for NotebookLM upload)
        col_company, col_role = st.columns(2)
        with col_company:
            company_name = st.text_input(
                "🏢 Company Name",
                value=st.session_state.company_name,
                placeholder="e.g., E Corp",
                help="Used for organizing uploads to NotebookLM",
            )
            st.session_state.company_name = company_name
        with col_role:
            role_name = st.text_input(
                "🎯 Job Role",
                value=st.session_state.role_name,
                placeholder="e.g., Chief Technology Officer",
                help="Used for organizing uploads to NotebookLM",
            )
            st.session_state.role_name = role_name

        # Generate button
        st.divider()

        generate_clicked = st.button(
            "✨ Generate Tailored Resume & Cover Letter",
            type="primary",
            disabled=not job_description
            or not st.session_state.llm_agent
            or not st.session_state.llm_agent.available,
        )

        if generate_clicked:
            with st.spinner("🔍 Searching your resume database..."):
                # Search RAG for relevant chunks
                rag_results = st.session_state.rag_engine.search(
                    job_description, k=10  # Get top 10 relevant chunks
                )

                st.info(
                    f"📊 Found {len(rag_results)} relevant chunks from your work history"
                )

                # Show retrieved chunks (collapsible)
                with st.expander(
                    f"🔍 View retrieved context ({len(rag_results)} chunks)"
                ):
                    for i, chunk in enumerate(rag_results, 1):
                        st.markdown(f"""
                        **Chunk {i}** (Score: {chunk['score']:.3f})
                        📁 File: `{Path(chunk['file_path']).name}`
                        📂 Section: {chunk['metadata']['section']}
                        
                        {chunk['text'][:300]}...
                        """)
                        st.divider()

            with st.spinner("🤖 Generating tailored documents..."):
                # Generate resume and cover letter
                result = st.session_state.llm_agent.generate_resume_and_cover_letter(
                    job_description, rag_results
                )

                st.session_state.generation_result = result

                st.success("✅ Generation complete!")

                # Auto-upload to NotebookLM if authenticated
                if (
                    st.session_state.notebooklm
                    and st.session_state.notebooklm.authenticated
                ):
                    if company_name and role_name:
                        with st.spinner("📓 Uploading to NotebookLM..."):
                            # Save generated files with proper naming format
                            timestamp = datetime.now().strftime("%m%d%y")
                            # Format: FirstName_LastName_Company_Date_cv.rtf
                            applicant_name = (
                                "Applicant"  # Will be replaced with actual name from CV
                            )
                            resume_file = Path(
                                f"./my_documents/cv_applications/{applicant_name}_{company_name.replace(' ', '_')}_{timestamp}_cv.rtf"
                            )
                            cl_file = Path(
                                f"./my_documents/cv_applications/{applicant_name}_{company_name.replace(' ', '_')}_{timestamp}_cover_letter.rtf"
                            )

                            resume_file.write_text(result.get("resume", ""))
                            cl_file.write_text(result.get("cover_letter", ""))

                            # Upload to NotebookLM
                            upload_result = upload_generated_application(
                                company=company_name,
                                role=role_name,
                                resume_path=resume_file,
                                cover_letter_path=cl_file,
                                job_description=job_description,
                            )

                            if upload_result.get(
                                "resume_uploaded"
                            ) and upload_result.get("cover_letter_uploaded"):
                                st.success("✅ Auto-uploaded to NotebookLM!")
                            else:
                                st.warning(
                                    "⚠️ Generation complete but NotebookLM upload failed"
                                )
                    else:
                        st.info(
                            "💡 Enter company name and role to auto-upload to NotebookLM"
                        )

    with col2:
        st.subheader("📚 Your Document Library")

        # Show documents directory
        docs_dir = Path("./my_documents")
        if docs_dir.exists():
            files = list(docs_dir.rglob("*"))
            files = [
                f
                for f in files
                if f.is_file() and f.suffix in [".pdf", ".docx", ".xlsx", ".md", ".txt"]
            ]

            st.metric("Total Files", len(files))

            # Show recent files
            if files:
                st.markdown("**Recent Files:**")
                for f in sorted(files, key=lambda x: x.stat().st_mtime, reverse=True)[
                    :5
                ]:
                    st.markdown(f"📄 {f.name}")
        else:
            st.warning("⚠️ Documents directory not found")
            st.info("💡 Create a `my_documents` folder and add your resume/CV files")

        st.divider()

        # Quick stats
        st.subheader("📊 Database Stats")
        if st.session_state.rag_engine:
            stats = st.session_state.rag_engine.get_stats()
            st.markdown(f"""
            - **Chunks:** {stats.get('total_chunks', 0)}
            - **Files:** {stats.get('total_files', 0)}
            - **Sections:** {len(stats.get('sections', {}))}
            """)

    # Display generation results (full width)
    if st.session_state.generation_result:
        st.divider()
        st.subheader("📝 Generated Documents")

        result = st.session_state.generation_result

        # Two tabs for resume and cover letter
        tab1, tab2 = st.tabs(["📄 Resume", "✉️ Cover Letter"])

        with tab1:
            st.markdown(result.get("resume", "No resume generated"))

            # Download button for resume
            st.download_button(
                label="📥 Download Resume (.md)",
                data=result.get("resume", ""),
                file_name=f"tailored_resume_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                mime="text/markdown",
            )

        with tab2:
            st.markdown(result.get("cover_letter", "No cover letter generated"))

            # Download button for cover letter
            st.download_button(
                label="📥 Download Cover Letter (.md)",
                data=result.get("cover_letter", ""),
                file_name=f"cover_letter_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                mime="text/markdown",
            )

    # Footer
    st.divider()
    st.markdown(
        """
    <div style="text-align: center; color: #6b7280; font-size: 0.875rem;">
        <p>
            🔒 <strong>Privacy First:</strong> All processing happens locally on your M2 Mac.
            No data leaves your network. No cloud APIs. No tracking.
        </p>
        <p>
            Powered by: Ollama • LanceDB • sentence-transformers • MarkItDown • Playwright
        </p>
    </div>
    """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
