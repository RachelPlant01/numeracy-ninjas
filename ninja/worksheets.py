"""Printable worksheets built from the app's own question generators.

`build_worksheets()` returns one self-contained HTML document (A4, print
ready) holding every sheet, with optional answer pages at the end. Teachers
download it, open it in a browser and print / save as PDF.
"""
from __future__ import annotations

import html as _html
import random
from dataclasses import dataclass
from functools import lru_cache

from . import scaffold_types as stypes  # installs the scaffold tagging
from . import scaffolds as sc
from .curriculum import EO_DRAFT, eo_label
from .generators import KEY_SKILLS, MENTAL_STRATEGIES

ALL_SKILLS: dict[str, dict] = {**MENTAL_STRATEGIES, **KEY_SKILLS}

# How many re-rolls we allow while hunting for a ticked scaffold type / a
# prompt not already on the sheet. Generation is ~0.03 ms, so this is cheap
# (some types are rare for a skill, e.g. fraction circles in KS17).
_MAX_TRIES = 2000


def skill_name(sid: str, lang: str = "en") -> str:
    return ALL_SKILLS[sid]["gd" if lang == "gd" else "en"]


@lru_cache(maxsize=None)
def available_types(sid: str, samples: int = 250) -> tuple[str, ...]:
    """Scaffold types this skill can draw, found by sampling it."""
    fn = ALL_SKILLS[sid]["fn"]
    seen = set()
    for _ in range(samples):
        seen.add(stypes.scaffold_type(fn("en").scaffold_html))
    return tuple(t for t in stypes.ALL_TYPES if t in seen)


@dataclass
class SheetQuestion:
    sid: str
    prompt: str
    answer: str
    scaffold_html: str
    scaffold_type: str
    show_scaffold: bool
    type_matched: bool


def _make_question(sid: str, wanted: set[str] | None, seen: set[str], lang: str):
    fn = ALL_SKILLS[sid]["fn"]
    can_match = wanted is None or bool(wanted & set(available_types(sid)))
    fallback = None
    for _ in range(_MAX_TRIES):
        q = fn(lang)
        t = stypes.scaffold_type(q.scaffold_html)
        type_ok = (not can_match) or wanted is None or t in wanted
        if type_ok and fallback is None:
            fallback = (q, t)
        if type_ok and q.prompt not in seen:
            return q, t, can_match
    q, t = fallback if fallback else (q, t)
    return q, t, can_match and (wanted is None or t in wanted)


def generate_sheet(skill_ids: list[str], n_questions: int, wanted_types: set[str] | None,
                   scaffold_mode: str = "all", mix: bool = False, lang: str = "en") -> list[SheetQuestion]:
    """`scaffold_mode`: "all", "first_half" (scaffolds fade out half way) or "none"."""
    # Share the questions out between the skills as evenly as possible.
    order = [skill_ids[i % len(skill_ids)] for i in range(n_questions)]
    if mix:
        random.shuffle(order)
    else:
        order.sort(key=skill_ids.index)
    seen: set[str] = set()
    out = []
    for i, sid in enumerate(order):
        q, t, matched = _make_question(sid, wanted_types, seen, lang)
        seen.add(q.prompt)
        if scaffold_mode == "none":
            show = False
        elif scaffold_mode == "first_half":
            show = i < (n_questions + 1) // 2
        else:
            show = True
        out.append(SheetQuestion(sid, q.prompt, q.answer_display, q.scaffold_html, t, show, matched))
    return out


# --------------------------------------------------------------------- HTML
_CSS = """
@page { size: A4; margin: 12mm 12mm 14mm 12mm; }
* { box-sizing: border-box; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body { font-family: Arial, Helvetica, sans-serif; color: #1c1c1c; background: #fff; margin: 0; }
.toolbar { position: sticky; top: 0; background: #f4f6fa; border-bottom: 1px solid #d5dbe5;
  padding: 10px 16px; display: flex; gap: 12px; align-items: center; z-index: 5; font-size: 14px; }
.toolbar button { font-size: 15px; font-weight: 700; padding: 8px 16px; border-radius: 8px;
  border: 0; background: #1c64d6; color: #fff; cursor: pointer; }
.sheet { width: 186mm; margin: 0 auto; padding: 8mm 0 4mm; page-break-after: always; break-after: page; }
.sheet:last-child { page-break-after: auto; break-after: auto; }
.head { border: 2px solid #1c1c1c; border-radius: 8px; padding: 8px 12px; margin-bottom: 10px; }
.head-top { display: flex; justify-content: space-between; align-items: baseline; gap: 10px; }
.title { font-size: 20px; font-weight: 800; }
.sheetno { font-size: 13px; color: #555; white-space: nowrap; }
.fields { display: flex; gap: 18px; margin-top: 8px; font-size: 14px; }
.fields span { flex: 1; border-bottom: 1px solid #555; padding-bottom: 2px; }
.fields span.short { flex: 0 0 26%; }
.skills { font-size: 12px; color: #444; margin-top: 6px; }
.q { display: flex; gap: 10px; padding: 8px 2px 10px; border-bottom: 1px dashed #c5c9d0;
  break-inside: avoid; page-break-inside: avoid; }
.qn { flex: 0 0 30px; height: 30px; border-radius: 50%; background: #1c1c1c; color: #fff;
  font-weight: 700; display: flex; align-items: center; justify-content: center; font-size: 15px; }
.qbody { flex: 1; min-width: 0; }
.prompt { font-size: 22px; font-weight: 700; margin: 2px 0 6px; line-height: 1.3; }
.scaf { zoom: 0.8; max-width: 100%; overflow: hidden; }
.ans { display: flex; justify-content: flex-end; margin-top: 6px; font-size: 15px; }
.ans span { display: inline-block; width: 46mm; border-bottom: 1.5px solid #333; margin-left: 6px; }
.work { height: 22mm; }
.compact .scaf { zoom: 0.52; }
.compact .prompt { font-size: 18px; }
.compact .ans span { width: 30mm; }
.quick .q { padding: 6px 2px 8px; }
.quick .ans { margin-top: 2px; }
.grid2 { display: grid; grid-template-columns: 1fr 1fr; column-gap: 8mm; }
.grid2 .q { border-bottom: 1px dashed #c5c9d0; }
.foot { margin-top: 8px; font-size: 10.5px; color: #666; }
.answers h2 { font-size: 18px; margin: 0 0 6px; }
.answers table { border-collapse: collapse; width: 100%; font-size: 14px; margin-bottom: 12px; }
.answers td, .answers th { border: 1px solid #999; padding: 4px 6px; text-align: left; vertical-align: middle; }
.answers th { background: #eef1f6; }
.anskey { break-inside: avoid; page-break-inside: avoid; }
@media print { .toolbar { display: none; } .sheet { padding-top: 0; } }
"""


