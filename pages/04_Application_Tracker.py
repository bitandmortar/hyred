#!/usr/bin/env python3
"""
04 — Application Tracker
==========================
Full lifecycle tracking: submitted → response → interview → offer/rejection.
SQLite-backed via version_history + job_queue data.
"""
import streamlit as st
import sqlite3
import json
from pathlib import Path
from datetime import datetime, date
from typing import List, Dict

DB_PATH = Path("./hyred_data/applications.db")

STATUS_FLOW = ["drafted", "submitted", "no response", "response", "phone screen",
               "technical", "final round", "offer", "rejected", "withdrawn", "archived"]
STATUS_COLORS = {
    "drafted":      "#9ca3af", "submitted":    "#6366f1", "no response":  "#d1d5db",
    "response":     "#3b82f6", "phone screen": "#8b5cf6", "technical":    "#f59e0b",
    "final round":  "#10b981", "offer":        "#22c55e", "rejected":     "#ef4444",
    "withdrawn":    "#6b7280", "archived":     "#e5e7eb",
}


def _get_conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at      TEXT NOT NULL,
            updated_at      TEXT,
            company         TEXT,
            role            TEXT,
            location        TEXT,
            url             TEXT,
            status          TEXT DEFAULT 'submitted',
            applied_date    TEXT,
            response_date   TEXT,
            interview_dates TEXT,
            offer_amount    TEXT,
            ats_score       INTEGER,
            generation_id   INTEGER,
            notes           TEXT,
            contacts        TEXT,
            follow_up_date  TEXT
        )
    """)
    conn.commit()
    return conn


def add_application(company, role, location="", url="", status="submitted",
                    applied_date=None, ats_score=0, generation_id=None, notes="") -> int:
    conn = _get_conn()
    cur = conn.execute("""
        INSERT INTO applications
            (created_at, updated_at, company, role, location, url, status,
             applied_date, ats_score, generation_id, notes, interview_dates)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
    """, (datetime.now().isoformat(), datetime.now().isoformat(),
          company, role, location, url, status,
          applied_date or date.today().isoformat(),
          ats_score, generation_id, notes, "[]"))
    conn.commit()
    rid = cur.lastrowid
    conn.close()
    return rid


def list_applications() -> List[Dict]:
    conn = _get_conn()
    rows = conn.execute("SELECT * FROM applications ORDER BY updated_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_application(row_id: int, **kwargs):
    kwargs["updated_at"] = datetime.now().isoformat()
    sets = ", ".join(f"{k}=?" for k in kwargs)
    conn = _get_conn()
    conn.execute(f"UPDATE applications SET {sets} WHERE id=?", (*kwargs.values(), row_id))
    conn.commit()
    conn.close()


# ---- UI ----
st.set_page_config(page_title="Application Tracker", page_icon="📋", layout="wide")
st.markdown("# 📋 Application Tracker")
st.caption("Track every application from first draft to offer or rejection.")

tab_board, tab_add, tab_stats = st.tabs(["🗂️ Board", "➕ Add", "📊 Stats"])

with tab_add:
    with st.form("add_app_form"):
        c1, c2 = st.columns(2)
        company = c1.text_input("Company *")
        role = c2.text_input("Role *")
        c3, c4 = st.columns(2)
        location = c3.text_input("Location")
        url = c4.text_input("Job URL")
        c5, c6 = st.columns(2)
        status = c5.selectbox("Initial Status", STATUS_FLOW, index=1)
        applied_date = c6.date_input("Applied Date", value=date.today())
        notes = st.text_area("Notes", height=80)
        submitted = st.form_submit_button("Add Application", type="primary")
        if submitted and company and role:
            add_application(company, role, location, url, status,
                            applied_date.isoformat(), notes=notes)
            st.success(f"✅ Added: {role} @ {company}")
            st.rerun()


with tab_board:
    apps = list_applications()
    if not apps:
        st.info("No applications tracked yet. Add one in the ➕ tab, or applications are auto-added when you generate from the main page.")
    else:
        # Group by status
        status_filter = st.multiselect(
            "Show statuses", STATUS_FLOW,
            default=[s for s in STATUS_FLOW if s not in ("archived",)],
        )
        apps = [a for a in apps if a.get("status") in status_filter]

        # Kanban-style columns — group into 4 stage buckets
        stages = {
            "🔵 Applied": ["submitted", "drafted"],
            "🟡 In Progress": ["response", "phone screen", "technical", "final round"],
            "🟢 Outcome": ["offer"],
            "🔴 Closed": ["rejected", "withdrawn", "no response", "archived"],
        }
        cols = st.columns(len(stages))
        for col, (stage_label, statuses) in zip(cols, stages.items()):
            stage_apps = [a for a in apps if a.get("status") in statuses]
            col.markdown(f"**{stage_label}** ({len(stage_apps)})")
            for a in stage_apps:
                color = STATUS_COLORS.get(a.get("status", ""), "#9ca3af")
                with col.expander(f"{a['company']} · {a['role'][:25]}"):
                    new_status = st.selectbox(
                        "Status", STATUS_FLOW,
                        index=STATUS_FLOW.index(a.get("status","submitted")),
                        key=f"status_{a['id']}"
                    )
                    if new_status != a.get("status"):
                        update_application(a["id"], status=new_status)
                        st.rerun()

                    st.markdown(f"📅 Applied: {a.get('applied_date','?')}")
                    if a.get("ats_score"):
                        st.markdown(f"📊 ATS: {a['ats_score']}")
                    if a.get("url"):
                        st.markdown(f"[🔗 Job posting]({a['url']})")

                    new_notes = st.text_area("Notes", value=a.get("notes",""), key=f"notes_{a['id']}", height=60)
                    if st.button("Save notes", key=f"save_{a['id']}"):
                        update_application(a["id"], notes=new_notes)
                        st.success("Saved")

                    follow_up = st.date_input("Follow-up reminder", key=f"fu_{a['id']}")
                    if st.button("Set reminder", key=f"rem_{a['id']}"):
                        update_application(a["id"], follow_up_date=follow_up.isoformat())

with tab_stats:
    apps_all = list_applications()
    if not apps_all:
        st.info("No data yet.")
    else:
        total = len(apps_all)
        offers = sum(1 for a in apps_all if a.get("status") == "offer")
        rejected = sum(1 for a in apps_all if a.get("status") == "rejected")
        in_progress = sum(1 for a in apps_all if a.get("status") in ("phone screen","technical","final round","response"))
        response_rate = round((in_progress + offers + rejected) / total * 100) if total else 0

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Applied", total)
        c2.metric("Response Rate", f"{response_rate}%")
        c3.metric("Offers", offers)
        c4.metric("In Progress", in_progress)

        st.divider()
        st.subheader("By Status")
        from collections import Counter
        status_counts = Counter(a.get("status","?") for a in apps_all)
        for status, count in sorted(status_counts.items(), key=lambda x: -x[1]):
            color = STATUS_COLORS.get(status, "#9ca3af")
            bar_width = int(count / total * 100)
            st.markdown(
                f"<div style='margin-bottom:6px'>"
                f"<span style='width:120px;display:inline-block'>{status}</span>"
                f"<span style='background:{color};display:inline-block;height:16px;"
                f"width:{bar_width}%;border-radius:4px;vertical-align:middle'></span>"
                f" <b>{count}</b></div>",
                unsafe_allow_html=True,
            )
