#!/usr/bin/env python3
"""
Interview Prep Generator - Generate Q&A from CV + job requirements
"""

import streamlit as st
from pathlib import Path
from rag_engine import get_rag_engine
from llm_agent import get_llm_agent

st.set_page_config(page_title="Interview Prep", page_icon="🎯", layout="wide")

st.title("🎯 Interview Prep Generator")
st.markdown("Generate likely interview questions and suggested answers")

st.divider()

# Input section
col1, col2 = st.columns(2)

with col1:
    st.subheader("📋 Job Description")
    job_desc = st.text_area(
        "Paste job description",
        height=300,
        placeholder="Paste the full job description here...",
    )

with col2:
    st.subheader("🏢 Company Info")
    company = st.text_input("Company", placeholder="e.g., Satsyil Corp")
    role = st.text_input("Role", placeholder="e.g., Senior Databricks Architect")

    st.divider()

    # Interview type
    interview_type = st.selectbox(
        "Interview Type",
        [
            "Technical",
            "Behavioral",
            "System Design",
            "Manager",
            "HR Screening",
            "Final Round",
        ],
    )

    # Experience level
    experience_level = st.selectbox(
        "Experience Level", ["Junior", "Mid-Level", "Senior", "Staff", "Principal"]
    )

st.divider()

# Generate button
if st.button("🚀 Generate Interview Prep", use_container_width=True):
    if not job_desc:
        st.warning("⚠️ Please paste a job description")
    elif not company or not role:
        st.warning("⚠️ Please enter company and role")
    else:
        with st.spinner("🤖 Generating interview questions..."):
            # Get RAG engine
            rag_engine = get_rag_engine()

            # Search for relevant experience
            rag_results = rag_engine.search(job_desc, k=10)

            # Get LLM agent
            llm_agent = get_llm_agent()

            # Build prompt
            prompt = f"""You are an expert interview coach. Generate interview questions and suggested answers for:

**Company:** {company}
**Role:** {role}
**Interview Type:** {interview_type}
**Experience Level:** {experience_level}

**Job Description:**
{job_desc}

**Candidate's Experience (from RAG context):**
"""

            for i, chunk in enumerate(rag_results, 1):
                prompt += f"\n{i}. {chunk['text'][:200]}..."

            prompt += """

**Generate:**
1. 5-10 likely interview questions for this specific role and company
2. For each question, provide a suggested answer using the candidate's actual experience from the RAG context
3. Include follow-up questions they might ask
4. Mark which skills/requirements from the job description each question addresses

**Format:**
### Question 1: [Question text]
**Addresses:** [Skill/requirement from job description]
**Suggested Answer:** [Answer using candidate's actual experience]
**Follow-up:** [Likely follow-up question]

### Question 2: ...
"""

            # Generate
            if llm_agent.available:
                result = llm_agent._generate_with_ollama(prompt)

                if result.get("resume"):
                    st.success("✅ Generated!")

                    # Display questions
                    st.markdown(result["resume"])

                    # Download button
                    st.download_button(
                        "📥 Download as Markdown",
                        result["resume"],
                        f"{company}_{role}_Interview_Prep.md",
                        "text/markdown",
                    )
            else:
                st.error("❌ LLM not available. Please ensure Ollama is running.")

st.divider()

# Tips section
with st.expander("💡 Interview Tips"):
    st.markdown("""
    ### Technical Interviews
    
    **Before:**
    - Review the job requirements
    - Practice coding problems
    - Prepare system design examples
    
    **During:**
    - Think out loud
    - Ask clarifying questions
    - Explain your thought process
    
    ### Behavioral Interviews
    
    **STAR Method:**
    - **S**ituation: Describe the context
    - **T**ask: Explain your responsibility
    - **A**ction: Detail what you did
    - **R**esult: Share the outcome
    
    ### System Design
    
    **Framework:**
    1. Requirements clarification
    2. High-level design
    3. Detailed design
    4. Bottleneck analysis
    5. Scaling considerations
    """)

# Sidebar - Recent prep
with st.sidebar:
    st.subheader("📚 Recent Prep Sessions")

    prep_dir = Path("./my_documents/interview_prep")
    if prep_dir.exists():
        prep_files = list(prep_dir.glob("*.md"))
        if prep_files:
            for f in sorted(prep_files, key=lambda x: x.stat().st_mtime, reverse=True)[
                :5
            ]:
                st.caption(f"📄 {f.name}")
        else:
            st.caption("No prep sessions yet")
