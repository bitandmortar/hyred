#!/usr/bin/env python3
"""
Job Queue — Batch pipeline with comparison, location clustering, scoring
=========================================================================
SQLite-backed queue. Each entry holds the raw URL, scraped JD data,
parsed structure, ATS pre-score, salary intel, and ghost status.
Supports location clustering and side-by-side comparison.
"""
import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

DB_PATH = Path("./hyred_data/job_queue.db")

LOCATION_CLUSTERS = {
    "Remote":         ["remote", "anywhere", "distributed", "work from home", "wfh"],
    "New York":       ["new york", "nyc", "brooklyn", "manhattan", "queens"],
    "San Francisco":  ["san francisco", "sf", "bay area", "south bay", "silicon valley", "san jose", "oakland"],
    "Los Angeles":    ["los angeles", "la ", "santa monica", "culver city", "venice"],
    "Seattle":        ["seattle", "bellevue", "redmond", "kirkland"],
    "Austin":         ["austin", "texas"],
    "Boston":         ["boston", "cambridge ma"],
    "Chicago":        ["chicago"],
    "Denver":         ["denver", "colorado"],
    "DC / NoVa":      ["washington dc", "arlington", "northern virginia", "mclean", "reston"],
    "NYC Metro":      ["hoboken", "jersey city", "newark"],
    "London":         ["london", "uk", "united kingdom"],
    "Toronto":        ["toronto", "canada"],
    "Berlin":         ["berlin", "germany"],
    "Amsterdam":      ["amsterdam", "netherlands"],
}


def _get_conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS job_queue (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            added_at        TEXT NOT NULL,
            url             TEXT,
            status          TEXT DEFAULT 'pending',
            company         TEXT,
            role            TEXT,
            location_raw    TEXT,
            location_cluster TEXT,
            remote_policy   TEXT,
            seniority       TEXT,
            tech_stack      TEXT,
            required_skills TEXT,
            salary_range    TEXT,
            salary_intel    TEXT,
            ats_prescore    INTEGER,
            ghost_status    TEXT,
            ghost_days_old  INTEGER,
            job_description TEXT,
            parsed_jd       TEXT,
            interest_level  INTEGER DEFAULT 3,
            notes           TEXT,
            selected        INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    return conn

def cluster_location(location: str) -> str:
    """Map a raw location string to a cluster label."""
    if not location:
        return "Unknown"
    tl = location.lower()
    for cluster, keywords in LOCATION_CLUSTERS.items():
        if any(k in tl for k in keywords):
            return cluster
    return location.split(",")[0].strip().title() if location else "Unknown"


def add_job(url: str = "", job_description: str = "", scraped_data: Optional[Dict] = None,
            parsed_jd: Optional[Dict] = None, salary_intel: Optional[Dict] = None,
            ghost_result: Optional[Dict] = None, ats_prescore: int = 0) -> int:
    """Insert a job into the queue. Returns new row id."""
    scraped = scraped_data or {}
    parsed = parsed_jd or {}
    location_raw = parsed.get("location") or scraped.get("location") or ""
    cluster = cluster_location(location_raw)

    conn = _get_conn()
    cur = conn.execute("""
        INSERT INTO job_queue
            (added_at, url, status, company, role, location_raw, location_cluster,
             remote_policy, seniority, tech_stack, required_skills,
             salary_range, salary_intel, ats_prescore, ghost_status, ghost_days_old,
             job_description, parsed_jd, selected)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,0)
    """, (
        datetime.now().isoformat(), url, "pending",
        parsed.get("company") or scraped.get("company"),
        parsed.get("job_title") or scraped.get("job_title"),
        location_raw, cluster,
        parsed.get("remote_policy", "unspecified"),
        parsed.get("seniority", "mid"),
        json.dumps(parsed.get("tech_stack", [])),
        json.dumps(parsed.get("required_skills", [])),
        parsed.get("salary_range") or (salary_intel or {}).get("jd_stated"),
        json.dumps(salary_intel or {}),
        ats_prescore,
        (ghost_result or {}).get("status", "unknown"),
        (ghost_result or {}).get("days_old"),
        job_description,
        json.dumps(parsed_jd or {}),
    ))
    conn.commit()
    row_id = cur.lastrowid
    conn.close()
    return row_id


def list_queue(status_filter: Optional[str] = None) -> List[Dict]:
    conn = _get_conn()
    q = "SELECT * FROM job_queue"
    args = []
    if status_filter:
        q += " WHERE status=?"
        args.append(status_filter)
    q += " ORDER BY id DESC"
    rows = conn.execute(q, args).fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        for key in ("tech_stack", "required_skills", "salary_intel", "parsed_jd"):
            try:
                d[key] = json.loads(d[key] or "null")
            except Exception:
                pass
        result.append(d)
    return result


def get_job(row_id: int) -> Optional[Dict]:
    conn = _get_conn()
    row = conn.execute("SELECT * FROM job_queue WHERE id=?", (row_id,)).fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    for key in ("tech_stack", "required_skills", "salary_intel", "parsed_jd"):
        try:
            d[key] = json.loads(d[key] or "null")
        except Exception:
            pass
    return d


def update_job(row_id: int, **kwargs):
    if not kwargs:
        return
    for key in ("tech_stack", "required_skills", "salary_intel", "parsed_jd"):
        if key in kwargs and not isinstance(kwargs[key], str):
            kwargs[key] = json.dumps(kwargs[key])
    sets = ", ".join(f"{k}=?" for k in kwargs)
    conn = _get_conn()
    conn.execute(f"UPDATE job_queue SET {sets} WHERE id=?", (*kwargs.values(), row_id))
    conn.commit()
    conn.close()


def set_selected(row_ids: List[int], selected: bool = True):
    conn = _get_conn()
    conn.execute("UPDATE job_queue SET selected=0")
    if selected and row_ids:
        placeholders = ",".join("?" * len(row_ids))
        conn.execute(f"UPDATE job_queue SET selected=1 WHERE id IN ({placeholders})", row_ids)
    conn.commit()
    conn.close()


def delete_job(row_id: int):
    conn = _get_conn()
    conn.execute("DELETE FROM job_queue WHERE id=?", (row_id,))
    conn.commit()
    conn.close()


def get_clusters() -> Dict[str, List[Dict]]:
    """Group queue entries by location cluster."""
    jobs = list_queue()
    clusters: Dict[str, List[Dict]] = {}
    for job in jobs:
        cluster = job.get("location_cluster") or "Unknown"
        clusters.setdefault(cluster, []).append(job)
    return clusters
