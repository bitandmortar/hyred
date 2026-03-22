#!/usr/bin/env python3
"""
Version History — SQLite-backed generation log
================================================
Stores every generation: company, role, ATS score, file paths, timestamp.
Zero external deps beyond stdlib sqlite3.
"""
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

DB_PATH = Path("./hyred_data/version_history.db")


def _get_conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS generations (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at  TEXT    NOT NULL,
            profile_name TEXT,
            company     TEXT,
            role        TEXT,
            location    TEXT,
            ats_score   INTEGER,
            tone        INTEGER,
            model       TEXT,
            resume_md   TEXT,
            cover_letter_md TEXT,
            job_description TEXT,
            notes       TEXT
        )
    """)
    conn.commit()
    return conn

def save_generation(
    company: str, role: str, resume_md: str, cover_letter_md: str,
    ats_score: int = 0, tone: int = 50, model: str = "",
    job_description: str = "", location: str = "",
    profile_name: str = "", notes: str = ""
) -> int:
    """Insert a generation record. Returns the new row id."""
    conn = _get_conn()
    cur = conn.execute("""
        INSERT INTO generations
            (created_at, profile_name, company, role, location, ats_score,
             tone, model, resume_md, cover_letter_md, job_description, notes)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        datetime.now().isoformat(), profile_name, company, role, location,
        ats_score, tone, model, resume_md, cover_letter_md, job_description, notes
    ))
    conn.commit()
    row_id = cur.lastrowid
    conn.close()
    return row_id


def list_generations(limit: int = 50) -> List[Dict]:
    conn = _get_conn()
    rows = conn.execute("""
        SELECT id, created_at, profile_name, company, role, location,
               ats_score, tone, model, notes
        FROM generations ORDER BY id DESC LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_generation(row_id: int) -> Optional[Dict]:
    conn = _get_conn()
    row = conn.execute(
        "SELECT * FROM generations WHERE id=?", (row_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def update_notes(row_id: int, notes: str):
    conn = _get_conn()
    conn.execute("UPDATE generations SET notes=? WHERE id=?", (notes, row_id))
    conn.commit()
    conn.close()


def delete_generation(row_id: int):
    conn = _get_conn()
    conn.execute("DELETE FROM generations WHERE id=?", (row_id,))
    conn.commit()
    conn.close()
