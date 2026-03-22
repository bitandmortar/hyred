#!/usr/bin/env python3
"""
Cover Letter Config — JSON-persisted template preferences
===========================================================
Stores structural preferences: opening hook style, sign-off,
max word count, enthusiasm level, forbidden phrases, custom instructions.
"""
import json
from pathlib import Path
from typing import Dict, Any

CONFIG_PATH = Path("./hyred_data/cover_letter_config.json")

ENTHUSIASM_LEVELS = {
    0:  "Measured & precise. Never use exclamation points. Tone is authoritative.",
    25: "Professional warmth. Occasionally express genuine interest, no hyperbole.",
    50: "Balanced. Show clear enthusiasm for the role without overdoing it.",
    75: "Enthusiastic. Express genuine excitement. One exclamation point max per letter.",
    100: "Openly passionate. Convey real excitement and strong desire for this role specifically.",
}

DEFAULTS: Dict[str, Any] = {
    "opening_style": "hook",          # hook | direct | question | achievement
    "sign_off": "Best regards",
    "max_words": 350,
    "enthusiasm": 50,                  # 0-100 mapped to ENTHUSIASM_LEVELS
    "forbidden_phrases": [
        "I am writing to apply",
        "To whom it may concern",
        "I believe I would be a great fit",
        "passionate about",
        "fast-paced environment",
    ],
    "custom_instructions": "",
    "include_ps": False,
    "ps_text": "",
}

OPENING_STYLE_PROMPTS = {
    "hook":        "Open with a compelling one-sentence hook — a specific achievement, bold claim, or vivid scenario that immediately frames why you're the right person.",
    "direct":      "Open by directly stating the role and your most relevant qualification in one crisp sentence. No preamble.",
    "question":    "Open with a rhetorical question that highlights a challenge the company faces and positions you as the answer.",
    "achievement": "Open with your single most impressive quantified achievement that's directly relevant to this role.",
}


def load_config() -> Dict[str, Any]:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    if CONFIG_PATH.exists():
        try:
            return {**DEFAULTS, **json.loads(CONFIG_PATH.read_text())}
        except Exception:
            pass
    return DEFAULTS.copy()


def save_config(config: Dict[str, Any]):
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(config, indent=2))


def build_system_addendum(config: Dict[str, Any]) -> str:
    """Return a prompt addendum that encodes the CL preferences."""
    enthusiasm_note = ENTHUSIASM_LEVELS.get(
        min(ENTHUSIASM_LEVELS.keys(), key=lambda k: abs(k - config["enthusiasm"])),
        ENTHUSIASM_LEVELS[50]
    )
    opening_note = OPENING_STYLE_PROMPTS.get(config["opening_style"], OPENING_STYLE_PROMPTS["hook"])
    forbidden = ", ".join(f'"{p}"' for p in config["forbidden_phrases"]) if config["forbidden_phrases"] else "none"

    lines = [
        f"\nCOVER LETTER STRUCTURAL RULES:",
        f"- Opening style: {opening_note}",
        f"- Sign off with: {config['sign_off']}",
        f"- Maximum words: {config['max_words']} (be concise, cut ruthlessly)",
        f"- Enthusiasm level: {enthusiasm_note}",
        f"- FORBIDDEN phrases (never use): {forbidden}",
    ]
    if config.get("include_ps") and config.get("ps_text"):
        lines.append(f"- End with a P.S.: {config['ps_text']}")
    if config.get("custom_instructions"):
        lines.append(f"- Additional instructions: {config['custom_instructions']}")
    return "\n".join(lines)
