#!/usr/bin/env python3
"""
Salary Scraper — levels.fyi + heuristics
==========================================
Scrapes public salary data from levels.fyi for a given title + location.
Falls back to JD-stated range if scraping fails.
All local, no API keys.
"""
import re
import requests
from bs4 import BeautifulSoup
from typing import Optional, Dict

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


def scrape_levels_fyi(job_title: str, location: str = "") -> Optional[Dict]:
    """
    Attempt to pull salary data from levels.fyi search.
    Returns dict with median, p25, p75, source — or None on failure.
    """
    try:
        query = f"{job_title} {location}".strip().replace(" ", "%20")
        url = f"https://www.levels.fyi/t/{query.replace('%20', '-').lower()}/"
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.status_code != 200:
            return None
        soup = BeautifulSoup(resp.text, "html.parser")

        # levels.fyi renders salary data in structured spans/divs
        salary_els = soup.select('[class*="salary"]') or soup.select('[class*="compensation"]')
        amounts = []
        for el in salary_els[:10]:
            text = el.get_text()
            matches = re.findall(r"\$[\d,]+(?:K|k)?", text)
            for m in matches:
                val = m.replace("$", "").replace(",", "").replace("K", "000").replace("k", "000")
                try:
                    amounts.append(int(val))
                except ValueError:
                    pass

        if amounts:
            amounts.sort()
            n = len(amounts)
            return {
                "median": amounts[n // 2],
                "p25": amounts[n // 4],
                "p75": amounts[3 * n // 4],
                "sample_count": n,
                "source": "levels.fyi",
                "url": url,
            }
    except Exception:
        pass
    return None


def estimate_from_jd(job_description: str) -> Optional[str]:
    """Pull salary range directly from job description text."""
    pattern = r"\$[\d,]+(?:k|K)?(?:\s*[-–—]\s*\$[\d,]+(?:k|K)?)?"
    match = re.search(pattern, job_description)
    return match.group() if match else None


def get_salary_intel(
    job_title: str, location: str = "", job_description: str = ""
) -> Dict:
    """
    Master function — tries levels.fyi, falls back to JD extraction.
    Returns a display-ready dict.
    """
    jd_stated = estimate_from_jd(job_description)
    levels_data = scrape_levels_fyi(job_title, location)

    return {
        "jd_stated": jd_stated,
        "levels_data": levels_data,
        "has_data": bool(jd_stated or levels_data),
    }


def format_salary_display(intel: Dict) -> str:
    """Return a short human-readable summary string."""
    parts = []
    if intel.get("jd_stated"):
        parts.append(f"📋 Listed: **{intel['jd_stated']}**")
    if intel.get("levels_data"):
        d = intel["levels_data"]
        median_k = f"${d['median'] // 1000}k"
        p25_k = f"${d['p25'] // 1000}k"
        p75_k = f"${d['p75'] // 1000}k"
        parts.append(f"📊 Market ({d['source']}): {p25_k}–{p75_k} (median {median_k})")
    if not parts:
        parts.append("💡 No salary data found — check levels.fyi manually")
    return "\n".join(parts)
