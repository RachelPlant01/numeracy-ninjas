"""Pupil-facing assessment pages: start → Part A (fluency) → Part B
(understanding) → "show your teacher" screen.

Pupils never see their scores. They finish on a results code + QR code; the
report opens only with the teacher PIN — on the pupil's Chromebook, or on
the teacher's own device by scanning the QR / pasting the code.

Kept out of app.py like teacher_tools.py; app.py routes the `assess_*`
stages here and passes in the helpers it already has.
"""
from __future__ import annotations

import hmac
import re
import secrets
import time

import segno
import streamlit as st

from ninja import assessment as asmt
from ninja import results_code
from ninja.worksheets import skill_name

# Set your own in .streamlit/secrets.toml (or the host's secrets settings):
#   teacher_pin = "…"   results_key = "…long random text…"
_DEFAULT_PIN = "1234"
_DEFAULT_KEY = "numeracy-ninjas-default-key"


def _secret(name: str, default: str) -> str:
    try:
        return str(st.secrets.get(name, default))
    except Exception:  # no secrets file at all
        return default


def using_default_secrets() -> bool:
    return _secret("teacher_pin", _DEFAULT_PIN) == _DEFAULT_PIN or \
        _secret("results_key", _DEFAULT_KEY) == _DEFAULT_KEY


def _reset(skills: list[str], lang: str):
    seed = secrets.randbits(32)
    fluency, concept, fp = asmt.build_items(skills, lang, seed)
    st.session_state.as_skills = skills
    st.session_state.as_seed = seed
    st.session_state.as_fp = fp
    st.session_state.as_fluency = fluency
    st.session_state.as_concept = concept
    st.session_state.as_f_given = []
    st.session_state.as_c_given = []
    st.session_state.as_i = 0
    st.session_state.as_shown_at = time.time()
    st.session_state.teacher_unlocked = False  # a fresh pupil must not inherit the last unlock


def _elapsed() -> float:
    return round(time.time() - st.session_state.as_shown_at, 1)


def _header(go, part: str, i: int, n: int, sid: str):
    col_home, col_head = st.columns([1, 5])
    with col_home:
        if st.button("✖ Quit", key=f"as_quit_{part}_{i}"):
            go("landing")
            st.rerun()
    with col_head:
        st.markdown(f'<div class="quiz-header"><span>{part} · {skill_name(sid, st.session_state.lang)}</span>'
                    f'<span>Question {i + 1} of {n}</span></div>', unsafe_allow_html=True)
    st.progress(i / n)


def render_start(banner, go):
    banner()
    if st.button("← Back", key="as_back"):
        go("landing")
        st.rerun()
    st.subheader("📝 Assessment")
    st.write("Your teacher will give you an **assessment code** — the skills to check, like `MS5 KS7 KS17`.")
    code = st.text_input("Assessment code", value=st.session_state.get("as_code", ""), key="as_code_in")
    skills = asmt.parse_code(code)
    if skills:
        st.caption("Skills: " + " · ".join(f"{s} {skill_name(s, st.session_state.lang)}" for s in skills))
    elif code.strip():
        st.warning("That code doesn't match any skills — check it with your teacher.")
    pupil = st.text_input("Your initials (optional — they only go on your results code)",
                          value=st.session_state.get("as_pupil", ""), key="as_pupil_in", max_chars=20)
    st.markdown(
        "**Part A — Quick questions.** No pictures, no help. Answer as quickly *and* carefully as you can.\n\n"
        "**Part B — Thinking questions.** Spot mistakes, use facts you know and explain your thinking. "
        "Take your time on these.\n\n"
        "At the end you'll go through your results with your teacher.")
    st.warning("⚠️ Don't refresh the page or close this tab until you've finished — your answers would be lost.")
    if st.button("Start Part A ▶", type="primary", use_container_width=True, disabled=not skills, key="as_go_a"):
        st.session_state.as_pupil = pupil.strip()
        _reset(skills, st.session_state.lang)
        go("assess_fluency")
        st.rerun()


