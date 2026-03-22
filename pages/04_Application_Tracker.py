#!/usr/bin/env python3
"""
Application Tracker - Track job applications with status
"""

import streamlit as st
from pathlib import Path
import json
from datetime import datetime
import pandas as pd

st.set_page_config(page_title="Application Tracker", page_icon="📊", layout="wide")

# Data file
TRACKER_FILE = Path("./my_documents/application_tracker.json")


def load_applications():
    """Load applications from JSON file"""
    if TRACKER_FILE.exists():
        with open(TRACKER_FILE, "r") as f:
            return json.load(f)
    return []


def save_applications(apps):
    """Save applications to JSON file"""
    TRACKER_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(TRACKER_FILE, "w") as f:
        json.dump(apps, f, indent=2, default=str)


def add_application(company, role, url, status="Draft"):
    """Add new application"""
    apps = load_applications()
    app = {
        "id": datetime.now().strftime("%Y%m%d%H%M%S"),
        "company": company,
        "role": role,
        "url": url,
        "status": status,
        "date_applied": None,
        "date_updated": datetime.now().isoformat(),
        "salary_range": "",
        "location": "",
        "tech_stack": "",
        "notes": "",
        "cv_version": "",
        "cover_letter": "",
    }
    apps.append(app)
    save_applications(apps)
    return app


def update_application(app_id, **kwargs):
    """Update application fields"""
    apps = load_applications()
    for app in apps:
        if app["id"] == app_id:
            app.update(kwargs)
            app["date_updated"] = datetime.now().isoformat()
            break
    save_applications(apps)


def delete_application(app_id):
    """Delete application"""
    apps = load_applications()
    apps = [app for app in apps if app["id"] != app_id]
    save_applications(apps)


# Initialize session state
if "applications" not in st.session_state:
    st.session_state.applications = load_applications()

# Header
st.title("📊 Application Tracker")
st.markdown("Track all your job applications in one place")

st.divider()

# Add new application
st.subheader("➕ New Application")

col1, col2, col3 = st.columns(3)
with col1:
    company = st.text_input("Company*", key="new_company")
with col2:
    role = st.text_input("Role*", key="new_role")
with col3:
    url = st.text_input("Job URL", key="new_url")

col4, col5 = st.columns([4, 1])
with col4:
    status = st.selectbox(
        "Status",
        ["Draft", "Applied", "Interview", "Offer", "Rejected"],
        key="new_status",
    )
with col5:
    if st.button("➕ Add", use_container_width=True, key="add_app_btn"):
        if company and role:
            add_application(company, role, url, status)
            st.session_state.applications = load_applications()
            st.success("✅ Added!")
            st.rerun()

st.divider()

# Display applications
st.subheader(f"📋 Applications ({len(st.session_state.applications)})")

if st.session_state.applications:
    # Filter by status
    status_filter = st.multiselect(
        "Filter by Status",
        options=["Draft", "Applied", "Interview", "Offer", "Rejected"],
        default=["Draft", "Applied", "Interview", "Offer", "Rejected"],
    )

    filtered_apps = [
        app for app in st.session_state.applications if app["status"] in status_filter
    ]

    if filtered_apps:
        # Display as cards
        for app in filtered_apps:
            with st.container():
                col6, col7, col8, col9, col10 = st.columns([2, 2, 1, 2, 1])

                with col6:
                    st.markdown(f"**{app['company']}**")
                    st.caption(app["role"])

                with col7:
                    status_colors = {
                        "Draft": "📝",
                        "Applied": "✅",
                        "Interview": "🎯",
                        "Offer": "🎉",
                        "Rejected": "❌",
                    }
                    st.caption(
                        f"{status_colors.get(app['status'], '')} {app['status']}"
                    )

                with col8:
                    if app.get("date_applied"):
                        st.caption(f"📅 {app['date_applied']}")
                    else:
                        st.caption("Not applied")

                with col9:
                    if app.get("location"):
                        st.caption(f"📍 {app['location']}")

                with col10:
                    if st.button("🗑️", key=f"del_{app['id']}"):
                        delete_application(app["id"])
                        st.session_state.applications = load_applications()
                        st.rerun()

                # Expandable details
                with st.expander("📝 Details"):
                    col11, col12 = st.columns(2)
                    with col11:
                        new_salary = st.text_input(
                            "Salary Range",
                            value=app.get("salary_range", ""),
                            key=f"salary_{app['id']}",
                        )
                        new_location = st.text_input(
                            "Location",
                            value=app.get("location", ""),
                            key=f"loc_{app['id']}",
                        )
                    with col12:
                        new_stack = st.text_area(
                            "Tech Stack",
                            value=app.get("tech_stack", ""),
                            key=f"stack_{app['id']}",
                        )

                    new_notes = st.text_area(
                        "Notes", value=app.get("notes", ""), key=f"notes_{app['id']}"
                    )

                    # Update button
                    if st.button("💾 Save Changes", key=f"save_{app['id']}"):
                        update_application(
                            app["id"],
                            salary_range=new_salary,
                            location=new_location,
                            tech_stack=new_stack,
                            notes=new_notes,
                        )
                        st.session_state.applications = load_applications()
                        st.success("✅ Saved!")
                        st.rerun()

                    # Status change
                    new_status = st.selectbox(
                        "Update Status",
                        ["Draft", "Applied", "Interview", "Offer", "Rejected"],
                        index=[
                            "Draft",
                            "Applied",
                            "Interview",
                            "Offer",
                            "Rejected",
                        ].index(app["status"]),
                        key=f"status_{app['id']}",
                    )
                    if new_status != app["status"]:
                        update_application(app["id"], status=new_status)
                        if new_status == "Applied" and not app.get("date_applied"):
                            update_application(
                                app["id"],
                                date_applied=datetime.now().strftime("%Y-%m-%d"),
                            )
                        st.session_state.applications = load_applications()
                        st.success(f"✅ Status updated to {new_status}")
                        st.rerun()

                st.divider()

# Stats
st.divider()
st.subheader("📈 Statistics")

if st.session_state.applications:
    stats_col1, stats_col2, stats_col3, stats_col4 = st.columns(4)

    with stats_col1:
        st.metric("Total", len(st.session_state.applications))

    with stats_col2:
        applied = len(
            [a for a in st.session_state.applications if a["status"] == "Applied"]
        )
        st.metric("Applied", applied)

    with stats_col3:
        interviews = len(
            [a for a in st.session_state.applications if a["status"] == "Interview"]
        )
        st.metric("Interviews", interviews)

    with stats_col4:
        offers = len(
            [a for a in st.session_state.applications if a["status"] == "Offer"]
        )
        st.metric("Offers", offers)

    # Conversion rates
    if applied > 0:
        interview_rate = (interviews / applied) * 100
        st.caption(f"Interview Rate: {interview_rate:.1f}%")

    if len(st.session_state.applications) > 0:
        offer_rate = (offers / len(st.session_state.applications)) * 100
        st.caption(f"Offer Rate: {offer_rate:.1f}%")

# Export
st.divider()
if st.button("📥 Export to CSV"):
    if st.session_state.applications:
        df = pd.DataFrame(st.session_state.applications)
        csv = df.to_csv(index=False)
        st.download_button(
            "📥 Download CSV",
            csv,
            f"applications_{datetime.now().strftime('%Y%m%d')}.csv",
            "text/csv",
        )
