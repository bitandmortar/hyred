#!/usr/bin/env python3
"""
Skills Gap Analysis - Compare CV vs job requirements
"""

import streamlit as st
from pathlib import Path
from rag_engine import get_rag_engine
import re

st.set_page_config(page_title="Skills Gap Analysis", page_icon="📊", layout="wide")

st.title("📊 Skills Gap Analysis")
st.markdown("Compare your CV against job requirements to identify gaps")

st.divider()

# Input
col1, col2 = st.columns(2)

with col1:
    st.subheader("📋 Job Requirements")
    job_desc = st.text_area(
        "Paste job description",
        height=400,
        placeholder="Paste the full job description with requirements...",
    )

with col2:
    st.subheader("🎯 Analysis")

    if st.button("🔍 Analyze Skills Gap", use_container_width=True):
        if not job_desc:
            st.warning("⚠️ Please paste a job description")
        else:
            with st.spinner("📊 Analyzing..."):
                # Get RAG engine
                rag_engine = get_rag_engine()

                # Extract skills from job description
                skills_pattern = r"(?:skills|requirements|qualifications|must have|should have)[:\s]+([^\n]+(?:\n[^\n]+)*?)(?=\n\n|\Z)"
                skills_match = re.search(skills_pattern, job_desc, re.IGNORECASE)

                if skills_match:
                    required_skills = skills_match.group(1).strip().split("\n")
                else:
                    # Fallback: extract bullet points
                    required_skills = re.findall(r"[•\-\*]\s*(.+)", job_desc)

                # Search CV for each skill
                skill_matches = {}
                for skill in required_skills[:20]:  # Limit to 20 skills
                    skill = skill.strip()
                    if len(skill) > 2:
                        results = rag_engine.search(skill, k=3)
                        skill_matches[skill] = results

                # Display analysis
                st.success("✅ Analysis Complete!")

                # Matched skills
                matched = [s for s, r in skill_matches.items() if r]
                unmatched = [s for s, r in skill_matches.items() if not r]

                st.metric("Skills Found", len(matched))
                st.metric("Skills Missing", len(unmatched))

                st.divider()

                # ✅ Matched Skills
                st.subheader("✅ Your Strengths")
                for skill in matched[:10]:
                    with st.expander(f"✅ {skill}"):
                        results = skill_matches[skill]
                        for result in results:
                            st.caption(f"📄 From: {Path(result['file_path']).name}")
                            st.markdown(f"> {result['text'][:200]}...")

                # ❌ Missing Skills
                if unmatched:
                    st.subheader("❌ Skills to Develop")
                    for skill in unmatched:
                        st.warning(f"❌ **{skill}** - Not found in your CV")

                        # Suggest learning resources
                        with st.expander(f"💡 Learn {skill}"):
                            st.markdown("""
                            **Recommended Resources:**
                            - Official documentation
                            - Online courses (Coursera, Udemy, edX)
                            - Practice projects
                            - Books and tutorials
                            
                            **Time Estimate:** 2-4 weeks for proficiency
                            """)

                # Learning Plan
                if unmatched:
                    st.divider()
                    st.subheader("📚 Recommended Learning Plan")

                    for i, skill in enumerate(unmatched[:5], 1):
                        st.markdown(f"""
                        **{i}. {skill}**
                        - Week 1-2: Fundamentals & tutorials
                        - Week 3-4: Practice projects
                        - Week 5-6: Advanced topics
                        - Week 7-8: Build portfolio piece
                        """)

st.divider()

# Visualization
st.subheader("📊 Skills Coverage")

if "skill_matches" in locals():
    matched_count = len([s for s, r in skill_matches.items() if r])
    total_count = len(skill_matches)

    if total_count > 0:
        coverage = (matched_count / total_count) * 100

        # Progress bar
        st.progress(coverage / 100)
        st.caption(
            f"**{coverage:.1f}%** skills coverage ({matched_count}/{total_count})"
        )

        # Breakdown by category
        st.markdown("**By Category:**")

        tech_skills = len(
            [
                s
                for s in skill_matches.keys()
                if any(
                    t in s.lower() for t in ["python", "sql", "aws", "spark", "data"]
                )
            ]
        )
        soft_skills = len(
            [
                s
                for s in skill_matches.keys()
                if any(
                    t in s.lower()
                    for t in ["communication", "leadership", "team", "collaborate"]
                )
            ]
        )

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Technical Skills", tech_skills)
        with col2:
            st.metric("Soft Skills", soft_skills)

# Sidebar - Tips
with st.sidebar:
    st.subheader("💡 Tips")
    st.markdown("""
    **Interpreting Results:**
    
    - ✅ Green = Found in your CV
    - ❌ Red = Not found (gap)
    - ⚠️ Yellow = Partial match
    
    **Action Items:**
    1. Review missing skills
    2. Add relevant experience to CV
    3. Create learning plan
    4. Practice before interview
    """)
