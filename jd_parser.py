#!/usr/bin/env python3
"""
JD Parser — Structured extraction via Ollama function calling
==============================================================
Parses a raw job description into a typed structure using the local LLM.
Falls back to regex heuristics if the model doesn't support tool calls.
"""
import json
import re
import requests
from typing import Dict, List, Optional

OLLAMA_URL = "http://localhost:11434"

EXTRACT_PROMPT = """Extract structured data from this job description. 
Return ONLY valid JSON with this exact schema — no markdown, no explanation:
{
  "job_title": "string",
  "company": "string or null",
  "location": "string (city, state or 'Remote' or 'Hybrid')",
  "seniority": "intern|junior|mid|senior|staff|principal|director|vp|executive",
  "employment_type": "full-time|part-time|contract|freelance",
  "required_skills": ["list of required hard skills"],
  "nice_to_have": ["list of preferred/bonus skills"],
  "tech_stack": ["specific technologies, frameworks, languages mentioned"],
  "responsibilities": ["top 5 key responsibilities as brief phrases"],
  "salary_range": "string or null (e.g. '$120k-$150k' or null if not mentioned)",
  "posted_date": "string or null (e.g. '2024-03-01' or null if not mentioned)",
  "remote_policy": "remote|hybrid|onsite|unspecified"
}

JOB DESCRIPTION:
"""


def parse_jd(job_description: str, model: str = "llama3.2", base_url: str = OLLAMA_URL) -> Dict:
    """
    Parse a job description into structured data.
    Tries Ollama LLM first, falls back to heuristics.
    """
    try:
        resp = requests.post(
            f"{base_url}/api/generate",
            json={
                "model": model,
                "prompt": EXTRACT_PROMPT + job_description[:4000],
                "stream": False,
                "options": {"temperature": 0.1, "num_predict": 800},
            },
            timeout=60,
        )
        if resp.status_code == 200:
            raw = resp.json().get("response", "")
            # Strip markdown fences if present
            raw = re.sub(r"```(?:json)?", "", raw).strip().rstrip("`").strip()
            # Find first { ... }
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            if match:
                return json.loads(match.group())
    except Exception:
        pass

    # Heuristic fallback
    return _heuristic_parse(job_description)


def _heuristic_parse(text: str) -> Dict:
    """Regex-based fallback parser."""
    lines = text.splitlines()

    salary_match = re.search(
        r"\$[\d,]+(?:k|K)?(?:\s*[-–]\s*\$[\d,]+(?:k|K)?)?(?:\s*/\s*(?:yr|year|annual))?",
        text
    )

    remote_policy = "unspecified"
    tl = text.lower()
    if "fully remote" in tl or "100% remote" in tl:
        remote_policy = "remote"
    elif "hybrid" in tl:
        remote_policy = "hybrid"
    elif "on-site" in tl or "onsite" in tl or "in office" in tl or "in-office" in tl:
        remote_policy = "onsite"

    seniority = "mid"
    for level, keywords in [
        ("intern", ["intern", "internship"]),
        ("junior", ["junior", "jr.", "entry level", "entry-level", "associate"]),
        ("senior", ["senior", "sr.", "sr "]),
        ("staff", ["staff engineer", "staff software"]),
        ("principal", ["principal"]),
        ("director", ["director"]),
        ("vp", ["vice president", "vp of", "vp,"]),
        ("executive", ["cto", "ceo", "cpo", "chief"]),
    ]:
        if any(k in tl for k in keywords):
            seniority = level
            break

    return {
        "job_title": lines[0].strip() if lines else None,
        "company": None,
        "location": None,
        "seniority": seniority,
        "employment_type": "full-time",
        "required_skills": [],
        "nice_to_have": [],
        "tech_stack": _extract_tech(text),
        "responsibilities": [],
        "salary_range": salary_match.group() if salary_match else None,
        "posted_date": None,
        "remote_policy": remote_policy,
    }


TECH_KEYWORDS = [
    "python","rust","typescript","javascript","go","java","c++","ruby","swift","kotlin",
    "react","vue","angular","next.js","svelte","fastapi","django","flask","rails",
    "postgres","mysql","sqlite","mongodb","redis","elasticsearch","neo4j",
    "docker","kubernetes","terraform","ansible","aws","gcp","azure","cloudflare",
    "ollama","pytorch","tensorflow","huggingface","langchain","llm","rag","vector",
    "git","github","gitlab","ci/cd","graphql","rest","grpc","kafka","rabbitmq",
]


def _extract_tech(text: str) -> List[str]:
    tl = text.lower()
    return [t for t in TECH_KEYWORDS if re.search(r'\b' + re.escape(t) + r'\b', tl)]
