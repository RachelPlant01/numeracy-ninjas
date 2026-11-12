"""Teacher tools page: printable worksheet generator and skill trackers.

Kept out of app.py so the pupil-facing quiz code stays as it was; app.py
just adds a "Teacher tools" button and calls `render_teacher_tools()`.
"""
from __future__ import annotations

import datetime as _dt
import re

import streamlit as st
import streamlit.components.v1 as components

import assessment_pages as ap
from ninja import assessment as asmt
from ninja import trackers
from ninja.curriculum import EO_DRAFT, LEVELS, eo_label
from ninja.generators import KEY_SKILLS, MENTAL_STRATEGIES
from ninja.scaffold_types import ALL_TYPES
from ninja.worksheets import available_types, build_worksheets, skill_name

ALL_IDS = list(MENTAL_STRATEGIES) + list(KEY_SKILLS)


def _label(sid: str) -> str:
    return f"{sid} — {skill_name(sid)}"


def _slug(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "-", text).strip("-")[:60] or "file"


def _skill_picker(key: str) -> list[str]:
    c1, c2 = st.columns(2)
    with c1:
        ms = st.multiselect("Mental strategies", list(MENTAL_STRATEGIES), format_func=_label, key=f"{key}_ms")
    with c2:
        ks = st.multiselect("Key skills", list(KEY_SKILLS), format_func=_label, key=f"{key}_ks")
    return ms + ks


# ---------------------------------------------------------------- worksheets
def _worksheets_tab():
    st.write("Pick the skills, the scaffolds and how many sheets you want, then download "
             "the file, open it and print it (or save it as a PDF).")
    skills = _skill_picker("ws")
    if not skills:
        st.info("Choose at least one skill to start.")
        return

    st.markdown("##### Scaffolds")
    mode_label = st.radio(
        "Show scaffolds",
        ["On every question", "On the first half only (fade out)", "No scaffolds"],
        horizontal=True, key="ws_mode",
    )
    scaffold_mode = {"On every question": "all", "On the first half only (fade out)": "first_half",
                     "No scaffolds": "none"}[mode_label]

    wanted = None
    if scaffold_mode != "none":
        choice = st.radio("Which scaffolds?", ["Random mix", "Choose types"], horizontal=True, key="ws_pick")
        if choice == "Choose types":
            # Only offer types at least one chosen skill can actually draw.
            offered = {t: [s for s in skills if t in available_types(s)] for t in ALL_TYPES}
            offered = {t: ss for t, ss in offered.items() if ss}
            cols = st.columns(3)
            picked = set()
            for i, (t, ss) in enumerate(offered.items()):
                with cols[i % 3]:
                    if st.checkbox(t, key=f"ws_type_{t}", help="Used by: " + ", ".join(ss)):
                        picked.add(t)
            if not picked:
                st.warning("Tick at least one scaffold type (or choose Random mix).")
                return
            wanted = picked
            missing = [s for s in skills if not (picked & set(available_types(s)))]
            if missing:
                st.caption("⚠️ None of the ticked types exist for " + ", ".join(missing)
                           + " — those questions will use a random scaffold instead.")

    st.markdown("##### Sheets")
    c1, c2, c3 = st.columns(3)
    with c1:
        n_sheets = st.number_input("Number of sheets", 1, 30, 1, key="ws_nsheets",
                                   help="Each sheet gets fresh questions.")
    with c2:
        n_q = st.number_input("Questions per sheet", 1, 40, 10, key="ws_nq")
    with c3:
        layout = st.radio("Layout", ["Large", "Compact"], key="ws_layout",
                          help="Compact puts two scaffolded questions per row (smaller pictures).")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        bw = st.checkbox("Black and white", key="ws_bw")
    with c2:
        answers = st.checkbox("Answer pages", value=True, key="ws_ans")
    with c3:
        mix = st.checkbox("Mix the skills up", value=len(skills) > 1, key="ws_mix",
                          help="Off: questions are grouped by skill in the order chosen.")
    with c4:
        lang = st.selectbox("Language", ["en", "gd"], key="ws_lang",
                            format_func=lambda x: "English" if x == "en" else "Gàidhlig")

    default_title = skill_name(skills[0]) if len(skills) == 1 else "Numeracy practice"
    title = st.text_input("Sheet title", value=default_title, key="ws_title")

    if st.button("Make worksheets ▶", type="primary", use_container_width=True):
        html, sheets = build_worksheets(
            skills, int(n_sheets), int(n_q), wanted, scaffold_mode, mix, bw, answers, title, lang,
            layout.lower(),
        )
        st.session_state.ws_html = html
        st.session_state.ws_fname = f"{_slug(title)}-{_dt.date.today():%Y-%m-%d}.html"
        unmatched = sum(1 for sh in sheets for q in sh if q.show_scaffold and not q.type_matched)
        st.session_state.ws_note = (f"{unmatched} question(s) used a different scaffold type — see the warning above."
                                    if unmatched else "")

    if st.session_state.get("ws_html"):
        st.success("Ready. Download it, open it, and press **Print / Save as PDF** at the top.")
        if st.session_state.get("ws_note"):
            st.caption(st.session_state.ws_note)
        st.download_button("⬇️ Download worksheets", st.session_state.ws_html,
                           file_name=st.session_state.ws_fname, mime="text/html",
                           use_container_width=True)
        with st.expander("Preview", expanded=True):
            components.html(st.session_state.ws_html, height=900, scrolling=True)