def render_fluency(go, focus_answer_input, placeholder: str):
    items = st.session_state.as_fluency
    i = st.session_state.as_i
    if i >= len(items):
        go("assess_break")
        st.rerun()
        return
    sid, q = items[i]
    _header(go, "Part A", i, len(items), sid)
    st.markdown(f'<div class="big-question">{q.prompt}</div>', unsafe_allow_html=True)
    with st.form(key=f"as_f_{i}", enter_to_submit=True):
        given = st.text_input("Your answer", key=f"as_f_in_{i}", placeholder=placeholder,
                              label_visibility="collapsed")
        submitted = st.form_submit_button("Next ▶", type="primary", use_container_width=True)
    focus_answer_input()
    if submitted:
        st.session_state.as_f_given.append((given, _elapsed()))
        st.session_state.as_i += 1
        st.session_state.as_shown_at = time.time()
        st.rerun()


def render_break(banner, go):
    banner()
    st.subheader("✅ Part A done!")
    st.write("Now for **Part B — thinking questions**. These check that you understand *why*, not just how. "
             "Some ask you to spot a mistake, some ask you to use a fact you're given. Take your time.")
    if st.button("Start Part B ▶", type="primary", use_container_width=True, key="as_go_b"):
        st.session_state.as_i = 0
        st.session_state.as_shown_at = time.time()
        go("assess_concept")
        st.rerun()


def render_concept(go, focus_answer_input, placeholder: str):
    items = st.session_state.as_concept
    i = st.session_state.as_i
    if i >= len(items):
        go("assess_results")
        st.rerun()
        return
    sid, it = items[i]
    _header(go, "Part B", i, len(items), sid)
    st.caption(it.kind)
    st.markdown(f"<div style='font-size:1.6rem;font-weight:700;margin:10px 0 16px'>{it.prompt}</div>",
                unsafe_allow_html=True)
    with st.form(key=f"as_c_{i}", enter_to_submit=True):
        if it.options:
            given = st.radio("Choose one", it.options, index=None, key=f"as_c_in_{i}")
        else:
            given = st.text_input("Your answer", key=f"as_c_in_{i}", placeholder=placeholder,
                                  label_visibility="collapsed")
        submitted = st.form_submit_button("Next ▶", type="primary", use_container_width=True)
    if not it.options:
        focus_answer_input()
    if submitted:
        if it.options and given is None:
            st.warning("Choose an answer first.")
            return
        st.session_state.as_c_given.append((given or "", _elapsed()))
        st.session_state.as_i += 1
        st.session_state.as_shown_at = time.time()
        st.rerun()


# ------------------------------------------------------------ results code
def _make_code() -> str:
    """Pack this pupil's assessment into a results code. Multiple-choice
    answers travel as the option's position, typed answers as text."""
    concept = st.session_state.as_concept
    c = [[it.options.index(g) if it.options and g in it.options else g, t]
         for (_, it), (g, t) in zip(concept, st.session_state.as_c_given)]
    return results_code.encode({
        "s": st.session_state.as_seed, "l": st.session_state.lang, "k": " ".join(st.session_state.as_skills),
        "p": st.session_state.get("as_pupil", ""), "h": st.session_state.as_fp,
        "f": [[g, t] for g, t in st.session_state.as_f_given], "c": c,
    }, _secret("results_key", _DEFAULT_KEY))


def open_code(code: str) -> tuple[list[asmt.SkillResult], str, str]:
    """results code -> (results, pupil initials, lang). Raises ValueError."""
    p = results_code.decode(code, _secret("results_key", _DEFAULT_KEY))
    skills = asmt.parse_code(p["k"])
    fluency, concept, _ = asmt.build_items(skills, p["l"], p["s"], expect=p["h"])
    c_given = [(it.options[g] if it.options and isinstance(g, int) and g < len(it.options) else str(g), t)
               for (_, it), (g, t) in zip(concept, p["c"])]
    return asmt.score(skills, fluency, concept, [tuple(x) for x in p["f"]], c_given), p.get("p", ""), p["l"]


def _qr_svg(text: str) -> str:
    return segno.make(text, error="l").svg_inline(scale=4, border=2)


