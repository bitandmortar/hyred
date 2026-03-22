#!/usr/bin/env python3
"""
Job Description Archive - Searchable archive of all job postings
"""

import streamlit as st
from pathlib import Path
import json
from datetime import datetime
import pandas as pd

st.set_page_config(page_title="Job Archive", page_icon="📚", layout="wide")

# Archive file
ARCHIVE_FILE = Path("./my_documents/job_descriptions.json")


def load_archive():
    """Load job descriptions from archive"""
    if ARCHIVE_FILE.exists():
        with open(ARCHIVE_FILE, "r") as f:
            return json.load(f)
    return []


def save_archive(jobs):
    """Save job descriptions to archive"""
    ARCHIVE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(ARCHIVE_FILE, "w") as f:
        json.dump(jobs, f, indent=2, default=str)


def add_to_archive(company, role, url, description, tags=None):
    """Add job description to archive"""
    jobs = load_archive()
    job = {
        "id": datetime.now().strftime("%Y%m%d%H%M%S"),
        "company": company,
        "role": role,
        "url": url,
        "description": description,
        "tags": tags or [],
        "date_saved": datetime.now().isoformat(),
        "salary_range": "",
        "location": "",
        "tech_stack": "",
    }
    jobs.append(job)
    save_archive(jobs)
    return job


st.title("📚 Job Description Archive")
st.markdown("Searchable archive of all job postings")

st.divider()

# Add new job
st.subheader("➕ Add Job Description")

col1, col2, col3 = st.columns(3)
with col1:
    company = st.text_input("Company", key="jd_company")
with col2:
    role = st.text_input("Role", key="jd_role")
with col3:
    url = st.text_input("Job URL", key="jd_url")

jd_description = st.text_area(
    "Job Description",
    height=200,
    placeholder="Paste the full job description here...",
    key="jd_desc",
)

tags = st.text_input(
    "Tags (comma-separated)",
    placeholder="e.g., remote, python, data engineering",
    key="jd_tags",
)

col4, col5 = st.columns([4, 1])
with col4:
    if st.button("➕ Add to Archive", use_container_width=True, key="add_jd_btn"):
        if company and role and jd_description:
            tag_list = [t.strip() for t in tags.split(",")] if tags else []
            add_to_archive(company, role, url, jd_description, tag_list)
            st.success("✅ Added to archive!")
            st.rerun()

st.divider()

# Search and display
st.subheader("🔍 Search Archive")

jobs = load_archive()

if jobs:
    # Search
    search_query = st.text_input(
        "Search jobs...", placeholder="Search by company, role, skills, or tags..."
    )

    # Filter
    if search_query:
        query_lower = search_query.lower()
        filtered_jobs = [
            job
            for job in jobs
            if (
                query_lower in job["company"].lower()
                or query_lower in job["role"].lower()
                or query_lower in job["description"].lower()
                or any(query_lower in tag.lower() for tag in job.get("tags", []))
            )
        ]
    else:
        filtered_jobs = jobs

    st.caption(f"Found {len(filtered_jobs)} jobs")

    # Display
    if filtered_jobs:
        for job in filtered_jobs:
            with st.container():
                col6, col7, col8 = st.columns([2, 2, 1])

                with col6:
                    st.markdown(f"**{job['company']}**")
                    st.caption(job["role"])

                with col7:
                    if job.get("tags"):
                        tags_str = " • ".join(job["tags"][:5])
                        st.caption(f"🏷️ {tags_str}")

                with col8:
                    st.caption(f"📅 {job['date_saved'][:10]}")

                # Expandable description
                with st.expander("📄 View Description"):
                    st.markdown(job["description"])

                    # Edit metadata
                    col9, col10 = st.columns(2)
                    with col9:
                        new_salary = st.text_input(
                            "Salary",
                            value=job.get("salary_range", ""),
                            key=f"salary_{job['id']}",
                        )
                        new_location = st.text_input(
                            "Location",
                            value=job.get("location", ""),
                            key=f"loc_{job['id']}",
                        )
                    with col10:
                        new_stack = st.text_area(
                            "Tech Stack",
                            value=job.get("tech_stack", ""),
                            key=f"stack_{job['id']}",
                        )

                    if st.button("💾 Save Metadata", key=f"save_{job['id']}"):
                        for j in jobs:
                            if j["id"] == job["id"]:
                                j["salary_range"] = new_salary
                                j["location"] = new_location
                                j["tech_stack"] = new_stack
                                break
                        save_archive(jobs)
                        st.success("✅ Saved!")
                        st.rerun()

                    # Download
                    st.download_button(
                        "📥 Download",
                        job["description"],
                        f"{job['company']}_{job['role']}.md",
                        key=f"dl_{job['id']}",
                    )

                st.divider()

    # Stats
    st.divider()
    st.subheader("📊 Archive Statistics")

    stat_col1, stat_col2, stat_col3 = st.columns(3)

    with stat_col1:
        st.metric("Total Jobs", len(jobs))

    with stat_col2:
        companies = len(set(j["company"] for j in jobs))
        st.metric("Companies", companies)

    with stat_col3:
        roles = len(set(j["role"] for j in jobs))
        st.metric("Unique Roles", roles)

    # Top tags
    all_tags = []
    for job in jobs:
        all_tags.extend(job.get("tags", []))

    if all_tags:
        from collections import Counter

        tag_counts = Counter(all_tags)

        st.caption("**Top Tags:**")
        top_tags = tag_counts.most_common(10)
        tags_str = " • ".join([f"{tag} ({count})" for tag, count in top_tags])
        st.caption(tags_str)

    # Export
    st.divider()
    if st.button("📥 Export to CSV"):
        df = pd.DataFrame(jobs)
        csv = df.to_csv(index=False)
        st.download_button(
            "📥 Download CSV",
            csv,
            f"job_archive_{datetime.now().strftime('%Y%m%d')}.csv",
            "text/csv",
        )

else:
    st.info("📭 No jobs in archive yet. Add your first job description above!")

# Sidebar - Recent
with st.sidebar:
    st.subheader("📚 Recent Jobs")

    if jobs:
        recent = sorted(jobs, key=lambda x: x["date_saved"], reverse=True)[:5]
        for job in recent:
            st.caption(f"📄 {job['company']} - {job['role']}")
    else:
        st.caption("No jobs yet")