# ------------------------------------------------------------------ trackers
def _trackers_tab():
    st.write("Four levels for each skill:")
    st.markdown(" ".join(
        f'<span style="background:{c};padding:2px 8px;border-radius:6px;margin-right:6px;'
        f'display:inline-block;margin-bottom:4px">{code} · {lab}</span>' for code, lab, c in LEVELS),
        unsafe_allow_html=True)
    if EO_DRAFT:
        st.caption("Es and Os links are a first draft — check them before relying on them.")
    st.caption("No pupil names are entered here or stored by the app. Names go in the blank cells "
               "once the tracker is in your shared OneDrive (or on paper).")

    which = st.radio("Skills on the tracker", ["All skills", "Choose skills"], horizontal=True, key="tr_which")
    skills = ALL_IDS if which == "All skills" else _skill_picker("tr")
    if not skills:
        st.info("Choose at least one skill.")
        return

    st.markdown("##### Excel tracker (for the shared OneDrive)")
    c1, c2 = st.columns([2, 1])
    with c1:
        classes_txt = st.text_area("Class names, one per line (one sheet each)", "S1A\nS1B", key="tr_classes",
                                   height=100)
    with c2:
        n_pupils = st.number_input("Pupil columns per class", 5, 40, 25, key="tr_np")
    classes = [c.strip() for c in classes_txt.splitlines() if c.strip()] or ["Class 1"]
    st.download_button(
        "⬇️ Download Excel tracker",
        trackers.build_excel(classes, skills, int(n_pupils)),
        file_name="Numeracy-skills-tracker.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )

    st.markdown("##### Printable trackers")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Class grid** (A4 landscape)")
        cname = st.text_input("Class", "S1A", key="tr_cname")
        n_cols = st.number_input("Pupil columns", 5, 30, 20, key="tr_ncols")
        st.download_button("⬇️ Download class grid", trackers.printable_class_grid(cname, skills, int(n_cols)),
                           file_name=f"Tracker-{_slug(cname)}.html", mime="text/html",
                           use_container_width=True)
    with c2:
        st.markdown("**Pupil record** (A4 portrait, one per pupil)")
        copies = st.number_input("Copies", 1, 40, 1, key="tr_copies")
        st.download_button("⬇️ Download pupil record", trackers.printable_pupil_record(skills, int(copies)),
                           file_name="Pupil-skills-record.html", mime="text/html",
                           use_container_width=True)

    with st.expander("Which Es and Os is each skill linked to?"):
        st.table({"Skill": [_label(s) for s in skills], "Es and Os": [eo_label(s) for s in skills]})


# --------------------------------------------------------------- assessments
def _assessments_tab():
    st.write("Each assessment checks two things for every skill you choose:")
    st.markdown(
        f"- **Fluency (Part A)** — {asmt.FLUENCY_QUESTIONS['MS']} questions per mental strategy and "
        f"{asmt.FLUENCY_QUESTIONS['KS']} per key skill, with no scaffold and no feedback, every answer timed. "
        f"*Fluent* = at least {int(asmt.ACCURACY_BAR * 100)}% correct **and** a median time within the target.\n"
        f"- **Understanding (Part B)** — {asmt.CONCEPT_QUESTIONS} thinking questions per skill: spot the mistake "
        "(built on common misconceptions), use what you know (derived facts, inverses, patterns), "
        f"reasoning, estimating and representing. *Understands* = {asmt.UNDERSTANDING_BAR} or more correct.\n"
        "- Each skill then gets a profile and a suggested tracker level (1–4).")
    st.table({
        "": ["Understands", "Not yet"],
        "Fluent": ["4 · Secure", "2 · Can do it, understanding shaky"],
        "Accurate, not yet quick": ["3 · Building speed", "2 · Can do it, understanding shaky"],
        "Not yet accurate": ["2 · Understands, needs practice", "1 · Needs teaching"],
    })

    skills = _skill_picker("as")
    if not skills:
        st.info(f"Choose the skills to assess (up to {asmt.MAX_SKILLS}).")
        return
    if len(skills) > asmt.MAX_SKILLS:
        st.warning(f"Only the first {asmt.MAX_SKILLS} skills will be used — split the rest into a second assessment.")
        skills = skills[:asmt.MAX_SKILLS]
    code = " ".join(skills)
    n_q = sum(asmt.n_fluency(s) + asmt.CONCEPT_QUESTIONS for s in skills)
    st.markdown(f"##### Assessment code: `{code}`")
    st.caption(f"{n_q} questions — roughly {max(5, round(n_q * 0.5))}–{round(n_q * 1.0) + 5} minutes.")
    base = (st.context.url or "").split("?")[0]
    if base:
        st.markdown("Share this link (e.g. on Teams) — it opens the assessment straight away:")
        st.code(f"{base}?assess={','.join(skills)}", language=None)
    st.write("Or pupils press **📝 Take an assessment** on the home page and type the code. Pupils don't see "
             "their scores: they finish on a **results code and QR code**. Unlock the report there with your "
             "PIN, scan the QR code with your own device, or paste codes into **🔓 Open results**. "
             "Nothing is stored by the app — the code is the result.")
    with st.expander("Fluency target times for these skills"):
        st.table({"Skill": [_label(s) for s in skills],
                  "Target median time": [f"{asmt.target_seconds(s):g} s" for s in skills]})
        st.caption("Targets are starting points and include reading and typing time. "
                   "Change them in ninja/assessment.py (TARGET_SECONDS).")


# -------------------------------------------------------------- open results
def _open_results_tab():
    if ap.using_default_secrets():
        st.warning("This app is still using the built-in PIN (1234) and scrambling key. Set your own "
                   "`teacher_pin` and `results_key` in the app's secrets before using it with a class.")
    if not ap.pin_gate("tools"):
        return
    codes_txt = st.text_area("Paste one or more results codes — one per line", key="rc_codes", height=140)
    codes = [c for c in codes_txt.splitlines() if c.strip()]
    if not codes:
        st.info("Pupils' codes are on their screen when they finish (and in the QR code link).")
        return
    opened = []
    for n, code in enumerate(codes, 1):
        try:
            results, pupil, lang = ap.open_code(code)
            opened.append((pupil or f"Pupil {n}", results, lang))
        except ValueError as e:
            st.error(f"Line {n}: {e}")
    if len(opened) > 1:
        st.markdown("##### Class summary — suggested tracker levels")
        skills = list(dict.fromkeys(r.skill_id for _, rs, _ in opened for r in rs))
        table = {"Pupil": [p for p, _, _ in opened]}
        for sid in skills:
            table[sid] = [next((f"{r.profile()[1]} · {r.concept_score}/{len(r.concept)} understanding"
                                for r in rs if r.skill_id == sid), "") for _, rs, _ in opened]
        st.table(table)
    for n, (pupil, results, lang) in enumerate(opened):
        with st.expander(pupil, expanded=len(opened) == 1):
            ap.render_report(results, pupil, lang, key=f"tools_{n}")


def render_teacher_tools(banner, go):
    banner()
    if st.button("← Back"):
        go("landing")
        st.rerun()
    st.subheader("🧑‍🏫 Teacher tools")
    tab_ws, tab_tr, tab_as, tab_rc = st.tabs(["🖨️ Worksheets", "📊 Trackers", "📝 Assessments", "🔓 Open results"])
    with tab_ws:
        _worksheets_tab()
    with tab_tr:
        _trackers_tab()
    with tab_as:
        _assessments_tab()
    with tab_rc:
        _open_results_tab()
