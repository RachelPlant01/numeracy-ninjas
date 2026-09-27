"""BGE Numeracy — scaffolded practice app.

Landing page → choose Key Skills or Mental Strategies → choose a skill →
set scaffold-fade options → answer questions one at a time, timed.
"""
from __future__ import annotations

import time

import streamlit as st
import streamlit.components.v1 as components

from ninja.generators import KEY_SKILLS, MENTAL_STRATEGIES

CATEGORIES = {
    "key_skills": {
        "skills": KEY_SKILLS,
        "n_questions": 5,
    },
    "mental_strategies": {
        "skills": MENTAL_STRATEGIES,
        "n_questions": 10,
    },
}

# Every piece of static interface text, in both languages. Question prompts
# themselves are translated inside ninja/generators.py (each generator takes
# a `lang` argument); this dict only covers the app's own chrome.
UI = {
    "en": {
        "app_name": "Matamataig Mìorbhaileach",
        "subtitle": "Pick a practice zone to get started.",
        "key_skills_title": "🗝️ Key Skills",
        "key_skills_desc": "Core written arithmetic and number skills.",
        "skills_caption": "{n} skills · {q} questions per session",
        "choose_key_skills": "Choose Key Skills",
        "mental_strategies_title": "⚡ Mental Strategies",
        "mental_strategies_desc": "Quick mental-maths strategies and number sense.",
        "choose_mental_strategies": "Choose Mental Strategies",
        "back": "← Back",
        "choose_skill": "Choose the skill you're working on:",
        "session_info": "You'll do **{n} questions** and we'll time how long it takes.",
        "show_scaffold": "Show the visual scaffold",
        "show_scaffold_help": "Turn off to remove the scaffold picture entirely, for pupils working from memory.",
        "fade_scaffold": "Fade the scaffold after a while",
        "fade_scaffold_help": "The visual scaffold will automatically hide itself after the chosen time, so pupils move towards working independently.",
        "fade_seconds_label": "Fade scaffold after (seconds)",
        "fade_stay_visible": "Scaffold will stay visible for every question.",
        "start": "Start ▶",
        "home": "🏠 Home",
        "question_of": "Question {i} of {n}",
        "scaffold_hidden": "💭 Scaffold hidden — try it from memory now.",
        "scaffold_hidden_inline": "Scaffold hidden — try it from memory now.",
        "answer_placeholder": "Type your answer, then press Enter…",
        "submit": "Submit ▶",
        "correct": "Correct! ✅",
        "not_quite": "Not quite. You wrote **{user}** — the answer was **{ans}**.",
        "blank": "(blank)",
        "next_question": "Next question ▶",
        "session_complete": "## Session complete — {title}",
        "score": "Score",
        "time_taken": "Time taken",
        "practice_again": "🔁 Practice again",
        "choose_another_skill": "📚 Choose another skill",
    },
    "gd": {
        "app_name": "Matamataig Mìorbhaileach",
        "subtitle": "Tagh raon cleachdaidh gus tòiseachadh.",
        "key_skills_title": "🗝️ Prìomh Sgilean",
        "key_skills_desc": "Àireamhachd sgrìobhte bunasach agus sgilean àireimh.",
        "skills_caption": "{n} sgilean · {q} ceistean gach seisean",
        "choose_key_skills": "Tagh Prìomh Sgilean",
        "mental_strategies_title": "⚡ Ro-innleachdan Inntinn",
        "mental_strategies_desc": "Ro-innleachdan luath airson àireamhachd na h-inntinn.",
        "choose_mental_strategies": "Tagh Ro-innleachdan Inntinn",
        "back": "← Air ais",
        "choose_skill": "Tagh an sgil air a bheil thu ag obair:",
        "session_info": "Nì thu **{n} ceistean** agus cuiridh sinn ùine ris.",
        "show_scaffold": "Seall an dealbh taice",
        "show_scaffold_help": "Cuir seo dheth gus an dealbh taice a thoirt air falbh gu tur, airson sgoilearan ag obair às an cuimhne.",
        "fade_scaffold": "Falbh an dealbh taice às dèidh greis",
        "fade_scaffold_help": "Falbhaidh an dealbh taice às an t-sealladh gu fèin-obrachail às dèidh na h-ùine a thagh thu, gus sgoilearan a ghluasad a dh'ionnsaigh obair neo-eisimeileach.",
        "fade_seconds_label": "Falbh an dealbh taice às dèidh (diogan)",
        "fade_stay_visible": "Fanaidh an dealbh taice ri fhaicinn airson gach ceist.",
        "start": "Tòisich ▶",
        "home": "🏠 Dhachaigh",
        "question_of": "Ceist {i} de {n}",
        "scaffold_hidden": "💭 An dealbh taice falaichte — feuch bhon chuimhne a-nis.",
        "scaffold_hidden_inline": "An dealbh taice falaichte — feuch bhon chuimhne a-nis.",
        "answer_placeholder": "Sgrìobh do fhreagairt, an uairsin brùth Enter…",
        "submit": "Cuir a-steach ▶",
        "correct": "Ceart! ✅",
        "not_quite": "Chan eil sin buileach ceart. Sgrìobh thu **{user}** — b' e **{ans}** am freagairt.",
        "blank": "(bàn)",
        "next_question": "An ath cheist ▶",
        "session_complete": "## Seisean deiseil — {title}",
        "score": "Sgòr",
        "time_taken": "Ùine a ghabh e",
        "practice_again": "🔁 Cleachd a-rithist",
        "choose_another_skill": "📚 Tagh sgil eile",
    },
}


