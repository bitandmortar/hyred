#!/usr/bin/env python3
"""
09 — Job Queue & Comparison Pipeline
======================================
Bulk URL import → scrape → parse → score → compare → select → generate.
"""
import streamlit as st

from job_scraper import LocalJobScraper
from jd_parser import parse_jd
from ats_scorer import score_ats_match
from salary_scraper import get_salary_intel
from ghost_detector import detect_ghost_job
from job_queue import (
    add_job, list_queue, delete_job,
    set_selected, get_clusters
)

st.set_page_config(page_title="Job Queue", page_icon="🗂️", layout="wide")

st.markdown("""
<style>
.job-card { border: 1px solid #e5e7eb; border-radius: 10px; padding: 14px 18px; margin-bottom: 10px; }
.job-card:hover { border-color: #6366f1; }
.badge { display:inline-block; padding:2px 9px; border-radius:9999px; font-size:.75rem; font-weight:600; margin:2px; }
.badge-fresh   { background:#d1fae5; color:#065f46; }
.badge-aging   { background:#fef9c3; color:#854d0e; }
.badge-stale   { background:#fee2e2; color:#991b1b; }
.badge-remote  { background:#ede9fe; color:#4c1d95; }
.badge-onsite  { background:#e0f2fe; color:#075985; }
.badge-hybrid  { background:#f0fdf4; color:#14532d; }
.score-ring    { font-size:1.8rem; font-weight:900; line-height:1; }
</style>
""", unsafe_allow_html=True)

st.markdown("# 🗂️ Job Queue")
st.caption("Bulk-import job links, compare them side-by-side, select the best, then generate.")

# ---------------------------------------------------------------------------
# Tab layout
# ---------------------------------------------------------------------------
tab_add, tab_compare, tab_clusters, tab_selected = st.tabs([
    "➕ Add Jobs", "📊 Compare All", "🗺️ By Location", "✅ Selected Queue"
])

scraper = LocalJobScraper()

# ---------------------------------------------------------------------------
# TAB 1 — Add Jobs
# ---------------------------------------------------------------------------
with tab_add:
    st.subheader("Add job URLs")
    st.caption("Paste one URL per line — or mix URLs and raw descriptions separated by `---`")

    bulk_input = st.text_area(
        "URLs / descriptions",
        height=180,
        placeholder=(
            "https://boards.greenhouse.io/company/jobs/123456\n"
            "https://jobs.lever.co/company/abc\n"
            "https://www.linkedin.com/jobs/view/1234567890\n"
            "---\n"
            "Or paste a raw job description here..."
        ),
    )

    rag_engine = st.session_state.get("rag_engine")
    rag_context = ""
    if rag_engine:
        try:
            chunks = rag_engine.search("skills experience background", k=5)
            rag_context = " ".join(c.get("text", "") for c in chunks)
        except Exception:
            pass

    process_btn = st.button("🚀 Process & Add to Queue", type="primary", disabled=not bulk_input)

    if process_btn and bulk_input:
        entries = [e.strip() for e in bulk_input.strip().split("\n") if e.strip()]
        # Group: URLs vs raw text blocks (split on ---)
        raw_blocks = bulk_input.split("---")
        to_process = []
        for block in raw_blocks:
            block = block.strip()
            if not block:
                continue
            lines = [line.strip() for line in block.splitlines() if line.strip()]
            for line in lines:
                if line.startswith("http://") or line.startswith("https://"):
                    to_process.append(("url", line))
            # If no URLs found in this block, treat it as raw JD
            if not any(line.startswith("http") for line in lines) and block:
                to_process.append(("text", block))

        progress = st.progress(0)
        results_placeholder = st.empty()
        added = []

        for i, (kind, content) in enumerate(to_process):
            progress.progress((i + 1) / len(to_process), text=f"Processing {i+1}/{len(to_process)}…")

            with st.spinner(f"Processing: {content[:60]}…"):
                jd_text = ""
                scraped_data = {}
                url = ""

                if kind == "url":
                    url = content
                    result = scraper.scrape_url(url)
                    if not result.get("error"):
                        parts = []
                        for field, prefix in [
                            ("job_title", "Job Title:"), ("company", "Company:"),
                            ("job_description", "Description:\n"), ("requirements", "Requirements:\n"),
                        ]:
                            if result.get(field):
                                parts.append(f"{prefix} {result[field]}")
                        jd_text = "\n\n".join(parts)
                        scraped_data = result
                    else:
                        st.warning(f"Scrape failed for {url[:60]}: {result['error']}")
                        jd_text = ""
                else:
                    jd_text = content

                if not jd_text:
                    continue

                # Parse structure
                parsed = parse_jd(jd_text, model=st.session_state.get("selected_model", "llama3.2"))

                # ATS pre-score against RAG context
                prescore = score_ats_match(jd_text, rag_context)["score"] if rag_context else 0

                # Salary intel
                salary_intel = get_salary_intel(
                    parsed.get("job_title") or scraped_data.get("job_title") or "",
                    parsed.get("location") or "",
                    jd_text,
                )

                # Ghost detector
                ghost = detect_ghost_job(url=url, job_description=jd_text,
                                         parsed_date=parsed.get("posted_date"))

                row_id = add_job(
                    url=url, job_description=jd_text,
                    scraped_data=scraped_data, parsed_jd=parsed,
                    salary_intel=salary_intel, ghost_result=ghost,
                    ats_prescore=prescore,
                )
                added.append((row_id, parsed.get("job_title", "Unknown"), parsed.get("company", "")))

        progress.empty()
        if added:
            st.success(f"✅ Added {len(added)} job(s) to queue:")
            for rid, title, company in added:
                st.markdown(f"- **#{rid}** {title} @ {company or '—'}")
            st.rerun()


