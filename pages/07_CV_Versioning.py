#!/usr/bin/env python3
"""
CV Versioning - Track CV iterations with diff viewer
"""

import streamlit as st
from pathlib import Path
import hashlib
from datetime import datetime
import difflib

st.set_page_config(page_title="CV Versioning", page_icon="📝", layout="wide")

# CV versions directory
CV_VERSIONS_DIR = Path("./my_documents/cv_versions")
CV_VERSIONS_DIR.mkdir(parents=True, exist_ok=True)


def get_cv_versions():
    """Get all CV versions"""
    if not CV_VERSIONS_DIR.exists():
        return []

    versions = []
    for f in CV_VERSIONS_DIR.glob("*.md"):
        stat = f.stat()
        versions.append(
            {
                "path": f,
                "name": f.name,
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime),
                "hash": hashlib.md5(f.read_bytes()).hexdigest()[:8],
            }
        )

    return sorted(versions, key=lambda x: x["modified"], reverse=True)


def save_cv_version(content, name=""):
    """Save new CV version"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = (
        f"cv_{timestamp}_{name.replace(' ', '_')[:20]}.md"
        if name
        else f"cv_{timestamp}.md"
    )
    filepath = CV_VERSIONS_DIR / filename

    with open(filepath, "w") as f:
        f.write(content)

    return filepath


def compare_versions(version1, version2):
    """Compare two CV versions"""
    with open(version1["path"], "r") as f1, open(version2["path"], "r") as f2:
        diff = difflib.unified_diff(
            f1.readlines(),
            f2.readlines(),
            fromfile=version1["name"],
            tofile=version2["name"],
            lineterm="",
        )
        return list(diff)


st.title("📝 CV Versioning")
st.markdown("Track CV iterations and compare versions")

st.divider()

# Current versions
st.subheader("📚 CV Versions")

versions = get_cv_versions()

if versions:
    # Display versions
    for i, version in enumerate(versions[:10]):  # Show last 10 versions
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

        with col1:
            st.markdown(f"**{version['name']}**")
            st.caption(f"Modified: {version['modified'].strftime('%Y-%m-%d %H:%M')}")

        with col2:
            st.caption(f"Size: {version['size'] / 1024:.1f} KB")

        with col3:
            st.caption(f"Hash: `{version['hash']}`")

        with col4:
            # Download button
            with open(version["path"], "r") as f:
                st.download_button(
                    "📥", f.read(), version["name"], key=f"dl_{version['name']}"
                )

        st.divider()

    # Compare versions
    if len(versions) >= 2:
        st.subheader("🔍 Compare Versions")

        col5, col6 = st.columns(2)

        with col5:
            version1_options = {v["name"]: v for v in versions}
            selected_v1 = st.selectbox(
                "Version 1 (Older)", list(version1_options.keys()), key="compare_v1"
            )

        with col6:
            version2_options = {v["name"]: v for v in versions}
            selected_v2 = st.selectbox(
                "Version 2 (Newer)", list(version2_options.keys()), key="compare_v2"
            )

        if st.button("🔍 Compare"):
            v1 = version1_options[selected_v1]
            v2 = version2_options[selected_v2]

            diff = compare_versions(v1, v2)

            # Display diff
            st.code("".join(diff), language="diff")

            # Stats
            additions = len(
                [
                    line
                    for line in diff
                    if line.startswith("+") and not line.startswith("+++")
                ]
            )
            deletions = len(
                [
                    line
                    for line in diff
                    if line.startswith("-") and not line.startswith("---")
                ]
            )

            col7, col8 = st.columns(2)
            with col7:
                st.metric("Additions", additions)
            with col8:
                st.metric("Deletions", deletions)

else:
    st.info("📭 No CV versions yet. Upload your first CV to start versioning!")

st.divider()

# Save current CV
st.subheader("💾 Save Current CV")

# Get current CV from documents
current_cv_dir = Path("./my_documents")
if current_cv_dir.exists():
    cv_files = [f for f in current_cv_dir.glob("*.md") if "cv" in f.name.lower()]

    if cv_files:
        selected_cv = st.selectbox("Select CV to version", [f.name for f in cv_files])

        version_name = st.text_input(
            "Version Name (optional)", placeholder="e.g., Satsyil Corp Application"
        )

        if st.button("💾 Save Version"):
            cv_file = current_cv_dir / selected_cv
            with open(cv_file, "r") as f:
                content = f.read()

            saved_path = save_cv_version(content, version_name)
            st.success(f"✅ Saved to `{saved_path.name}`")
            st.rerun()

# Sidebar - Stats
with st.sidebar:
    st.subheader("📊 Version Stats")

    versions = get_cv_versions()

    if versions:
        st.metric("Total Versions", len(versions))

        if len(versions) >= 2:
            oldest = versions[-1]["modified"]
            newest = versions[0]["modified"]
            days = (newest - oldest).days + 1
            st.metric("Time Span", f"{days} days")

            if days > 0:
                st.metric("Versions/Day", f"{len(versions)/days:.2f}")

        # File sizes
        sizes = [v["size"] for v in versions]
        st.metric("Avg Size", f"{sum(sizes)/len(sizes)/1024:.1f} KB")
    else:
        st.caption("No versions yet")
