#!/usr/bin/env python3
"""
10 — Version History
======================
Browse all saved generations, compare ATS scores over time,
reload any past version into the session for further refinement.
"""
import streamlit as st
from datetime import datetime
from version_history import list_generations, get_generation, delete_generation, update_notes

st.set_page_config(page_title="Version History", page_icon="🕰️", layout="wide")
st.markdown("# 🕰️ Version History")
st.caption("Every generation is auto-saved here. Compare ATS scores, reload any version.")

generations = list_generations(limit=100)

if not generations:
    st.info("No generations saved yet. Generate a resume on the main page to get started.")
    st.stop()

# Summary stats
scores = [g["ats_score"] for g in generations if g.get("ats_score")]
if scores:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Versions", len(generations))
    c2.metric("Best ATS Score", max(scores))
    c3.metric("Average ATS Score", round(sum(scores)/len(scores)))
    c4.metric("Companies Targeted", len(set(g.get("company","?") for g in generations)))
    st.divider()

# Filter
companies = sorted(set(g.get("company","?") for g in generations))
filter_company = st.selectbox("Filter by company", ["All"] + companies)
if filter_company != "All":
    generations = [g for g in generations if g.get("company") == filter_company]

for g in generations:
    score = g.get("ats_score", 0)
    score_color = "#10b981" if score >= 70 else ("#f59e0b" if score >= 45 else "#ef4444")
    ts = g.get("created_at","")[:16].replace("T"," ")

    col_score, col_meta, col_actions = st.columns([1, 5, 2])

    with col_score:
        st.markdown(
            f"<div style='font-size:2rem;font-weight:900;color:{score_color};line-height:1'>{score}</div>"
            f"<div style='font-size:.7rem;color:#9ca3af'>ATS score</div>",
            unsafe_allow_html=True,
        )

    with col_meta:
        role = g.get("role") or "Unknown Role"
        company = g.get("company") or "Unknown"
        model = g.get("model","")
        tone = g.get("tone", 50)
        tone_label = "Formal" if tone < 35 else ("Conversational" if tone > 65 else "Balanced")
        st.markdown(f"**{role}** @ **{company}**")
        st.caption(f"🕐 {ts}  ·  🤖 {model}  ·  🎚️ {tone_label}  ·  #{g['id']}")
        if g.get("notes"):
            st.caption(f"📝 {g['notes']}")

    with col_actions:
        if st.button("🔄 Reload", key=f"reload_{g['id']}", help="Load this version into the session"):
            full = get_generation(g["id"])
            if full:
                st.session_state.generation_result = {
                    "resume": full.get("resume_md",""),
                    "cover_letter": full.get("cover_letter_md",""),
                }
                st.session_state.job_description = full.get("job_description","")
                st.session_state.company_name = full.get("company","")
                st.session_state.role_name = full.get("role","")
                st.success(f"Loaded version #{g['id']} into session. Go to main page to refine.")
        if st.button("🗑️", key=f"del_{g['id']}", help="Delete this version"):
            delete_generation(g["id"])
            st.rerun()

    with st.expander("Preview & Notes"):
        full = get_generation(g["id"])
        if full:
            t1, t2 = st.tabs(["📄 Resume", "✉️ Cover Letter"])
            with t1:
                st.markdown(full.get("resume_md","")[:1200] + ("…" if len(full.get("resume_md","")) > 1200 else ""))
            with t2:
                st.markdown(full.get("cover_letter_md","")[:800] + ("…" if len(full.get("cover_letter_md","")) > 800 else ""))
            new_notes = st.text_input("Notes", value=g.get("notes",""), key=f"notes_{g['id']}")
            if st.button("Save notes", key=f"savenotes_{g['id']}"):
                update_notes(g["id"], new_notes)
                st.rerun()

    st.markdown("---")