# ---------------------------------------------------------------------------
# TAB 2 — Compare All
# ---------------------------------------------------------------------------
with tab_compare:
    jobs = list_queue()
    if not jobs:
        st.info("No jobs in queue yet. Add some in the ➕ tab.")
    else:
        st.subheader(f"Comparing {len(jobs)} job(s)")

        # Sort controls
        sort_col, filter_col = st.columns([1, 2])
        with sort_col:
            sort_by = st.selectbox("Sort by", ["ATS Pre-Score ↓", "Added Date ↓", "Seniority", "Location"])
        with filter_col:
            filter_ghost = st.checkbox("Hide stale/ghost jobs", value=False)
            filter_remote = st.multiselect(
                "Remote policy", ["remote", "hybrid", "onsite", "unspecified"],
                default=["remote", "hybrid", "onsite", "unspecified"]
            )

        # Filter
        display_jobs = [j for j in jobs if j.get("remote_policy", "unspecified") in filter_remote]
        if filter_ghost:
            display_jobs = [j for j in display_jobs if j.get("ghost_status") not in ("stale", "ghost")]

        # Sort
        if sort_by == "ATS Pre-Score ↓":
            display_jobs.sort(key=lambda j: j.get("ats_prescore", 0), reverse=True)
        elif sort_by == "Added Date ↓":
            display_jobs.sort(key=lambda j: j.get("added_at", ""), reverse=True)
        elif sort_by == "Seniority":
            order = ["intern","junior","mid","senior","staff","principal","director","vp","executive"]
            display_jobs.sort(key=lambda j: order.index(j.get("seniority","mid")) if j.get("seniority","mid") in order else 99)
        elif sort_by == "Location":
            display_jobs.sort(key=lambda j: j.get("location_cluster", ""))

        # Bulk select
        select_ids = st.multiselect(
            "Select jobs to generate applications for",
            options=[j["id"] for j in display_jobs],
            format_func=lambda i: next(
                (f"#{j['id']} — {j.get('role','?')} @ {j.get('company','?')}"
                 for j in display_jobs if j["id"] == i), str(i)
            ),
        )
        if st.button("✅ Mark selected for generation", disabled=not select_ids):
            set_selected(select_ids)
            st.success(f"Marked {len(select_ids)} job(s). Go to ✅ Selected Queue tab.")

        st.divider()

        # Job cards
        for j in display_jobs:
            ghost_status = j.get("ghost_status", "unknown")
            ghost_badge_class = {
                "fresh": "badge-fresh", "aging": "badge-aging",
                "stale": "badge-stale", "ghost": "badge-stale"
            }.get(ghost_status, "")
            remote = j.get("remote_policy", "unspecified")
            remote_class = {"remote": "badge-remote", "hybrid": "badge-hybrid", "onsite": "badge-onsite"}.get(remote, "")
            score = j.get("ats_prescore", 0)
            score_color = "#10b981" if score >= 60 else ("#f59e0b" if score >= 35 else "#ef4444")

            tech = j.get("tech_stack") or []
            tech_str = " · ".join(tech[:8]) if isinstance(tech, list) else ""

            salary_intel = j.get("salary_intel") or {}
            salary_display = ""
            if j.get("salary_range"):
                salary_display = j["salary_range"]
            elif isinstance(salary_intel, dict) and salary_intel.get("jd_stated"):
                salary_display = salary_intel["jd_stated"]

            col_score, col_info, col_actions = st.columns([1, 5, 1])
            with col_score:
                st.markdown(
                    f'<div class="score-ring" style="color:{score_color}">{score}</div>'
                    f'<div style="font-size:.7rem;color:#9ca3af">ATS pre-score</div>',
                    unsafe_allow_html=True,
                )
            with col_info:
                title = j.get("role") or "Unknown Role"
                company = j.get("company") or "Unknown Company"
                location = j.get("location_cluster") or j.get("location_raw") or "?"
                seniority = j.get("seniority", "mid")

                badges = ""
                if ghost_badge_class:
                    badges += f'<span class="badge {ghost_badge_class}">{ghost_status}</span>'
                if remote_class:
                    badges += f'<span class="badge {remote_class}">{remote}</span>'
                badges += f'<span class="badge" style="background:#f3f4f6;color:#374151">{seniority}</span>'

                st.markdown(
                    f"**{title}** at **{company}**  \n"
                    f"📍 {location}" + (f"  |  💰 {salary_display}" if salary_display else "") + "  \n"
                    + (f"🛠️ {tech_str}  \n" if tech_str else "")
                    + badges,
                    unsafe_allow_html=True,
                )

            with col_actions:
                if st.button("🗑️", key=f"del_{j['id']}", help="Remove from queue"):
                    delete_job(j["id"])
                    st.rerun()

            if j.get("url"):
                st.caption(f"🔗 {j['url'][:80]}…" if len(j.get("url","")) > 80 else f"🔗 {j['url']}")

            with st.expander("Full details"):
                parsed = j.get("parsed_jd") or {}
                skills = parsed.get("required_skills") or []
                nice = parsed.get("nice_to_have") or []
                if skills:
                    st.markdown("**Required:** " + " · ".join(skills[:12]))
                if nice:
                    st.markdown("**Nice-to-have:** " + " · ".join(nice[:8]))
                if j.get("job_description"):
                    st.text_area("JD", j["job_description"][:1500], height=120, key=f"jd_{j['id']}", disabled=True)

            st.markdown("---")