def tr(key: str, **kwargs) -> str:
    text = UI[st.session_state.lang][key]
    return text.format(**kwargs) if kwargs else text


def skill_title(skill_entry: dict) -> str:
    return skill_entry["gd" if st.session_state.lang == "gd" else "en"]


st.set_page_config(page_title="Matamataig Mìorbhaileach", page_icon="🧮", layout="centered")

CSS = """
<style>
.block-container {
    padding-top: 3.2rem;
    padding-bottom: 1rem;
}
.app-banner {
    background: #1c1c1c;
    color: #f4d35e;
    padding: 18px 24px;
    border-radius: 12px;
    text-align: center;
    font-size: 1.9rem;
    font-weight: 800;
    letter-spacing: 2px;
    margin-bottom: 6px;
}
.app-sub {
    text-align:center;
    color:#666;
    margin-bottom:24px;
}
.quiz-header {
    display:flex;
    justify-content:space-between;
    align-items:baseline;
    color:#555;
    font-size:0.95rem;
    margin-bottom:2px;
}
.big-question {
    font-size: 3.2rem;
    font-weight: 800;
    text-align: center;
    margin: 10px 0 10px 0;
    color: #1c1c1c !important;
    line-height: 1.2;
}
div.stButton > button {
    border-radius: 10px;
    font-weight: 600;
}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


def banner():
    st.markdown(f'<div class="app-banner">🧮 {UI["en"]["app_name"].upper()}</div>', unsafe_allow_html=True)


def language_toggle():
    col_en, col_gd = st.columns(2)
    with col_en:
        if st.button("English", use_container_width=True,
                      type="primary" if st.session_state.lang == "en" else "secondary"):
            st.session_state.lang = "en"
            st.rerun()
    with col_gd:
        if st.button("Gàidhlig", use_container_width=True,
                      type="primary" if st.session_state.lang == "gd" else "secondary"):
            st.session_state.lang = "gd"
            st.rerun()


# ---------------------------------------------------------------- state init
def init_state():
    defaults = dict(
        stage="landing",
        lang="en",
        category=None,
        skill_id=None,
        scaffold_enabled=True,
        fade_enabled=True,
        fade_seconds=15,
        quiz_questions=[],
        quiz_index=0,
        quiz_results=[],
        awaiting_feedback=False,
        last_correct=None,
        last_user_answer="",
        quiz_start_time=None,
        quiz_end_time=None,
        question_shown_at=None,
    )
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def go(stage: str):
    st.session_state.stage = stage


def generate_question_sequence(gen_fn, n: int, lang: str, max_attempts: int = 50) -> list:
    """Generate `n` questions, re-rolling a question if its prompt has
    already appeared earlier in this session — so every distinct question a
    skill can produce gets shown before any of them repeat. Some skills only
    have a handful of possible prompts, so once those are exhausted a
    repeat becomes unavoidable and is allowed rather than looping forever."""
    questions = []
    seen_prompts: set[str] = set()
    for _ in range(n):
        q = gen_fn(lang)
        for _ in range(max_attempts):
            if q.prompt not in seen_prompts:
                break
            q = gen_fn(lang)
        questions.append(q)
        seen_prompts.add(q.prompt)
    return questions


def fading_scaffold(scaffold_html: str, seconds_remaining: float, key: str):
    """Render the scaffold as a normal part of the page (so it's always in
    sync with the current question — an iframe's srcdoc can lag a beat
    behind a fast rerun, which previously let a stale scaffold from an
    earlier question linger on screen). A tiny zero-height component then
    reaches into the parent page to hide it after `seconds_remaining`."""
    st.markdown(
        f'<div id="scaf-{key}">{scaffold_html}</div>'
        f'<div id="faded-{key}" style="display:none;color:#888;font-style:italic;'
        f'text-align:center;padding:10px;">{tr("scaffold_hidden_inline")}</div>',
        unsafe_allow_html=True,
    )
    components.html(
        f"""
        <script>
        setTimeout(function() {{
            var doc = window.parent.document;
            var s = doc.getElementById("scaf-{key}");
            var f = doc.getElementById("faded-{key}");
            if (s) s.style.display = "none";
            if (f) f.style.display = "block";
        }}, {max(0, int(seconds_remaining * 1000))});
        </script>
        """,
        height=0,
    )


def focus_answer_input():
    """Put the cursor in the answer box automatically, so pupils can start
    typing straight away without clicking into it first. Also hints a
    numeric keypad on mobile/tablet (most answers are plain numbers) —
    it's only a hint, not a restriction, so the odd answer that needs
    letters (e.g. "Yes"/"No") or symbols is still typeable via the
    keyboard's own switch-keyboard control."""
    placeholder = tr("answer_placeholder")
    components.html(
        f"""
        <script>
        setTimeout(function() {{
            const el = window.parent.document.querySelector(
                'input[placeholder="{placeholder}"]'
            );
            if (el) {{
                el.setAttribute('inputmode', 'decimal');
                el.focus();
            }}
        }}, 80);
        </script>
        """,
        height=0,
    )