def _esc(s: str) -> str:
    return _html.escape(s, quote=False)


def _skills_line(skill_ids: list[str], lang: str) -> str:
    parts = [f"<b>{sid}</b> {_esc(skill_name(sid, lang))} ({eo_label(sid)})" for sid in skill_ids]
    return " · ".join(parts)


def render_document(sheets: list[list[SheetQuestion]], title: str, skill_ids: list[str],
                    bw: bool = False, answers: bool = True, lang: str = "en",
                    layout: str = "large") -> str:
    """`layout`: "large" (one scaffolded question per row) or "compact" (two per row)."""
    blocks = []
    n = len(sheets)
    for si, qs in enumerate(sheets, start=1):
        no_scaffolds = not any(q.show_scaffold for q in qs)
        rows = []
        for qi, q in enumerate(qs, start=1):
            scaf = ""
            if q.show_scaffold:
                h = sc.to_black_and_white(q.scaffold_html) if bw else q.scaffold_html
                scaf = f'<div class="scaf">{h}</div>'
            # Written-method key skills get working space when there's no
            # scaffold; mental strategies are answered straight off.
            work = "" if q.show_scaffold or not q.sid.startswith("KS") else '<div class="work"></div>'
            rows.append(
                f'<div class="q"><div class="qn">{qi}</div><div class="qbody">'
                f'<div class="prompt">{q.prompt}</div>{scaf}{work}'
                f'<div class="ans">Answer:<span></span></div></div></div>'
            )
        quick = no_scaffolds and not any(q.sid.startswith("KS") for q in qs)
        if no_scaffolds or layout == "compact":
            cls = "grid2" + (" compact" if layout == "compact" and not no_scaffolds else "") + (" quick" if quick else "")
            body = f'<div class="{cls}">{"".join(rows)}</div>'
        else:
            body = "".join(rows)
        sheet_label = f"Sheet {si} of {n}" if n > 1 else ""
        blocks.append(
            f'<section class="sheet"><div class="head"><div class="head-top">'
            f'<div class="title">{_esc(title)}</div><div class="sheetno">{sheet_label}</div></div>'
            f'<div class="fields"><span>Name:</span><span class="short">Class:</span>'
            f'<span class="short">Date:</span></div>'
            f'<div class="skills">{_skills_line(skill_ids, lang)}</div></div>'
            f'{body}'
            f'<div class="foot">Numeracy Ninjas · '
            f'{"Es and Os links are a draft. " if EO_DRAFT else ""}'
            f'Score: ____ / {len(qs)}</div></section>'
        )

    if answers:
        keys = []
        for si, qs in enumerate(sheets, start=1):
            trs = "".join(
                f"<tr><td>{qi}</td><td>{q.prompt}</td><td><b>{_esc(q.answer)}</b></td></tr>"
                for qi, q in enumerate(qs, start=1)
            )
            keys.append(
                f'<div class="anskey"><h2>Answers — {"Sheet " + str(si) if n > 1 else _esc(title)}</h2>'
                f"<table><tr><th>Q</th><th>Question</th><th>Answer</th></tr>{trs}</table></div>"
            )
        blocks.append(f'<section class="sheet answers">{"".join(keys)}</section>')

    toolbar = (
        '<div class="toolbar"><button onclick="window.print()">🖨️ Print / Save as PDF</button>'
        f'<span>{n} sheet{"s" if n != 1 else ""}{" + answers" if answers else ""}. '
        'Tip: in the print box, set margins to "Default" and turn off headers and footers.</span></div>'
    )
    return (
        f'<!doctype html><html lang="{lang}"><head><meta charset="utf-8">'
        f'<meta name="viewport" content="width=device-width, initial-scale=1">'
        f"<title>{_esc(title)}</title><style>{_CSS}</style></head>"
        f'<body>{toolbar}{"".join(blocks)}</body></html>'
    )


def build_worksheets(skill_ids: list[str], n_sheets: int, n_questions: int,
                     wanted_types: set[str] | None, scaffold_mode: str = "all",
                     mix: bool = False, bw: bool = False, answers: bool = True,
                     title: str = "Numeracy practice", lang: str = "en", layout: str = "large"):
    """Returns (html, sheets) — sheets kept so the app can report mismatches."""
    sheets = [generate_sheet(skill_ids, n_questions, wanted_types, scaffold_mode, mix, lang)
              for _ in range(n_sheets)]
    return render_document(sheets, title, skill_ids, bw, answers, lang, layout), sheets
