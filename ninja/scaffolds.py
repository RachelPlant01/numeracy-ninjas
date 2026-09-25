"""Reusable visual-scaffold builders.

Each function returns a self-contained HTML/SVG snippet (string) styled to
loosely echo the look of the Numeracy Ninjas scaffolded worksheets (ten
frames, number-line jumps, bar models, place-value grids, clock faces) plus
a plain worked-steps hint list for skills that don't have a natural picture.
"""
from __future__ import annotations

import html


CARD_STYLE = (
    "border:2px solid #2b2b2b;border-radius:10px;padding:12px 20px;"
    "background:#fafafa;margin:4px 0;box-sizing:border-box;"
)


def _wrap(inner: str, note: str | None = None) -> str:
    # `note` (a plain-English caption) is intentionally not rendered — the
    # scaffold should be the picture alone, not a worded explanation of it.
    return f'<div style="{CARD_STYLE}">{inner}</div>'


# ---------------------------------------------------------------- number line
def number_line(
    min_v: int,
    max_v: int,
    jumps: list[tuple[float, float, str, str]] | None = None,
    circle: float | None = None,
    note: str | None = None,
    width: int = 640,
) -> str:
    height = 150 if jumps else 90
    n = max_v - min_v
    if n <= 0:
        n = 1
    pad = 40
    usable = width - 2 * pad

    def x(v: float) -> float:
        return pad + (v - min_v) / n * usable

    svg_parts = [
        f'<svg viewBox="0 0 {width} {height}" width="100%" height="{height}" '
        f'xmlns="http://www.w3.org/2000/svg" font-family="inherit">'
    ]
    y_line = height - 30
    svg_parts.append(
        f'<line x1="{pad}" y1="{y_line}" x2="{width - pad}" y2="{y_line}" '
        f'stroke="#222" stroke-width="2" marker-end="url(#arrow)"/>'
    )
    svg_parts.append(
        '<defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="4" refY="4" '
        'orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#222"/></marker></defs>'
    )
    step = 1 if n <= 20 else max(1, n // 20)
    v = min_v
    while v <= max_v:
        xv = x(v)
        svg_parts.append(f'<line x1="{xv}" y1="{y_line-6}" x2="{xv}" y2="{y_line+6}" stroke="#222" stroke-width="1.5"/>')
        if circle is not None and abs(v - circle) < 1e-9:
            svg_parts.append(f'<circle cx="{xv}" cy="{y_line+22}" r="13" fill="none" stroke="#c0392b" stroke-width="2"/>')
            svg_parts.append(f'<text x="{xv}" y="{y_line+27}" text-anchor="middle" font-size="13" fill="#c0392b" font-weight="bold">{v:g}</text>')
        else:
            svg_parts.append(f'<text x="{xv}" y="{y_line+24}" text-anchor="middle" font-size="13" fill="#222">{v:g}</text>')
        v += step

    colors = ["#2e6da4", "#c0392b", "#27ae60", "#8e44ad"]
    if jumps:
        for i, (a, b, label, _c) in enumerate(jumps):
            color = colors[i % len(colors)]
            xa, xb = x(a), x(b)
            mid = (xa + xb) / 2
            arc_h = 34 + 18 * i
            dash = "" if i == 0 else 'stroke-dasharray="5,4"'
            svg_parts.append(
                f'<path d="M{xa},{y_line} Q{mid},{y_line-arc_h} {xb},{y_line}" '
                f'fill="none" stroke="{color}" stroke-width="2.5" {dash} marker-end="url(#arrow)"/>'
            )
            svg_parts.append(
                f'<text x="{mid}" y="{y_line-arc_h-6}" text-anchor="middle" font-size="14" '
                f'fill="{color}" font-weight="bold">{html.escape(label)}</text>'
            )
    svg_parts.append("</svg>")
    return _wrap("".join(svg_parts), note)


# ------------------------------------------------------------------ ten frame
def ten_frame_pair(known: int, total: int, note: str | None = None) -> str:
    """Two ten-frames: `known` solid dots, then dashed dots up to `total`."""
    extra = max(total - known, 0)

    def frame(filled_from: int, filled_to: int, dashed_from: int, dashed_to: int) -> str:
        cells = []
        for i in range(10):
            row, col = divmod(i, 5)
            filled = filled_from <= i < filled_to
            dashed = dashed_from <= i < dashed_to
            if filled:
                dot = '<circle cx="19" cy="19" r="13" fill="#111"/>'
            elif dashed:
                dot = '<circle cx="19" cy="19" r="13" fill="none" stroke="#999" stroke-width="2" stroke-dasharray="3,3"/>'
            else:
                dot = ""
            cells.append(
                f'<div style="width:38px;height:38px;border:1px solid #333;'
                f'display:flex;align-items:center;justify-content:center;">'
                f'<svg width="38" height="38">{dot}</svg></div>'
            )
        rows = "".join(cells[0:5])
        rows2 = "".join(cells[5:10])
        return (
            f'<div style="display:inline-grid;grid-template-columns:repeat(5,38px);'
            f'grid-template-rows:repeat(2,38px);width:190px;">{rows}{rows2}</div>'
        )

    total_all = 10
    f1_known = min(known, 10)
    f1_extra_to = min(known + extra, 10)
    inner = frame(0, f1_known, f1_known, f1_extra_to)
    if known + extra > 10:
        known2 = 0
        extra2_from = max(0, known - 10)
        extra2_to = min(total_all, (known + extra) - 10)
        inner2 = frame(0, 0, extra2_from, extra2_to)
        inner = f'<div style="display:flex;gap:14px;flex-wrap:wrap;">{inner}{inner2}</div>'
    return _wrap(inner, note)


# -------------------------------------------------------------------- bar model
def bar_model(whole_label: str, parts: list[tuple[str, float]], note: str | None = None) -> str:
    """parts: list of (label, weight) — rendered as proportional segments."""
    total_weight = sum(w for _, w in parts) or 1
    colors = ["#f6c453", "#a3c9f9", "#b7e4c7", "#f7a5a5", "#d8bfd8"]
    segs = []
    for i, (label, w) in enumerate(parts):
        pct = 100 * w / total_weight
        color = colors[i % len(colors)]
        segs.append(
            f'<div style="width:{pct}%;background:{color};border:1px solid #333;'
            f'display:flex;align-items:center;justify-content:center;min-height:44px;'
            f'font-size:0.95rem;box-sizing:border-box;">{html.escape(label)}</div>'
        )
    top = (
        f'<div style="border:1px solid #333;min-height:40px;display:flex;'
        f'align-items:center;justify-content:center;background:#eee;font-weight:bold;">'
        f'{html.escape(whole_label)}</div>'
    )
    bottom = f'<div style="display:flex;width:100%;">{"".join(segs)}</div>'
    return _wrap(f'<div style="display:flex;flex-direction:column;gap:4px;">{top}{bottom}</div>', note)


# ------------------------------------------------------------- place value grid
def place_value_grid(number_str: str, headers: list[str], highlight: int | None = None, note: str | None = None) -> str:
    digits = list(number_str)
    cells_h, cells_d = [], []
    for i, (h, d) in enumerate(zip(headers, digits)):
        bg = "#ffe08a" if highlight == i else "#f0f0f0"
        cells_h.append(f'<div style="border:1px solid #333;padding:6px 10px;text-align:center;font-size:0.8rem;background:#ddd;">{html.escape(h)}</div>')
        cells_d.append(f'<div style="border:1px solid #333;padding:8px 10px;text-align:center;font-size:1.2rem;background:{bg};font-weight:bold;">{html.escape(d)}</div>')
    n = len(headers)
    grid_h = f'<div style="display:grid;grid-template-columns:repeat({n},1fr);max-width:{n*64}px;">{"".join(cells_h)}</div>'
    grid_d = f'<div style="display:grid;grid-template-columns:repeat({n},1fr);max-width:{n*64}px;">{"".join(cells_d)}</div>'
    return _wrap(grid_h + grid_d, note)


# --------------------------------------------------------------------- clock
def clock_face(hour24: int, minute: int, note: str | None = None) -> str:
    hour = hour24 % 12
    minute_angle = minute * 6 - 90
    hour_angle = (hour * 30 + minute * 0.5) - 90
    import math

    def point(cx, cy, r, angle_deg):
        a = math.radians(angle_deg)
        return cx + r * math.cos(a), cy + r * math.sin(a)

    cx, cy = 90, 90
    mx, my = point(cx, cy, 62, minute_angle)
    hx, hy = point(cx, cy, 40, hour_angle)
    ticks = []
    for i in range(12):
        ang = math.radians(i * 30 - 90)
        x1, y1 = cx + 72 * math.cos(ang), cy + 72 * math.sin(ang)
        x2, y2 = cx + 78 * math.cos(ang), cy + 78 * math.sin(ang)
        ticks.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#333" stroke-width="2"/>')
    svg = (
        f'<svg width="180" height="180" viewBox="0 0 180 180">'
        f'<circle cx="{cx}" cy="{cy}" r="80" fill="#fff" stroke="#222" stroke-width="3"/>'
        f'{"".join(ticks)}'
        f'<line x1="{cx}" y1="{cy}" x2="{hx:.1f}" y2="{hy:.1f}" stroke="#111" stroke-width="5" stroke-linecap="round"/>'
        f'<line x1="{cx}" y1="{cy}" x2="{mx:.1f}" y2="{my:.1f}" stroke="#111" stroke-width="3" stroke-linecap="round"/>'
        f'<circle cx="{cx}" cy="{cy}" r="4" fill="#111"/>'
        f'</svg>'
    )
    return _wrap(svg, note)


# ------------------------------------------------------------------ hint list
def hint_list(steps: list[str], note: str | None = None) -> str:
    items = "".join(f"<li style='margin-bottom:6px;'>{s}</li>" for s in steps)
    return _wrap(f'<ol style="margin:0;padding-left:1.3em;">{items}</ol>', note)


def fact_list(lines: list[str], note: str | None = None) -> str:
    items = "".join(f"<div style='margin-bottom:4px;font-size:1.05rem;'>{s}</div>" for s in lines)
    return _wrap(items, note)
