#!/usr/bin/env python3
"""
ATS Keyword Scorer - Local Analysis
=====================================
Scores generated resume/cover letter against job description keywords.
No external APIs — pure local string analysis.
"""

import re
from collections import Counter
from typing import Dict, List

STOP_WORDS = {
    "a","an","the","and","or","but","in","on","at","to","for","of","with","by",
    "from","as","is","was","are","were","be","been","being","have","has","had",
    "do","does","did","will","would","could","should","may","might","must",
    "can","you","we","they","their","our","your","this","that","these","those",
    "it","its","not","no","nor","so","yet","both","either","each","few","more",
    "most","other","some","such","than","too","very","just","about","above",
    "after","before","between","during","if","into","through","under","until",
    "while","who","which","what","when","where","how","all","any","also","well",
    "work","experience","team","new","role","company","position","job",
    "candidate","ability","strong","excellent","opportunity","required",
    "preferred","including","related","working","looking","seeking","help",
    "across","within","please","apply","must","will","use","used","using",
    "one","two","three","years","year","per","day","week","month","make",
    "build","built","good","great","high","low","large","small","based",
    "able","responsible","help","manage","ensure","support","provide",
    # ── EEOC / legal boilerplate ──────────────────────────────────────────
    "disability","veteran","veterans","gender","race","ethnicity","religion",
    "national","origin","sexual","orientation","status","equal","employer",
    "discrimination","affirmative","action","protected","class","eeo",
    "applicants","regardless","consideration","employment","without",
    "minorities","female","females","male","males","qualified","individuals",
    # ── Generic job-posting filler ────────────────────────────────────────
    "join","grow","growing","fast","innovative","passionate","driven",
    "excited","dynamic","collaborative","environment","culture","mission",
    "values","diverse","inclusion","inclusive","belong","belonging","people",
    "talent","hire","hiring","apply","applications","applicant","submit",
    "resume","cover","letter","interview","salary","compensation","benefits",
    "bonus","equity","stock","pto","vacation","remote","hybrid","office",
    "location","travel","relocation","authorized","sponsorship","visa",
    "citizen","clearance","background","check","drug","test","screening",
}


def _tokenize(text: str) -> List[str]:
    """Extract meaningful tokens from text."""
    return re.findall(r"\b[a-z][a-z0-9+#._/-]*\b", text.lower())


def _extract_keywords(text: str) -> List[str]:
    """Extract unigrams and meaningful bigrams from text."""
    tokens = _tokenize(text)
    unigrams = [t for t in tokens if len(t) > 2 and t not in STOP_WORDS]

    bigrams = []
    for i in range(len(tokens) - 1):
        a, b = tokens[i], tokens[i + 1]
        if a not in STOP_WORDS and b not in STOP_WORDS and len(a) > 2 and len(b) > 2:
            bigrams.append(f"{a} {b}")

    return unigrams + bigrams


def score_ats_match(job_description: str, generated_output: str) -> Dict:
    """
    Score how well generated output matches JD keywords.

    Returns dict with:
        score        - 0-100 integer
        matched      - list of matched keywords (top 20)
        missing      - list of missing high-frequency JD keywords (top 15)
        matched_count
        total_jd_keywords
    """
    jd_kw = Counter(_extract_keywords(job_description))
    out_kw = set(_extract_keywords(generated_output))

    # Focus on top 50 most-used JD keywords
    top_jd = dict(jd_kw.most_common(50))

    matched = [k for k in top_jd if k in out_kw]
    missing = [k for k in top_jd if k not in out_kw]

    total_weight = sum(top_jd.values())
    matched_weight = sum(top_jd[k] for k in matched)

    score = round((matched_weight / total_weight * 100) if total_weight > 0 else 0)

    return {
        "score": score,
        "matched": matched[:20],
        "missing": missing[:15],
        "matched_count": len(matched),
        "total_jd_keywords": len(top_jd),
    }
