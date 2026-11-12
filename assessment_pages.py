"""Pupil-facing assessment pages: start → Part A (fluency) → Part B
(understanding) → results.

Kept out of app.py like teacher_tools.py; app.py routes the `assess_*`
stages here and passes in the helpers it already has.
"""
from __future__ import annotations

import re
import time

import streamlit as st

from ninja import assessment as asmt
from ninja.understanding import concept_items
from ninja.worksheets import skill_name


def _reset(skills: list[str], gen_sequence, lang: str):
    fluency, concept = [], []
    for sid in skills:
        fn = asmt.ALL_SKILLS[sid]["fn"]
        fluency += [(sid, q) for q in gen_sequence(fn, asmt.n_fluency(sid), lang)]
        concept += [(sid, it) for it in concept_items(sid, asmt.CONCEPT_QUESTIONS)]
    st.session_state.as_skills = skills
    st.session_state.as_fluency = fluency
    st.session_state.as_concept = concept
    st.session_state.as_results = {sid: asmt.SkillResult(sid) for sid in skills}
    st.session_state.as_i = 0
    st.session_state.as_shown_at = time.time()


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


def render_start(banner, go, gen_sequence):
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
    pupil = st.text_input("Your name or initials (optional — only goes on your report, it isn't saved)",
                          value=st.session_state.get("as_pupil", ""), key="as_pupil_in")
    st.markdown(
        "**Part A — Quick questions.** No pictures, no help. Answer as quickly *and* carefully as you can. "
        "You won't see if you're right until the end.\n\n"
        "**Part B — Thinking questions.** Spot mistakes, use facts you know and explain your thinking. "
        "Take your time on these.")
    if st.button("Start Part A ▶", type="primary", use_container_width=True, disabled=not skills, key="as_go_a"):
        st.session_state.as_pupil = pupil
        _reset(skills, gen_sequence, st.session_state.lang)
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
        st.session_state.as_results[sid].fluency.append(asmt.Response(
            sid, q.prompt, q.answer_display, given, q.checker(given),
            time.time() - st.session_state.as_shown_at))
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
        given = given or ""
        ok = it.checker(given)
        st.session_state.as_results[sid].concept.append(asmt.Response(
            sid, it.prompt, it.answer_display, given, ok, time.time() - st.session_state.as_shown_at,
            kind=it.kind, note="" if ok else it.notes.get(given, "")))
        st.session_state.as_i += 1
        st.session_state.as_shown_at = time.time()
        st.rerun()


def render_results(banner, go):
    banner()
    results = [st.session_state.as_results[s] for s in st.session_state.as_skills]
    pupil = st.session_state.get("as_pupil", "")
    st.subheader("🎉 Assessment complete" + (f" — {pupil}" if pupil.strip() else ""))
    for r in results:
        head, level, step = r.profile()
        label, colour = asmt.level_label(level)
        st.markdown(
            f"<div style='border-left:8px solid {colour};background:#fafafa;padding:10px 14px;margin:8px 0;"
            f"border-radius:6px'><b>{r.skill_id} — {r.name}</b><br>"
            f"Quick questions: <b>{sum(x.correct for x in r.fluency)}/{len(r.fluency)}</b> "
            f"(typical time {r.median_seconds:.1f}s) · Thinking questions: <b>{r.concept_score}/{len(r.concept)}</b>"
            f"<br>{head} · <i>Tracker {level}: {label}</i></div>", unsafe_allow_html=True)

    report = asmt.build_report(results, pupil, st.session_state.lang)
    slug = re.sub(r"[^A-Za-z0-9]+", "-", pupil).strip("-") or "pupil"
    st.download_button("⬇️ Download the report for your teacher", report,
                       file_name=f"Assessment-{slug}-{time.strftime('%Y-%m-%d')}.html", mime="text/html",
                       use_container_width=True, type="primary")
    with st.expander("For your teacher — question by question"):
        for r in results:
            st.markdown(f"**{r.skill_id} — {r.name}** · fluency: {r.fluency_band} · "
                        f"target {asmt.target_seconds(r.skill_id):g}s")
            for x in r.fluency + r.concept:
                mark = "✅" if x.correct else "❌"
                note = f" — _{x.note}_" if x.note else ""
                st.markdown(f"{mark} {x.kind or 'Fluency'}: {x.prompt} → **{x.given or '(blank)'}** "
                            f"(answer {x.answer}, {x.seconds:.1f}s){note}", unsafe_allow_html=True)
    if st.button("🏠 Home", use_container_width=True, key="as_home"):
        go("landing")
        st.rerun()
