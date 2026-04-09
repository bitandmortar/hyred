#!/usr/bin/env python3
"""
Ghost Job Detector
===================
Flags stale job postings based on:
  - Posted date in the scraped content
  - Listing age heuristics from URL patterns
  - Cross-board staleness signals

Returns a staleness score and human-readable verdict.
"""
import re
from datetime import datetime, timedelta
from typing import Optional, Dict


STALE_DAYS = 45   # listings older than this get flagged


def _extract_date_from_text(text: str) -> Optional[datetime]:
    """Try to find a posted/updated date in the job description text."""
    # Common patterns: "Posted 3 days ago", "Posted January 15, 2024", etc.
    patterns = [
        # "X days/weeks/months ago"
        (r"(\d+)\s+day[s]?\s+ago", lambda m: datetime.now() - timedelta(days=int(m.group(1)))),
        (r"(\d+)\s+week[s]?\s+ago", lambda m: datetime.now() - timedelta(weeks=int(m.group(1)))),
        (r"(\d+)\s+month[s]?\s+ago", lambda m: datetime.now() - timedelta(days=int(m.group(1)) * 30)),
        # ISO date
        (r"(\d{4}-\d{2}-\d{2})", lambda m: datetime.strptime(m.group(1), "%Y-%m-%d")),
        # Month Day, Year
        (r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+(\d{1,2}),?\s+(\d{4})",
         lambda m: datetime.strptime(f"{m.group(1)[:3]} {m.group(2)} {m.group(3)}", "%b %d %Y")),
    ]
    for pattern, parser in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                return parser(match)
            except Exception:
                continue
    return None


def _extract_date_from_url(url: str) -> Optional[datetime]:
    """Some job boards embed dates in URLs."""
    match = re.search(r"(\d{4})[/-](\d{2})[/-](\d{2})", url)
    if match:
        try:
            return datetime(int(match.group(1)), int(match.group(2)), int(match.group(3)))
        except ValueError:
            pass
    return None


def _check_evergreen_signals(url: str, text: str) -> bool:
    """Detect signals that suggest a perpetually-open 'evergreen' listing."""
    evergreen_phrases = [
        "always looking for", "talent pool", "pipeline", "join our talent network",
        "future opportunities", "rolling basis", "ongoing basis",
    ]
    tl = text.lower()
    return any(p in tl for p in evergreen_phrases)


def detect_ghost_job(
    url: str = "",
    job_description: str = "",
    parsed_date: Optional[str] = None,
) -> Dict:
    """
    Analyse a job posting for staleness.

    Returns:
        status:   'fresh' | 'aging' | 'stale' | 'ghost' | 'unknown'
        days_old: int or None
        verdict:  human-readable string
        warning:  bool
    """
    posted_dt = None

    # 1. Try explicitly parsed date from JD parser
    if parsed_date:
        try:
            posted_dt = datetime.fromisoformat(parsed_date)
        except Exception:
            pass

    # 2. Try to extract from text
    if not posted_dt:
        posted_dt = _extract_date_from_text(job_description)

    # 3. Try URL pattern
    if not posted_dt and url:
        posted_dt = _extract_date_from_url(url)

    days_old = None
    if posted_dt:
        days_old = (datetime.now() - posted_dt).days

    is_evergreen = _check_evergreen_signals(url, job_description)

    # Verdict
    if is_evergreen:
        return {
            "status": "ghost",
            "days_old": days_old,
            "verdict": "⚠️ Evergreen listing — likely a talent pool or pipeline post, not an active opening.",
            "warning": True,
        }
    if days_old is None:
        return {
            "status": "unknown",
            "days_old": None,
            "verdict": "📅 Posting date unknown — verify freshness on the job board.",
            "warning": False,
        }
    if days_old <= 7:
        return {"status": "fresh", "days_old": days_old, "verdict": f"✅ Fresh listing ({days_old}d old)", "warning": False}
    if days_old <= STALE_DAYS:
        return {"status": "aging", "days_old": days_old, "verdict": f"🟡 Aging listing ({days_old}d old) — still worth applying", "warning": False}
    if days_old <= 90:
        return {"status": "stale", "days_old": days_old, "verdict": f"🟠 Stale listing ({days_old}d old) — response rate likely lower", "warning": True}
    return {
        "status": "ghost",
        "days_old": days_old,
        "verdict": f"🔴 Likely ghost job ({days_old}d old) — very low response probability",
        "warning": True,
    }
