#!/usr/bin/env python3
"""
05 — Interview Prep (Whisper + Ollama)
========================================
Generate role-specific questions → answer out loud → Whisper transcribes →
Ollama scores your answer against the JD → instant feedback loop.
Fully local: whisper.cpp or openai-whisper + Ollama.
"""
import streamlit as st
import subprocess
import tempfile
import json
import requests
from pathlib import Path

OLLAMA_URL = "http://localhost:11434"

st.set_page_config(page_title="Interview Prep", page_icon="🎙️", layout="wide")
st.markdown("# 🎙️ Interview Prep")
st.caption("Generate questions, answer out loud, get scored. All local via Whisper + Ollama.")

# ---- Whisper availability check ----
def _check_whisper_cpp() -> bool:
    try:
        r = subprocess.run(["whisper-cpp", "--version"], capture_output=True, timeout=3)
        return r.returncode == 0
    except Exception:
        return False

def _check_whisper_py() -> bool:
    try:
        import whisper  # noqa
        return True
    except ImportError:
        return False

def transcribe_audio_file(audio_path: str, model: str = "base") -> str:
    """Transcribe using whisper.cpp (preferred) or openai-whisper Python package."""
    # Try whisper.cpp first (faster on Apple Silicon)
    if _check_whisper_cpp():
        try:
            result = subprocess.run(
                ["whisper-cpp", "-m", f"models/ggml-{model}.bin",
                 "-f", audio_path, "--output-txt", "--no-prints"],
                capture_output=True, text=True, timeout=60,
            )
            txt_path = Path(audio_path).with_suffix(".txt")
            if txt_path.exists():
                return txt_path.read_text().strip()
        except Exception:
            pass

    # Fall back to openai-whisper Python package
    try:
        import whisper
        wm = whisper.load_model(model)
        result = wm.transcribe(audio_path)
        return result["text"].strip()
    except ImportError:
        return ""
    except Exception as e:
        return f"Transcription error: {e}"

def _ollama_generate(prompt: str, model: str = "llama3.2", temperature: float = 0.4) -> str:
    try:
        resp = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": model, "prompt": prompt, "stream": False,
                  "options": {"temperature": temperature, "num_predict": 600}},
            timeout=60,
        )
        return resp.json().get("response", "").strip()
    except Exception as e:
        return f"LLM error: {e}"

