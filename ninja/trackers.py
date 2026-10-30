"""Skill trackers: an Excel workbook (for the shared OneDrive) and printable
HTML versions (class grid and individual pupil record).

Levels 1–4 come from `curriculum.LEVELS`. No pupil names are entered or
stored in the app — the name cells are left blank for teachers to fill in.
"""
from __future__ import annotations

import html as _html
import io
import re

from .curriculum import EO_DRAFT, EOS, LEVELS, eo_codes, eo_label
from .generators import KEY_SKILLS, MENTAL_STRATEGIES

GROUPS = [("Mental strategies", MENTAL_STRATEGIES), ("Key skills", KEY_SKILLS)]


def _grouped(skill_ids: list[str]):
    """[(group title, [(sid, name), ...]), ...] in the app's own order."""
    out = []
    for title, d in GROUPS:
        rows = [(sid, d[sid]["en"]) for sid in d if sid in skill_ids]
        if rows:
            out.append((title, rows))
    return out


# ------------------------------------------------------------------ Excel
def build_excel(class_names: list[str], skill_ids: list[str], n_pupils: int = 25) -> bytes:
    from openpyxl import Workbook
    from openpyxl.formatting.rule import CellIsRule
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
    from openpyxl.utils import get_column_letter
    from openpyxl.worksheet.datavalidation import DataValidation

    thin = Side(style="thin", color="999999")
    box = Border(left=thin, right=thin, top=thin, bottom=thin)
    head_fill = PatternFill("solid", fgColor="E8ECF3")
    group_fill = PatternFill("solid", fgColor="1C1C1C")
    level_fills = [PatternFill("solid", fgColor=c.lstrip("#").upper()) for _, _, c in LEVELS]
    wrap = Alignment(wrap_text=True, vertical="center")
    centre = Alignment(horizontal="center", vertical="center")

    wb = Workbook()
    wb.remove(wb.active)

    # --- Key / how to use
    ks = wb.create_sheet("Key")
    ks["A1"] = "Numeracy skills tracker"
    ks["A1"].font = Font(size=16, bold=True)
    ks["A3"] = "Type a level number (1–4) in a pupil's column. The cell colours itself."
    ks["A4"] = "Pupil names go in the yellow cells along the top of each class sheet."
    ks["A5"] = "Add a class: right-click a class tab → Move or Copy → tick Create a copy."
    for i, (code, label, _) in enumerate(LEVELS):
        r = 7 + i
        ks.cell(r, 1, int(code)).fill = level_fills[i]
        ks.cell(r, 1).alignment = centre
        ks.cell(r, 1).border = box
        ks.cell(r, 2, label).border = box
    if EO_DRAFT:
        ks["A12"] = "Es and Os links are a DRAFT — please check before relying on them."
        ks["A12"].font = Font(italic=True, color="AA0000")
    ks.column_dimensions["A"].width = 10
    ks.column_dimensions["B"].width = 40

    # --- one sheet per class
    first_pupil_col = 4
    last_pupil_col = first_pupil_col + n_pupils - 1
    sum_col = last_pupil_col + 1
    used = set()
    for cname in class_names or ["Class 1"]:
        title = re.sub(r"[\[\]\*\?/\\:]", "-", cname.strip() or "Class")[:31]
        base, k = title, 2
        while title in used:
            title = f"{base[:28]} ({k})"
            k += 1
        used.add(title)
        ws = wb.create_sheet(title)

        ws["A1"] = f"Numeracy skills tracker — {cname}"
        ws["A1"].font = Font(size=14, bold=True)
        key_txt = "   ".join(f"{c} = {lab}" for c, lab, _ in LEVELS)
        ws["A2"] = "Key: " + key_txt
        ws["A2"].font = Font(size=10, color="444444")

        hdr = 4
        for col, text in [(1, "Code"), (2, "Skill"), (3, "Es and Os" + (" (draft)" if EO_DRAFT else ""))]:
            c = ws.cell(hdr, col, text)
            c.font = Font(bold=True)
            c.fill = head_fill
            c.border = box
            c.alignment = wrap
        name_fill = PatternFill("solid", fgColor="FFF8D6")
        for col in range(first_pupil_col, last_pupil_col + 1):
            c = ws.cell(hdr, col, None)
            c.fill = name_fill
            c.border = box
            c.alignment = Alignment(text_rotation=90, horizontal="center", vertical="bottom")
            ws.column_dimensions[get_column_letter(col)].width = 4.2
        for i, (code, _, _) in enumerate(LEVELS):
            col = sum_col + i
            c = ws.cell(hdr, col, f"No. at {code}")
            c.font = Font(bold=True, size=9)
            c.fill = level_fills[i]
            c.border = box
            c.alignment = Alignment(text_rotation=90, horizontal="center", vertical="bottom")
            ws.column_dimensions[get_column_letter(col)].width = 4.6
        ws.row_dimensions[hdr].height = 95
        ws.column_dimensions["A"].width = 6
        ws.column_dimensions["B"].width = 34
        ws.column_dimensions["C"].width = 18

        dv = DataValidation(type="list", formula1='"1,2,3,4"', allow_blank=True,
                            showErrorMessage=True, errorTitle="Level 1–4",
                            error="Please enter 1, 2, 3 or 4 (see the key).")
        ws.add_data_validation(dv)

        r = hdr + 1
        first_data = r
        for gtitle, rows in _grouped(skill_ids):
            ws.cell(r, 1, gtitle)
            for col in range(1, sum_col + len(LEVELS)):
                ws.cell(r, col).fill = group_fill
                ws.cell(r, col).font = Font(bold=True, color="FFFFFF")
            r += 1
            for sid, name in rows:
                ws.cell(r, 1, sid).border = box
                ws.cell(r, 2, name).border = box
                ws.cell(r, 2).alignment = wrap
                e = ws.cell(r, 3, eo_label(sid))
                e.border = box
                e.alignment = wrap
                e.font = Font(size=9)
                for col in range(first_pupil_col, last_pupil_col + 1):
                    c = ws.cell(r, col)
                    c.border = box
                    c.alignment = centre
                rng = f"{get_column_letter(first_pupil_col)}{r}:{get_column_letter(last_pupil_col)}{r}"
                dv.add(rng)
                for i, (code, _, _) in enumerate(LEVELS):
                    c = ws.cell(r, sum_col + i, f'=COUNTIF({rng},{code})')
                    c.border = box
                    c.alignment = centre
                    c.font = Font(size=9, color="555555")
                r += 1
        last_data = r - 1

        area = f"{get_column_letter(first_pupil_col)}{first_data}:{get_column_letter(last_pupil_col)}{last_data}"
        for i, (code, _, _) in enumerate(LEVELS):
            ws.conditional_formatting.add(area, CellIsRule(operator="equal", formula=[code], fill=level_fills[i]))

        ws.freeze_panes = ws.cell(hdr + 1, first_pupil_col)
        ws.print_title_rows = f"{hdr}:{hdr}"
        ws.page_setup.orientation = "landscape"
        ws.page_setup.paperSize = ws.PAPERSIZE_A4
        ws.page_setup.fitToWidth = 1
        ws.page_setup.fitToHeight = 0
        ws.sheet_properties.pageSetUpPr.fitToPage = True
        ws.print_options.gridLines = False

    # --- Es and Os reference
    es = wb.create_sheet("Es and Os")
    es["A1"] = "Es and Os used" + (" (DRAFT — check before relying on)" if EO_DRAFT else "")
    es["A1"].font = Font(bold=True, size=13)
    es["A3"], es["B3"], es["C3"] = "Code", "Short wording", "Skills"
    for c in ("A3", "B3", "C3"):
        es[c].font = Font(bold=True)
        es[c].fill = head_fill
    used_codes = sorted({c for sid in skill_ids for c in eo_codes(sid)})
    for i, code in enumerate(used_codes, start=4):
        es.cell(i, 1, code)
        es.cell(i, 2, EOS.get(code, "")).alignment = wrap
        es.cell(i, 3, ", ".join(s for s in skill_ids if code in eo_codes(s))).alignment = wrap
    es.column_dimensions["A"].width = 12
    es.column_dimensions["B"].width = 70
    es.column_dimensions["C"].width = 40

    wb.move_sheet("Key", offset=len(wb.sheetnames))  # class sheets first
    wb.active = 0
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