def enable_enter_to_advance():
    """Let pupils press Enter to move to the next question instead of
    having to click the button — attaches a document-level listener on the
    parent page and swaps out any listener from a previous render."""
    next_label = tr("next_question")
    components.html(
        f"""
        <script>
        if (window.parent.__bgeNextHandler) {{
            window.parent.document.removeEventListener('keydown', window.parent.__bgeNextHandler);
        }}
        window.parent.__bgeNextHandler = function(e) {{
            if (e.key !== 'Enter') return;
            const btns = window.parent.document.querySelectorAll('button');
            for (const b of btns) {{
                if (b.innerText.includes('{next_label}')) {{
                    b.click();
                    break;
                }}
            }}
        }};
        window.parent.document.addEventListener('keydown', window.parent.__bgeNextHandler);
        </script>
        """,
        height=0,
    )


# -------------------------------------------------------------------- pages
def render_landing():
    banner()
    language_toggle()
    st.markdown(f'<div class="app-sub">{tr("subtitle")}</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"### {tr('key_skills_title')}")
        st.write(tr("key_skills_desc"))
        st.caption(tr("skills_caption", n=len(KEY_SKILLS), q=CATEGORIES["key_skills"]["n_questions"]))
        if st.button(tr("choose_key_skills"), use_container_width=True, type="primary"):
            st.session_state.category = "key_skills"
            go("skill_select")
            st.rerun()
    with col2:
        st.markdown(f"### {tr('mental_strategies_title')}")
        st.write(tr("mental_strategies_desc"))
        st.caption(tr("skills_caption", n=len(MENTAL_STRATEGIES), q=CATEGORIES["mental_strategies"]["n_questions"]))
        if st.button(tr("choose_mental_strategies"), use_container_width=True, type="primary"):
            st.session_state.category = "mental_strategies"
            go("skill_select")
            st.rerun()


def render_skill_select():
    banner()
    cat = CATEGORIES[st.session_state.category]
    cat_title = tr("key_skills_title") if st.session_state.category == "key_skills" else tr("mental_strategies_title")
    st.subheader(cat_title)
    if st.button(tr("back")):
        go("landing")
        st.rerun()
    st.write(tr("choose_skill"))
    skills = cat["skills"]
    ids = list(skills.keys())
    cols = st.columns(2)
    for i, sid in enumerate(ids):
        title = skill_title(skills[sid])
        with cols[i % 2]:
            if st.button(title, key=f"skill_{sid}", use_container_width=True):
                st.session_state.skill_id = sid
                go("settings")
                st.rerun()


def render_settings():
    banner()
    cat = CATEGORIES[st.session_state.category]
    title = skill_title(cat["skills"][st.session_state.skill_id])
    st.subheader(title)
    if st.button(tr("back")):
        go("skill_select")
        st.rerun()

    st.write(tr("session_info", n=cat["n_questions"]))

    st.session_state.scaffold_enabled = st.checkbox(
        tr("show_scaffold"), value=st.session_state.scaffold_enabled,
        help=tr("show_scaffold_help"),
    )
    if st.session_state.scaffold_enabled:
        st.session_state.fade_enabled = st.checkbox(
            tr("fade_scaffold"), value=st.session_state.fade_enabled,
            help=tr("fade_scaffold_help"),
        )
        if st.session_state.fade_enabled:
            st.session_state.fade_seconds = st.slider(
                tr("fade_seconds_label"), min_value=5, max_value=60,
                value=st.session_state.fade_seconds, step=5,
            )
        else:
            st.caption(tr("fade_stay_visible"))

    if st.button(tr("start"), type="primary", use_container_width=True):
        _fn_gen = cat["skills"][st.session_state.skill_id]["fn"]
        st.session_state.quiz_questions = generate_question_sequence(_fn_gen, cat["n_questions"], st.session_state.lang)
        st.session_state.quiz_index = 0
        st.session_state.quiz_results = []
        st.session_state.awaiting_feedback = False
        now = time.time()
        st.session_state.quiz_start_time = now
        st.session_state.quiz_end_time = None
        st.session_state.question_shown_at = now
        go("quiz")
        st.rerun()


def render_quiz():
    cat = CATEGORIES[st.session_state.category]
    n = cat["n_questions"]
    idx = st.session_state.quiz_index

    if idx >= n:
        if st.session_state.quiz_end_time is None:
            st.session_state.quiz_end_time = time.time()
        go("results")
        st.rerun()
        return

    title = skill_title(cat["skills"][st.session_state.skill_id])
    col_home, col_head = st.columns([1, 5])
    with col_home:
        if st.button(tr("home"), key=f"home_{idx}"):
            go("landing")
            st.rerun()
    with col_head:
        st.markdown(
            f'<div class="quiz-header"><span>{title}</span><span>{tr("question_of", i=idx + 1, n=n)}</span></div>',
            unsafe_allow_html=True,
        )
    st.progress(idx / n)

    q = st.session_state.quiz_questions[idx]
    st.markdown(f'<div class="big-question">{q.prompt}</div>', unsafe_allow_html=True)

    if st.session_state.scaffold_enabled:
        elapsed_shown = time.time() - st.session_state.question_shown_at
        if st.session_state.fade_enabled:
            remaining = st.session_state.fade_seconds - elapsed_shown
            if remaining > 0:
                fading_scaffold(q.scaffold_html, remaining, key=f"q{idx}")
            else:
                st.caption(tr("scaffold_hidden"))
        else:
            st.markdown(q.scaffold_html, unsafe_allow_html=True)

    if not st.session_state.awaiting_feedback:
        with st.form(key=f"answer_form_{idx}", clear_on_submit=False, enter_to_submit=True):
            user_answer = st.text_input(
                "Your answer", key=f"input_{idx}",
                placeholder=tr("answer_placeholder"), label_visibility="collapsed",
            )
            submitted = st.form_submit_button(tr("submit"), type="primary", use_container_width=True)
        focus_answer_input()
        if submitted:
            correct = q.checker(user_answer)
            st.session_state.quiz_results.append(correct)
            st.session_state.awaiting_feedback = True
            st.session_state.last_correct = correct
            st.session_state.last_user_answer = user_answer
            st.rerun()
    else:
        if st.session_state.last_correct:
            st.success(tr("correct"))
        else:
            st.error(tr("not_quite", user=st.session_state.last_user_answer or tr("blank"), ans=q.answer_display))
        if st.button(tr("next_question"), type="primary", use_container_width=True):
            st.session_state.quiz_index += 1
            st.session_state.awaiting_feedback = False
            st.session_state.question_shown_at = time.time()
            st.rerun()
        enable_enter_to_advance()


def render_results():
    banner()
    cat = CATEGORIES[st.session_state.category]
    title = skill_title(cat["skills"][st.session_state.skill_id])
    n = cat["n_questions"]
    correct = sum(1 for r in st.session_state.quiz_results if r)
    elapsed = st.session_state.quiz_end_time - st.session_state.quiz_start_time
    mins, secs = divmod(elapsed, 60)

    st.markdown(tr("session_complete", title=title))
    c1, c2 = st.columns(2)
    c1.metric(tr("score"), f"{correct} / {n}")
    c2.metric(tr("time_taken"), f"{int(mins)}m {secs:04.1f}s")

    st.divider()
    b1, b2, b3 = st.columns(3)
    with b1:
        if st.button(tr("practice_again"), use_container_width=True):
            go("settings")
            st.rerun()
    with b2:
        if st.button(tr("choose_another_skill"), use_container_width=True):
            go("skill_select")
            st.rerun()
    with b3:
        if st.button(tr("home"), use_container_width=True):
            go("landing")
            st.rerun()


# ------------------------------------------------------------------- router
init_state()
STAGE_RENDERERS = {
    "landing": render_landing,
    "skill_select": render_skill_select,
    "settings": render_settings,
    "quiz": render_quiz,
    "results": render_results,
}
STAGE_RENDERERS[st.session_state.stage]()