def generate_questions(job_description: str, model: str, n: int = 8) -> list:
    prompt = f"""Generate {n} interview questions for this job role.
Mix: 2 behavioral (STAR format), 2 technical, 2 situational, 1 culture fit, 1 "why us".
Return ONLY a JSON array of strings — no markdown, no preamble.

JOB DESCRIPTION:
{job_description[:3000]}
"""
    raw = _ollama_generate(prompt, model, temperature=0.6)
    import re
    raw = re.sub(r"```(?:json)?", "", raw).strip().rstrip("`").strip()
    match = re.search(r"\[.*\]", raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except Exception:
            pass
    # Fallback: split by newlines
    lines = [line.strip().lstrip("0123456789.-) ") for line in raw.splitlines() if line.strip()]
    return [line for line in lines if len(line) > 15][:n]

def score_answer(question: str, answer: str, job_description: str, model: str) -> str:
    prompt = f"""You are an interviewer scoring a candidate's answer.

JOB DESCRIPTION (abbreviated):
{job_description[:1500]}

QUESTION: {question}

CANDIDATE'S ANSWER: {answer}

Score the answer on:
1. Relevance (does it address the question?)
2. Specificity (concrete examples vs vague?)
3. Alignment (does it match the job requirements?)
4. Structure (clear and concise?)

Give: a score out of 10, a one-paragraph critique, and one specific improvement suggestion.
Be honest and constructive. Format as:
Score: X/10
Critique: ...
Improve: ...
"""
    return _ollama_generate(prompt, model, temperature=0.3)


# ---- Main UI ----
model = st.session_state.get("selected_model", "llama3.2")

# Whisper status
has_whisper = _check_whisper_cpp() or _check_whisper_py()
if not has_whisper:
    st.warning(
        "⚠️ Whisper not found. Install with:  \n"
        "`pip install openai-whisper`  \n"
        "Or for Apple Silicon native speed: `brew install whisper-cpp`  \n"
        "You can still use text mode."
    )

# Job description source
jd = st.session_state.get("job_description", "")
if not jd:
    jd = st.text_area(
        "Paste job description (or go to main page first)",
        height=120,
        placeholder="Paste the job description here to generate targeted questions…",
    )
else:
    st.success(f"✅ Using JD from session: {jd[:80]}…")
    if st.button("Clear JD"):
        st.session_state.job_description = ""
        st.rerun()

st.divider()

col_settings, col_practice = st.columns([1, 3])

with col_settings:
    st.subheader("⚙️ Settings")
    n_questions = st.slider("Number of questions", 3, 15, 8)
    whisper_model = st.selectbox("Whisper model", ["tiny", "base", "small", "medium"], index=1,
                                 help="Larger = more accurate but slower. 'base' recommended for real-time.")
    answer_mode = st.radio("Answer mode", ["🎤 Voice (Whisper)", "⌨️ Text"], index=0 if has_whisper else 1)

    if st.button("🎲 Generate Questions", type="primary", disabled=not jd):
        with st.spinner("Generating questions…"):
            qs = generate_questions(jd, model, n_questions)
            st.session_state["prep_questions"] = qs
            st.session_state["prep_answers"] = {}
            st.session_state["prep_scores"] = {}
        st.rerun()

with col_practice:
    questions = st.session_state.get("prep_questions", [])
    if not questions:
        st.info("Click **Generate Questions** to start a practice session.")
    else:
        st.subheader(f"📝 {len(questions)} Questions")
        for i, q in enumerate(questions):
            with st.expander(f"Q{i+1}: {q[:70]}{'…' if len(q) > 70 else ''}", expanded=(i == 0)):
                st.markdown(f"**{q}**")

                answer_key = f"ans_{i}"
                score_key = f"score_{i}"

                if answer_mode == "⌨️ Text":
                    answer = st.text_area(
                        "Your answer", height=100,
                        value=st.session_state.get("prep_answers", {}).get(str(i), ""),
                        key=f"ta_{i}",
                    )
                    if st.button("📊 Score my answer", key=f"score_btn_{i}", disabled=not answer):
                        with st.spinner("Scoring…"):
                            feedback = score_answer(q, answer, jd, model)
                            if "prep_answers" not in st.session_state:
                                st.session_state["prep_answers"] = {}
                            if "prep_scores" not in st.session_state:
                                st.session_state["prep_scores"] = {}
                            st.session_state["prep_answers"][str(i)] = answer
                            st.session_state["prep_scores"][str(i)] = feedback
                            st.rerun()

                elif answer_mode == "🎤 Voice (Whisper)" and has_whisper:
                    st.caption("Record your answer, then upload the audio file below.")
                    audio_file = st.file_uploader(
                        "Upload audio (.wav / .mp3 / .m4a)",
                        type=["wav", "mp3", "m4a", "ogg"],
                        key=f"audio_{i}",
                    )
                    if audio_file and st.button("🎙️ Transcribe & Score", key=f"ts_btn_{i}"):
                        with tempfile.NamedTemporaryFile(suffix=Path(audio_file.name).suffix, delete=False) as tmp:
                            tmp.write(audio_file.getbuffer())
                            tmp_path = tmp.name
                        with st.spinner("Transcribing…"):
                            transcript = transcribe_audio_file(tmp_path, whisper_model)
                        st.info(f"📝 Transcript: {transcript}")
                        if transcript and not transcript.startswith("Transcription error"):
                            with st.spinner("Scoring…"):
                                feedback = score_answer(q, transcript, jd, model)
                                st.session_state.setdefault("prep_answers", {})[str(i)] = transcript
                                st.session_state.setdefault("prep_scores", {})[str(i)] = feedback
                                st.rerun()

                # Show score if available
                score_text = st.session_state.get("prep_scores", {}).get(str(i))
                if score_text:
                    lines = score_text.splitlines()
                    score_line = next((ln for ln in lines if ln.startswith("Score:")), "")
                    color = "#10b981" if "8" in score_line or "9" in score_line or "10" in score_line else (
                        "#f59e0b" if "6" in score_line or "7" in score_line else "#ef4444"
                    )
                    st.markdown(
                        f"<div style='background:#f9fafb;border-left:4px solid {color};"
                        f"padding:12px;border-radius:4px;margin-top:8px'>{score_text}</div>",
                        unsafe_allow_html=True,
                    )

        # Session summary
        scores = st.session_state.get("prep_scores", {})
        if len(scores) == len(questions):
            st.balloons()
            st.success(f"🎉 Session complete! Answered all {len(questions)} questions.")