# ------------------------------------------------------- printable (HTML)
_CSS = """
* { box-sizing: border-box; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body { font-family: Arial, Helvetica, sans-serif; color: #1c1c1c; background: #fff; margin: 0; }
.toolbar { position: sticky; top: 0; background: #f4f6fa; border-bottom: 1px solid #d5dbe5;
  padding: 10px 16px; display: flex; gap: 12px; align-items: center; z-index: 5; font-size: 14px; }
.toolbar button { font-size: 15px; font-weight: 700; padding: 8px 16px; border-radius: 8px;
  border: 0; background: #1c64d6; color: #fff; cursor: pointer; }
.page { margin: 0 auto; padding: 8mm 0; page-break-after: always; break-after: page; }
.page:last-child { page-break-after: auto; break-after: auto; }
h1 { font-size: 18px; margin: 0 0 4px; }
.meta { display: flex; gap: 18px; font-size: 13px; margin: 6px 0 8px; }
.meta span { flex: 1; border-bottom: 1px solid #555; padding-bottom: 2px; }
.key { display: flex; gap: 6px; flex-wrap: wrap; font-size: 11px; margin-bottom: 8px; }
.key b { display: inline-block; min-width: 18px; text-align: center; border: 1px solid #888;
  border-radius: 3px; margin-right: 3px; }
.key span { display: inline-flex; align-items: center; }
table { border-collapse: collapse; width: 100%; }
td, th { border: 1px solid #888; font-size: 10.5px; padding: 2px 4px; }
th { background: #e8ecf3; }
tr { break-inside: avoid; page-break-inside: avoid; }
.grp td { background: #1c1c1c; color: #fff; font-weight: 700; font-size: 11px; }
.code { white-space: nowrap; font-weight: 700; }
.eo { font-size: 9px; color: #444; }
.name { height: 30mm; vertical-align: bottom; width: 6.5mm; background: #fffbe6; }
.cell { width: 6.5mm; height: 6.5mm; }
.lvl { text-align: center; font-size: 10px; }
.lvlcell { height: 9mm; width: 21mm; }
.note { font-size: 10px; color: #666; margin-top: 6px; }
@media print { .toolbar { display: none; } .page { padding-top: 0; } }
"""


