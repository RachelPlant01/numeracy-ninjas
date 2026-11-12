"""Assessment: fluency + understanding for each chosen skill.

Part A (fluency) reuses the practice generators with no scaffold and no
feedback, timing every answer. Part B (understanding) uses the concept
items in `understanding.py`. Each skill then gets a profile and a suggested
tracker level (the same 1–4 levels as the trackers in curriculum.py).

STATUS: the target times below are starting points — adjust them once you've
seen how your classes get on. Nothing about a pupil is stored by the app;
the report is shown on screen and can be downloaded.
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import html as _html
import random
import re
import statistics
import threading
from dataclasses import dataclass, field

from .curriculum import LEVELS
from .generators import KEY_SKILLS, MENTAL_STRATEGIES
from .understanding import concept_items

ALL_SKILLS: dict[str, dict] = {**MENTAL_STRATEGIES, **KEY_SKILLS}

FLUENCY_QUESTIONS = {"MS": 6, "KS": 4}  # per skill, by category
CONCEPT_QUESTIONS = 3  # per skill
MAX_SKILLS = 8
ACCURACY_BAR = 0.8  # fraction correct to count as accurate
UNDERSTANDING_BAR = 2  # concept items correct (out of CONCEPT_QUESTIONS)

# Target median seconds per question for a pupil to count as *fluent*,
# including reading and typing time. Mental strategies default to 5s.
TARGET_SECONDS: dict[str, float] = {
    "MS1": 4, "MS2": 4, "MS30": 4, "MS5": 4, "MS7": 4, "MS9": 4, "MS10": 4,
    "MS3": 5, "MS4": 6, "MS6": 6, "MS8": 6, "MS28": 5, "MS29": 5, "MS11": 6, "MS12": 6,
    "MS13": 5, "MS14": 6, "MS15": 5, "MS16": 6, "MS17": 8, "MS18": 8, "MS19": 8,
    "MS20": 6, "MS21": 6, "MS22": 6, "MS23": 8, "MS25": 12, "MS26": 15, "MS27": 15,
    "KS1": 60, "KS2": 45, "KS3": 30, "KS4": 30, "KS5": 12, "KS6": 20, "KS7": 20, "KS8": 25,
    "KS9": 25, "KS10": 12, "KS11": 10, "KS12": 10, "KS13": 30, "KS14": 30, "KS15": 6, "KS16": 6,
    "KS17": 15, "KS18": 12, "KS19": 20, "KS20": 8, "KS21": 8, "KS22": 8, "KS24": 15, "KS25": 5,
    "KS26": 15, "KS28": 6, "KS29": 8, "KS30": 10, "KS31": 15, "KS32": 15,
}


def n_fluency(sid: str) -> int:
    return FLUENCY_QUESTIONS["MS" if sid.startswith("MS") else "KS"]


def target_seconds(sid: str) -> float:
    return TARGET_SECONDS.get(sid, 5 if sid.startswith("MS") else 20)


def parse_code(code: str) -> list[str]:
    """'ks7, ms5 KS17' -> ['KS7', 'MS5', 'KS17'] (unknown ids dropped)."""
    seen = []
    for tok in re.split(r"[^A-Za-z0-9]+", code or ""):
        tok = tok.upper()
        if tok in ALL_SKILLS and tok not in seen:
            seen.append(tok)
    return seen[:MAX_SKILLS]


# --------------------------------------------------------- seeded questions
# The results code doesn't carry the questions, only a seed: the teacher's
# device regenerates the exact same questions from it. The generators share
# Python's global `random`, so generation is done under a lock, and a
# fingerprint of the questions travels in the code to prove the rebuild matched.
_GEN_LOCK = threading.Lock()


def _sequence(fn, n: int, lang: str, max_attempts: int = 50) -> list:
    """`n` questions with no repeated prompt where the skill allows it
    (same rule as practice mode's generate_question_sequence)."""
    out, seen = [], set()
    for _ in range(n):
        q = fn(lang)
        for _ in range(max_attempts):
            if q.prompt not in seen:
                break
            q = fn(lang)
        out.append(q)
        seen.add(q.prompt)
    return out


def _generate(skills: list[str], lang: str, seed: int) -> tuple[list, list]:
    with _GEN_LOCK:
        random.seed(seed)
        fluency = [(sid, q) for sid in skills for q in _sequence(ALL_SKILLS[sid]["fn"], n_fluency(sid), lang)]
        concept = [(sid, it) for sid in skills for it in concept_items(sid, CONCEPT_QUESTIONS)]
        random.seed()
    return fluency, concept


def fingerprint(fluency: list, concept: list) -> str:
    text = "\n".join([q.prompt + "=" + q.answer_display for _, q in fluency]
                     + [it.prompt + "|" + "|".join(it.options or []) for _, it in concept])
    return hashlib.sha256(text.encode()).hexdigest()[:8]


def build_items(skills: list[str], lang: str, seed: int, expect: str = "", tries: int = 8):
    """(fluency, concept, fingerprint) for this seed. Practice-mode pupils
    also draw from the shared `random`; if one does so mid-generation the
    questions come out different, so generate twice (or against the expected
    fingerprint) and retry until they agree."""
    for _ in range(tries):
        fluency, concept = _generate(skills, lang, seed)
        fp = fingerprint(fluency, concept)
        if fp == (expect or fingerprint(*_generate(skills, lang, seed))):
            return fluency, concept, fp
    raise ValueError("Couldn't rebuild these questions — the code may be from a different version of the app.")


def score(skills: list[str], fluency: list, concept: list, f_given: list, c_given: list) -> list["SkillResult"]:
    """Mark the answers. `f_given` / `c_given` are (answer text, seconds)
    lists in question order."""
    results = {sid: SkillResult(sid) for sid in skills}
    for (sid, q), (given, secs) in zip(fluency, f_given):
        results[sid].fluency.append(Response(sid, q.prompt, q.answer_display, given, q.checker(given), secs))
    for (sid, it), (given, secs) in zip(concept, c_given):
        ok = it.checker(given)
        results[sid].concept.append(Response(sid, it.prompt, it.answer_display, given, ok, secs,
                                             kind=it.kind, note="" if ok else it.notes.get(given, "")))
    return [results[sid] for sid in skills]


@dataclass
class Response:
    skill_id: str
    prompt: str
    answer: str
    given: str
    correct: bool
    seconds: float
    kind: str = ""  # concept items only
    note: str = ""  # misconception suggested by a wrong option


@dataclass
class SkillResult:
    skill_id: str
    fluency: list[Response] = field(default_factory=list)
    concept: list[Response] = field(default_factory=list)

    @property
    def name(self) -> str:
        return ALL_SKILLS[self.skill_id]["en"]

    @property
    def accuracy(self) -> float:
        return sum(r.correct for r in self.fluency) / len(self.fluency) if self.fluency else 0.0

    @property
    def median_seconds(self) -> float:
        return statistics.median(r.seconds for r in self.fluency) if self.fluency else 0.0

    @property
    def concept_score(self) -> int:
        return sum(r.correct for r in self.concept)

    @property
    def fluency_band(self) -> str:
        if self.accuracy < ACCURACY_BAR:
            return "Not yet accurate"
        return "Fluent" if self.median_seconds <= target_seconds(self.skill_id) else "Accurate, not yet quick"

    @property
    def understands(self) -> bool:
        return self.concept_score >= UNDERSTANDING_BAR

    def profile(self) -> tuple[str, int, str]:
        """(headline, suggested tracker level 1–4, next step)."""
        band = self.fluency_band
        if self.understands:
            if band == "Fluent":
                return "Secure — fluent and understands", 4, "Keep it fresh with mixed practice; move on."
            if band == "Accurate, not yet quick":
                return "Understands — building speed", 3, "Short, frequent practice with no scaffold to build speed."
            return "Understands the idea — needs practice", 2, "Practise with the scaffold faded to build accuracy."
        if band == "Not yet accurate":
            return "Needs teaching", 1, "Reteach with the scaffold and modelling; check the misconceptions below."
        return ("Can do it, but understanding is shaky", 2,
                "Answers are right but the reasoning isn't secure — revisit with the scaffold and talk it through.")


def level_label(level: int) -> tuple[str, str]:
    _code, label, colour = LEVELS[level - 1]
    return label, colour


# ------------------------------------------------------------------- report
def _esc(s) -> str:
    return _html.escape(str(s))


def build_report(results: list[SkillResult], pupil: str = "", lang: str = "en") -> str:
    """One self-contained HTML report (A4, print ready) for the teacher."""
    today = f"{_dt.date.today():%d %B %Y}"
    rows = []
    for r in results:
        head, level, step = r.profile()
        label, colour = level_label(level)
        rows.append(
            f"<tr><td><b>{_esc(r.skill_id)}</b> {_esc(r.name)}</td>"
            f"<td>{sum(x.correct for x in r.fluency)}/{len(r.fluency)}</td>"
            f"<td>{r.median_seconds:.1f}s <span class='muted'>(target {target_seconds(r.skill_id):g}s)</span></td>"
            f"<td>{_esc(r.fluency_band)}</td>"
            f"<td>{r.concept_score}/{len(r.concept)}</td>"
            f"<td><b>{_esc(head)}</b><br><span class='muted'>{_esc(step)}</span></td>"
            f"<td style='background:{colour};text-align:center'><b>{level}</b><br><small>{_esc(label)}</small></td></tr>"
        )

    detail = []
    for r in results:
        items = []
        for x in r.fluency:
            mark = "✓" if x.correct else "✗"
            items.append(f"<tr class='{'ok' if x.correct else 'bad'}'><td>Fluency</td><td>{x.prompt}</td>"
                         f"<td>{_esc(x.given or '(blank)')}</td><td>{_esc(x.answer)}</td>"
                         f"<td>{mark} {x.seconds:.1f}s</td></tr>")
        for x in r.concept:
            mark = "✓" if x.correct else "✗"
            note = f"<br><span class='note'>Possible misconception: {_esc(x.note)}</span>" if x.note else ""
            items.append(f"<tr class='{'ok' if x.correct else 'bad'}'><td>{_esc(x.kind)}</td><td>{_esc(x.prompt)}</td>"
                         f"<td>{_esc(x.given or '(blank)')}{note}</td><td>{_esc(x.answer)}</td>"
                         f"<td>{mark} {x.seconds:.1f}s</td></tr>")
        detail.append(f"<h3>{_esc(r.skill_id)} — {_esc(r.name)}</h3>"
                      "<table class='detail'><tr><th>Part</th><th>Question</th><th>Answer given</th>"
                      f"<th>Correct answer</th><th></th></tr>{''.join(items)}</table>")

    who = f" — {_esc(pupil)}" if pupil.strip() else ""
    return f"""<!doctype html><html><head><meta charset="utf-8"><title>Numeracy assessment{who}</title>
<style>
body {{ font-family: Arial, sans-serif; margin: 24px; color: #1c1c1c; }}
h1 {{ margin: 0 0 4px; font-size: 22px; }} h3 {{ margin: 22px 0 6px; }}
.muted {{ color: #666; font-size: 12px; }} .note {{ color: #a33; font-size: 12px; }}
table {{ border-collapse: collapse; width: 100%; font-size: 13px; }}
th, td {{ border: 1px solid #bbb; padding: 5px 7px; vertical-align: top; text-align: left; }}
th {{ background: #f0f0f0; }} tr.bad td {{ background: #fff4f2; }}
.key {{ font-size: 12px; margin: 10px 0 16px; line-height: 1.5; }}
.print {{ margin-bottom: 16px; }} @media print {{ .print {{ display: none; }} h3 {{ break-after: avoid; }} }}
</style></head><body>
<button class="print" onclick="window.print()">Print / Save as PDF</button>
<h1>Numeracy assessment{who}</h1>
<div class="muted">{today}{' · questions in Gàidhlig' if lang == 'gd' else ''}</div>
<div class="key"><b>Fluency</b>: {FLUENCY_QUESTIONS['MS']} questions per mental strategy, {FLUENCY_QUESTIONS['KS']} per key skill — no scaffold, no feedback, timed.
Fluent = at least {int(ACCURACY_BAR * 100)}% correct <i>and</i> a median time within the target.<br>
<b>Understanding</b>: {CONCEPT_QUESTIONS} questions per skill — spotting mistakes, using known facts, reasoning and estimating.
Understands = at least {UNDERSTANDING_BAR} of {CONCEPT_QUESTIONS} correct.<br>
<b>Tracker level</b> is a suggestion — your judgement wins.</div>
<table><tr><th>Skill</th><th>Fluency correct</th><th>Median time</th><th>Fluency</th><th>Understanding</th>
<th>Profile and next step</th><th>Tracker</th></tr>{''.join(rows)}</table>
<h2 style="font-size:18px;margin-top:26px">Question by question</h2>{''.join(detail)}
</body></html>"""
