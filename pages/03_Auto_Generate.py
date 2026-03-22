#!/usr/bin/env python3
"""
Auto-Generate CV from NotebookLM
Fetches Julian Mackler notebooks and generates tailored CV/cover letter
"""

import streamlit as st
from notebooklm_cv_import import NotebookLMCVImporter

st.set_page_config(
    page_title="Auto-Generate from NotebookLM", page_icon="🤖", layout="centered"
)

# Minimal CSS
st.markdown(
    """
<style>
    .block-container { padding-top: 1rem; }
    h1 { font-size: 1.5rem; }
    .notebook-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
</style>
""",
    unsafe_allow_html=True,
)

# Header
st.title("🤖 Auto-Generate from NotebookLM")
st.markdown("Fetch CV content from your Julian Mackler notebooks")

st.divider()

# Initialize importer
if "cv_importer" not in st.session_state:
    st.session_state.cv_importer = NotebookLMCVImporter()

if "cv_imported" not in st.session_state:
    st.session_state.cv_imported = False

if "cv_content" not in st.session_state:
    st.session_state.cv_content = ""

# Find notebooks button
if st.button("🔍 Find Julian Mackler Notebooks", use_container_width=True):
    with st.spinner("📓 Searching NotebookLM..."):
        notebooks = st.session_state.cv_importer.list_julian_mackler_notebooks()

        if notebooks:
            st.success(f"✅ Found {len(notebooks)} notebooks")

            # Display notebooks
            st.markdown("**Found Notebooks:**")
            for nb in notebooks:
                st.markdown(
                    f"""
                <div class="notebook-card">
                    <strong>📓 {nb['title']}</strong><br>
                    📊 Sources: {nb['source_count']}<br>
                    🆔 ID: `{nb['id'][:8]}...`
                </div>
                """,
                    unsafe_allow_html=True,
                )

            # Store for later use
            st.session_state.notebooks = notebooks

            # Import button
            if st.button(
                "📥 Import CV Content", use_container_width=True, key="import_cv"
            ):
                with st.spinner("📥 Downloading and processing..."):
                    cv_path = st.session_state.cv_importer.import_cv_to_documents()

                    if cv_path:
                        st.session_state.cv_imported = True
                        st.session_state.cv_path = cv_path

                        # Read content
                        with open(cv_path, "r") as f:
                            st.session_state.cv_content = f.read()

                        st.success(f"✅ CV imported to `{cv_path.name}`")

                        # Show preview
                        with st.expander("📄 Preview CV Content"):
                            st.markdown(st.session_state.cv_content[:2000] + "...")

                        st.info(
                            "💡 Your CV is now ready for AI tailoring on the main page!"
                        )
        else:
            st.error("❌ No notebooks found with 'Julian Mackler' in title")
            st.info("""
            **To add CV notebooks:**
            1. Go to https://notebooklm.google.com
            2. Create/upload notebooks with your CV/resume
            3. Include 'Julian Mackler' in the notebook title
            4. Click 'Find Notebooks' again
            """)

st.divider()

# Auto-generate section
if st.session_state.cv_imported:
    st.subheader("✨ Auto-Generate Tailored Documents")

    # Job description input
    job_desc = st.text_area(
        "Paste Job Description",
        height=200,
        placeholder="Paste the job description here to auto-generate tailored CV and cover letter...",
    )

    col1, col2 = st.columns(2)

    with col1:
        company = st.text_input("Company", placeholder="e.g., Satsyil Corp")

    with col2:
        role = st.text_input("Role", placeholder="e.g., Senior Databricks Architect")

    if st.button("🚀 Generate Tailored CV & Cover Letter", use_container_width=True):
        if not job_desc:
            st.warning("⚠️ Please paste a job description")
        elif not company or not role:
            st.warning("⚠️ Please enter company and role")
        else:
            with st.spinner("🤖 AI is tailoring your CV..."):
                # Here you would integrate with the LLM agent
                # For now, show placeholder
                st.success("✅ Integration with main resume builder coming soon!")
                st.info(
                    "💡 For now, use the main Resume Builder page with your imported CV"
                )

st.divider()

# Help section
with st.expander("❓ How this works"):
    st.markdown("""
    ### Auto-Generate from NotebookLM
    
    This feature automatically:
    1. **Searches** your NotebookLM for notebooks with "Julian Mackler" in the title
    2. **Downloads** all content from those notebooks
    3. **Extracts** CV sections (summary, experience, education, skills, etc.)
    4. **Saves** to `./my_documents/cv_base/` as Markdown
    5. **Ready** for AI tailoring
    
    ### What notebooks to create
    
    In NotebookLM, create notebooks like:
    - "Julian Mackler - CV 2026"
    - "Julian Mackler - Work Experience"
    - "Julian Mackler - Education & Certifications"
    - "Julian Mackler - Projects"
    
    ### Privacy
    
    - All downloads happen locally
    - Content saved to your machine only
    - No cloud APIs used for processing
    - Optional: Upload tailored versions back to NotebookLM
    """)

# Sidebar - Quick stats
with st.sidebar:
    st.subheader("📊 NotebookLM Status")

    # Check authentication
    auth_result = st.session_state.cv_importer._run_notebooklm(["auth", "check"])

    if "Authentication is valid" in auth_result.stdout:
        st.success("✅ Authenticated")
    else:
        st.error("❌ Not authenticated")
        st.info("Run: `notebooklm login`")

    if st.session_state.cv_imported:
        st.divider()
        st.success("✅ CV Imported")
        st.caption(f"File: {st.session_state.cv_path.name}")