def _esc(s: str) -> str:
    return _html.escape(s, quote=False)


def _key_html() -> str:
    return '<div class="key">' + "".join(
        f'<span><b style="background:{c}">{code}</b>{_esc(lab)}</span>' for code, lab, c in LEVELS
    ) + "</div>"


def _doc(title: str, page_css: str, body: str) -> str:
    toolbar = ('<div class="toolbar"><button onclick="window.print()">🖨️ Print / Save as PDF</button>'
               '<span>Tip: turn off headers and footers in the print box.</span></div>')
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>{_esc(title)}</title>'
            f"<style>{_CSS}{page_css}</style></head><body>{toolbar}{body}</body></html>")


def printable_class_grid(class_name: str, skill_ids: list[str], n_pupils: int = 20) -> str:
    """A4 landscape: skills down the side, a blank column per pupil."""
    names = "".join('<th class="name"></th>' for _ in range(n_pupils))
    rows = []
    for gtitle, items in _grouped(skill_ids):
        rows.append(f'<tr class="grp"><td colspan="{2 + n_pupils}">{_esc(gtitle)}</td></tr>')
        for sid, name in items:
            cells = '<td class="cell"></td>' * n_pupils
            rows.append(f'<tr><td class="code">{sid}</td><td>{_esc(name)}<div class="eo">'
                        f'{eo_label(sid)}</div></td>{cells}</tr>')
    body = (f'<section class="page"><h1>Numeracy skills tracker — {_esc(class_name)}</h1>'
            f'<div class="meta"><span>Teacher:</span><span>Session:</span></div>{_key_html()}'
            f'<table><thead><tr><th>Code</th><th style="min-width:55mm">Skill / Es and Os</th>{names}</tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table>'
            f'<div class="note">Write the level (1–4) or colour the square. Pupil names in the top row.'
            f'{" Es and Os links are a draft." if EO_DRAFT else ""}</div></section>')
    css = "@page { size: A4 landscape; margin: 10mm; } .page { width: 277mm; }"
    return _doc(f"Tracker — {class_name}", css, body)


def printable_pupil_record(skill_ids: list[str], copies: int = 1) -> str:
    """A4 portrait: one pupil, every skill, a date box under each level."""
    heads = "".join(f'<th class="lvl" style="background:{c}">{code}<br>{_esc(lab)}</th>'
                    for code, lab, c in LEVELS)
    rows = []
    for gtitle, items in _grouped(skill_ids):
        rows.append(f'<tr class="grp"><td colspan="{2 + len(LEVELS)}">{_esc(gtitle)}</td></tr>')
        for sid, name in items:
            cells = '<td class="lvlcell"></td>' * len(LEVELS)
            rows.append(f'<tr><td class="code">{sid}</td><td>{_esc(name)}<div class="eo">'
                        f'{eo_label(sid)}</div></td>{cells}</tr>')
    page = (f'<section class="page"><h1>My numeracy skills</h1>'
            f'<div class="meta"><span>Name:</span><span>Class:</span></div>'
            f'<table><thead><tr><th>Code</th><th>Skill / Es and Os</th>{heads}</tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table>'
            f'<div class="note">Write the date in a box when that level is reached.'
            f'{" Es and Os links are a draft." if EO_DRAFT else ""}</div></section>')
    css = "@page { size: A4 portrait; margin: 10mm; } .page { width: 190mm; } thead { display: table-header-group; }"
    return _doc("Pupil skills record", css, page * max(1, copies))
