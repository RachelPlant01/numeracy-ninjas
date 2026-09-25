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
        "label": "Key Skills",
        "description": "Core written arithmetic and number skills.",
        "skills": KEY_SKILLS,
        "n_questions": 5,
    },
    "mental_strategies": {
        "label": "Mental Strategies",
        "description": "Quick mental-maths strategies and number sense.",
        "skills": MENTAL_STRATEGIES,
        "n_questions": 10,
    },
}

st.set_page_config(page_title="BGE Numeracy", page_icon="🧮", layout="centered")

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
    st.markdown('<div class="app-banner">🧮 BGE NUMERACY</div>', unsafe_allow_html=True)


# ---------------------------------------------------------------- state init
def init_state():
    defaults = dict(
        stage="landing",
        category=None,
        skill_id=None,
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


def generate_question_sequence(gen_fn, n: int, max_attempts: int = 50) -> list:
    """Generate `n` questions, re-rolling a question if its prompt has
    already appeared earlier in this session — so every distinct question a
    skill can produce gets shown before any of them repeat. Some skills only
    have a handful of possible prompts, so once those are exhausted a
    repeat becomes unavoidable and is allowed rather than looping forever."""
    questions = []
    seen_prompts: set[str] = set()
    for _ in range(n):
        q = gen_fn()
        for _ in range(max_attempts):
            if q.prompt not in seen_prompts:
                break
            q = gen_fn()
        questions.append(q)
        seen_prompts.add(q.prompt)
    return questions


def fading_scaffold(scaffold_html: str, seconds_remaining: float, key: str):
    """Render scaffold HTML that hides itself client-side after `seconds_remaining`."""
    components.html(
        f"""
        <style>html,body{{background:#ffffff;margin:0;}}</style>
        <div id="scaf-{key}">{scaffold_html}</div>
        <div id="faded-{key}" style="display:none;color:#888;font-style:italic;
             text-align:center;padding:10px;">Scaffold hidden — try it from memory now.</div>
        <script>
        setTimeout(function() {{
            var s = document.getElementById("scaf-{key}");
            var f = document.getElementById("faded-{key}");
            if (s) s.style.display = "none";
            if (f) f.style.display = "block";
        }}, {max(0, int(seconds_remaining * 1000))});
        </script>
        """,
        height=280,
        scrolling=True,
    )


def focus_answer_input():
    """Put the cursor in the answer box automatically, so pupils can start
    typing straight away without clicking into it first."""
    components.html(
        """
        <script>
        setTimeout(function() {
            const el = window.parent.document.querySelector(
                'input[placeholder="Type your answer, then press Enter…"]'
            );
            if (el) el.focus();
        }, 80);
        </script>
        """,
        height=0,
    )


def enable_enter_to_advance():
    """Let pupils press Enter to move to the next question instead of
    having to click the button — attaches a document-level listener on the
    parent page and swaps out any listener from a previous render."""
    components.html(
        """
        <script>
        if (window.parent.__bgeNextHandler) {
            window.parent.document.removeEventListener('keydown', window.parent.__bgeNextHandler);
        }
        window.parent.__bgeNextHandler = function(e) {
            if (e.key !== 'Enter') return;
            const btns = window.parent.document.querySelectorAll('button');
            for (const b of btns) {
                if (b.innerText.includes('Next question')) {
                    b.click();
                    break;
                }
            }
        };
        window.parent.document.addEventListener('keydown', window.parent.__bgeNextHandler);
        </script>
        """,
        height=0,
    )


# -------------------------------------------------------------------- pages
def render_landing():
    banner()
    st.markdown('<div class="app-sub">Pick a practice zone to get started.</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 🗝️ Key Skills")
        st.write(CATEGORIES["key_skills"]["description"])
        st.caption(f"{len(KEY_SKILLS)} skills · 5 questions per session")
        if st.button("Choose Key Skills", use_container_width=True, type="primary"):
            st.session_state.category = "key_skills"
            go("skill_select")
            st.rerun()
    with col2:
        st.markdown("### ⚡ Mental Strategies")
        st.write(CATEGORIES["mental_strategies"]["description"])
        st.caption(f"{len(MENTAL_STRATEGIES)} skills · 10 questions per session")
        if st.button("Choose Mental Strategies", use_container_width=True, type="primary"):
            st.session_state.category = "mental_strategies"
            go("skill_select")
            st.rerun()


def render_skill_select():
    banner()
    cat = CATEGORIES[st.session_state.category]
    st.subheader(cat["label"])
    if st.button("← Back"):
        go("landing")
        st.rerun()
    st.write("Choose the skill you're working on:")
    skills = cat["skills"]
    ids = list(skills.keys())
    cols = st.columns(2)
    for i, sid in enumerate(ids):
        title, _fn = skills[sid]
        with cols[i % 2]:
            if st.button(title, key=f"skill_{sid}", use_container_width=True):
                st.session_state.skill_id = sid
                go("settings")
                st.rerun()


def render_settings():
    banner()
    cat = CATEGORIES[st.session_state.category]
    title, _fn = cat["skills"][st.session_state.skill_id]
    st.subheader(title)
    if st.button("← Back"):
        go("skill_select")
        st.rerun()

    st.write(f"You'll do **{cat['n_questions']} questions** and we'll time how long it takes.")

    st.session_state.fade_enabled = st.checkbox(
        "Fade the scaffold after a while", value=st.session_state.fade_enabled,
        help="The visual scaffold will automatically hide itself after the chosen time, so pupils move towards working independently.",
    )
    if st.session_state.fade_enabled:
        st.session_state.fade_seconds = st.slider(
            "Fade scaffold after (seconds)", min_value=5, max_value=60,
            value=st.session_state.fade_seconds, step=5,
        )
    else:
        st.caption("Scaffold will stay visible for every question.")

    if st.button("Start ▶", type="primary", use_container_width=True):
        _fn_gen = cat["skills"][st.session_state.skill_id][1]
        st.session_state.quiz_questions = generate_question_sequence(_fn_gen, cat["n_questions"])
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

    title, _fn = cat["skills"][st.session_state.skill_id]
    col_home, col_head = st.columns([1, 5])
    with col_home:
        if st.button("🏠 Home", key=f"home_{idx}"):
            go("landing")
            st.rerun()
    with col_head:
        st.markdown(
            f'<div class="quiz-header"><span>{title}</span><span>Question {idx + 1} of {n}</span></div>',
            unsafe_allow_html=True,
        )
    st.progress(idx / n)

    q = st.session_state.quiz_questions[idx]
    st.markdown(f'<div class="big-question">{q.prompt}</div>', unsafe_allow_html=True)

    elapsed_shown = time.time() - st.session_state.question_shown_at
    if st.session_state.fade_enabled:
        remaining = st.session_state.fade_seconds - elapsed_shown
        if remaining > 0:
            fading_scaffold(q.scaffold_html, remaining, key=f"q{idx}")
        else:
            st.caption("💭 Scaffold hidden — try it from memory now.")
    else:
        st.markdown(q.scaffold_html, unsafe_allow_html=True)

    if not st.session_state.awaiting_feedback:
        with st.form(key=f"answer_form_{idx}", clear_on_submit=False, enter_to_submit=True):
            user_answer = st.text_input(
                "Your answer", key=f"input_{idx}",
                placeholder="Type your answer, then press Enter…", label_visibility="collapsed",
            )
            submitted = st.form_submit_button("Submit ▶", type="primary", use_container_width=True)
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
            st.success("Correct! ✅")
        else:
            st.error(f"Not quite. You wrote **{st.session_state.last_user_answer or '(blank)'}** — the answer was **{q.answer_display}**.")
        if st.button("Next question ▶", type="primary", use_container_width=True):
            st.session_state.quiz_index += 1
            st.session_state.awaiting_feedback = False
            st.session_state.question_shown_at = time.time()
            st.rerun()
        enable_enter_to_advance()


def render_results():
    banner()
    cat = CATEGORIES[st.session_state.category]
    title, _fn = cat["skills"][st.session_state.skill_id]
    n = cat["n_questions"]
    correct = sum(1 for r in st.session_state.quiz_results if r)
    elapsed = st.session_state.quiz_end_time - st.session_state.quiz_start_time
    mins, secs = divmod(elapsed, 60)

    st.markdown(f"## Session complete — {title}")
    c1, c2 = st.columns(2)
    c1.metric("Score", f"{correct} / {n}")
    c2.metric("Time taken", f"{int(mins)}m {secs:04.1f}s")

    st.divider()
    b1, b2, b3 = st.columns(3)
    with b1:
        if st.button("🔁 Practice again", use_container_width=True):
            go("settings")
            st.rerun()
    with b2:
        if st.button("📚 Choose another skill", use_container_width=True):
            go("skill_select")
            st.rerun()
    with b3:
        if st.button("🏠 Home", use_container_width=True):
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