# ---------------------------------------------------------------------------
# TAB 3 — Location Clusters
# ---------------------------------------------------------------------------
with tab_clusters:
    clusters = get_clusters()
    if not clusters:
        st.info("No jobs in queue yet.")
    else:
        st.subheader(f"{len(clusters)} location cluster(s)")
        for cluster_name, cluster_jobs in sorted(clusters.items()):
            with st.expander(f"📍 {cluster_name}  ({len(cluster_jobs)} job{'s' if len(cluster_jobs)!=1 else ''})"):
                for j in cluster_jobs:
                    score = j.get("ats_prescore", 0)
                    score_color = "#10b981" if score >= 60 else ("#f59e0b" if score >= 35 else "#ef4444")
                    remote = j.get("remote_policy", "")
                    st.markdown(
                        f"**{j.get('role','?')}** @ {j.get('company','?')}  "
                        f"<span style='color:{score_color};font-weight:700'>{score}</span> ATS  "
                        f"· {remote}  · *{j.get('ghost_status','?')}*",
                        unsafe_allow_html=True,
                    )

# ---------------------------------------------------------------------------
# TAB 4 — Selected Queue (ready to generate)
# ---------------------------------------------------------------------------
with tab_selected:
    selected_jobs = [j for j in list_queue() if j.get("selected")]
    if not selected_jobs:
        st.info("No jobs selected yet. Use the 📊 Compare tab to select jobs.")
    else:
        st.subheader(f"{len(selected_jobs)} job(s) queued for generation")
        for j in selected_jobs:
            st.markdown(f"**#{j['id']}** — {j.get('role','?')} @ {j.get('company','?')} · ATS: {j.get('ats_prescore',0)}")
            col1, col2 = st.columns([3, 1])
            with col2:
                if st.button("Generate →", key=f"gen_{j['id']}"):
                    # Pass job to main app via session state and redirect
                    st.session_state.job_description = j.get("job_description", "")
                    st.session_state.company_name = j.get("company", "")
                    st.session_state.role_name = j.get("role", "")
                    st.switch_page("main_ui.py")
            with col1:
                st.caption(j.get("url", "")[:80])
        st.divider()
        if st.button("🗑️ Clear selected queue"):
            set_selected([], selected=False)
            st.rerun()