def pin_gate(key: str) -> bool:
    """True once the teacher PIN has been entered in this browser session."""
    if st.session_state.get("teacher_unlocked"):
        return True
    with st.form(key=f"pin_{key}"):
        pin = st.text_input("Teacher PIN", type="password", key=f"pin_in_{key}")
        if st.form_submit_button("Unlock 🔓", type="primary"):
            if hmac.compare_digest(pin.strip(), _secret("teacher_pin", _DEFAULT_PIN)):
                st.session_state.teacher_unlocked = True
                st.rerun()
            st.error("That PIN isn't right.")
    return False


def render_report(results: list[asmt.SkillResult], pupil: str, lang: str, key: str):
    """The teacher's view of one pupil's results, with the downloadable report."""
    for r in results:
        head, level, step = r.profile()
        label, colour = asmt.level_label(level)
        st.markdown(
            f"<div style='border-left:8px solid {colour};background:#fafafa;padding:10px 14px;margin:8px 0;"
            f"border-radius:6px'><b>{r.skill_id} — {r.name}</b><br>"
            f"Quick questions: <b>{sum(x.correct for x in r.fluency)}/{len(r.fluency)}</b> "
            f"(typical time {r.median_seconds:.1f}s, target {asmt.target_seconds(r.skill_id):g}s) · "
            f"Thinking questions: <b>{r.concept_score}/{len(r.concept)}</b>"
            f"<br>{head} · <i>Tracker {level}: {label}</i><br><small>{step}</small></div>",
            unsafe_allow_html=True)
    with st.expander("Question by question"):
        for r in results:
            st.markdown(f"**{r.skill_id} — {r.name}** · fluency: {r.fluency_band}")
            for x in r.fluency + r.concept:
                mark = "✅" if x.correct else "❌"
                note = f" — _{x.note}_" if x.note else ""
                st.markdown(f"{mark} {x.kind or 'Fluency'}: {x.prompt} → **{x.given or '(blank)'}** "
                            f"(answer {x.answer}, {x.seconds:.1f}s){note}", unsafe_allow_html=True)
    slug = re.sub(r"[^A-Za-z0-9]+", "-", pupil).strip("-") or "pupil"
    st.download_button("⬇️ Download report", asmt.build_report(results, pupil, lang),
                       file_name=f"Assessment-{slug}-{time.strftime('%Y-%m-%d')}.html", mime="text/html",
                       use_container_width=True, key=f"dl_{key}")


def render_done(banner, go):
    """Pupil's last screen: no scores, just the code for the teacher."""
    banner()
    if "as_result_code" not in st.session_state or st.session_state.get("as_result_for") != st.session_state.as_seed:
        st.session_state.as_result_code = _make_code()
        st.session_state.as_result_for = st.session_state.as_seed
    code = st.session_state.as_result_code
    pupil = st.session_state.get("as_pupil", "")
    st.subheader("✅ All done" + (f", {pupil}" if pupil else "") + "!")
    st.markdown("### ✋ Put your hand up and show your teacher this screen.")
    base = (st.context.url or "").split("?")[0]
    link = f"{base}?results={code.replace(' ', '')}" if base else code
    c1, c2 = st.columns([1, 2])
    with c1:
        st.markdown(_qr_svg(link), unsafe_allow_html=True)
    with c2:
        st.caption("Results code — scan the QR code, or copy this:")
        st.code(code, language=None, wrap_lines=True)

    st.divider()
    st.markdown("**🔒 Teacher**")
    if pin_gate("done"):
        results, pupil, lang = open_code(code)
        render_report(results, pupil, lang, key="done")
        if st.button("🏠 Finish and go home", use_container_width=True, key="as_home"):
            st.session_state.teacher_unlocked = False
            go("landing")
            st.rerun()


def render_open_link(banner, go):
    """Opened from a scanned QR code (…?results=CODE) on the teacher's device."""
    banner()
    st.subheader("🔓 Assessment results")
    if not pin_gate("link"):
        return
    try:
        results, pupil, lang = open_code(st.session_state.get("results_link", ""))
    except ValueError as e:
        st.error(str(e))
        return
    if pupil:
        st.markdown(f"#### {pupil}")
    render_report(results, pupil, lang, key="link")
    if st.button("🏠 Home", use_container_width=True, key="link_home"):
        go("landing")
        st.rerun()
