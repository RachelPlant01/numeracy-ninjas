"""Reusable visual-scaffold builders.

Each function returns a self-contained HTML/SVG snippet (string) styled to
loosely echo the look of the Numeracy Ninjas scaffolded worksheets (ten
frames, number-line jumps, bar models, place-value grids, clock faces) plus
a plain worked-steps hint list for skills that don't have a natural picture.
"""
from __future__ import annotations

import html
import math
import random


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
    jumps: list[tuple[float, float, str, bool]] | None = None,
    circle: float | None = None,
    hide_value: float | None = None,
    note: str | None = None,
    width: int = 640,
) -> str:
    """A number line, zebra-shaded in blocks of 5 so counts are easier to
    "see" without counting every tick one by one.

    `jumps` is a list of (from, to, label, dashed) — set `dashed=True` (and
    label="?") for a jump whose size is the thing the pupil must work out,
    so the scaffold never prints the answer itself. `circle` highlights a
    landmark value that's already given in the question; `hide_value` blanks
    out a tick's printed number (draws an empty box instead) for a position
    on the line that *is* the unknown being solved for.
    """
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

    # zebra-shade in blocks of 5 (two alternating bands) behind everything else
    band_colors = ["#eaf2fd", "#fdf3e2"]
    block = math.floor(min_v / 5) * 5
    i = 0
    while block < max_v:
        x0 = x(max(block, min_v))
        x1 = x(min(block + 5, max_v))
        svg_parts.append(f'<rect x="{x0:.1f}" y="{y_line-34}" width="{max(0, x1-x0):.1f}" height="60" fill="{band_colors[i % 2]}"/>')
        block += 5
        i += 1

    svg_parts.append(
        f'<line x1="{pad}" y1="{y_line}" x2="{width - pad}" y2="{y_line}" '
        f'stroke="#222" stroke-width="2" marker-end="url(#arrow)"/>'
    )
    svg_parts.append(
        '<defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="4" refY="4" '
        'orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#222"/></marker></defs>'
    )
    step = 1 if n <= 20 else max(1, n // 20)
    tick_values = set()
    v = min_v
    while v <= max_v:
        tick_values.add(v)
        v += step
    # `circle`/`hide_value` mark a specific value that must be visible no
    # matter where it falls — inject it as an extra tick if the regular
    # step would otherwise skip straight past it.
    for special in (circle, hide_value):
        if special is not None and min_v <= special <= max_v:
            tick_values.add(special)
    for v in sorted(tick_values):
        xv = x(v)
        on5 = v % 5 == 0
        tick_h = 9 if on5 else 6
        tick_w = 2.5 if on5 else 1.5
        svg_parts.append(f'<line x1="{xv}" y1="{y_line-tick_h}" x2="{xv}" y2="{y_line+tick_h}" stroke="#222" stroke-width="{tick_w}"/>')
        weight = "bold" if on5 else "normal"
        if hide_value is not None and abs(v - hide_value) < 1e-9:
            svg_parts.append(
                f'<rect x="{xv-11:.1f}" y="{y_line+14}" width="22" height="18" rx="3" '
                f'fill="#fff" stroke="#c0392b" stroke-width="2"/>'
            )
        elif circle is not None and abs(v - circle) < 1e-9:
            svg_parts.append(f'<circle cx="{xv}" cy="{y_line+22}" r="13" fill="none" stroke="#c0392b" stroke-width="2"/>')
            svg_parts.append(f'<text x="{xv}" y="{y_line+27}" text-anchor="middle" font-size="13" fill="#c0392b" font-weight="bold">{v:g}</text>')
        else:
            svg_parts.append(f'<text x="{xv}" y="{y_line+24}" text-anchor="middle" font-size="13" fill="#222" font-weight="{weight}">{v:g}</text>')
        v += step

    colors = ["#2e6da4", "#c0392b", "#27ae60", "#8e44ad"]
    if jumps:
        for i, (a, b, label, dashed) in enumerate(jumps):
            color = colors[i % len(colors)]
            xa, xb = x(a), x(b)
            mid = (xa + xb) / 2
            arc_h = 34 + 18 * i
            dash = 'stroke-dasharray="5,4"' if dashed else ""
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


def ten_frames_multi(known: int, total: int) -> str:
    """As many ten-frames as needed to hold `total`, filled solid up to
    `known` and then dashed (countable) the rest of the way — a multi-frame
    version of ten_frame_pair for totals bigger than 20, so a two-digit
    number doesn't get silently clipped to a single frame."""
    n_frames = max(1, math.ceil(total / 10))

    def one_frame(base: int) -> str:
        cells = []
        for i in range(10):
            g = base + i
            if g < known:
                dot = '<circle cx="19" cy="19" r="13" fill="#111"/>'
            elif g < total:
                dot = '<circle cx="19" cy="19" r="13" fill="none" stroke="#999" stroke-width="2" stroke-dasharray="3,3"/>'
            else:
                dot = ""
            cells.append(
                f'<div style="width:38px;height:38px;border:1px solid #333;'
                f'display:flex;align-items:center;justify-content:center;">'
                f'<svg width="38" height="38">{dot}</svg></div>'
            )
        row0, row1 = "".join(cells[0:5]), "".join(cells[5:10])
        return (
            f'<div style="display:inline-grid;grid-template-columns:repeat(5,38px);'
            f'grid-template-rows:repeat(2,38px);width:190px;">{row0}{row1}</div>'
        )

    frames = "".join(one_frame(f * 10) for f in range(n_frames))
    inner = f'<div style="display:flex;gap:10px;flex-wrap:wrap;">{frames}</div>'
    return _wrap(inner)


def double_frame(n: int, note: str | None = None) -> str:
    """A single ten-frame (5 columns, 2 rows). The top row holds `n` solid
    dots; the bottom row holds `n` greyed-out dots directly underneath —
    same column, same count — so doubling reads as "this row, and the same
    again below it" rather than a plain count. `n` must be 1-5 so both rows
    fit within the frame's 5 columns."""
    cells = []
    for i in range(10):
        row, col = divmod(i, 5)
        if col < n and row == 0:
            dot = '<circle cx="19" cy="19" r="13" fill="#111"/>'
        elif col < n and row == 1:
            dot = '<circle cx="19" cy="19" r="13" fill="none" stroke="#999" stroke-width="2" stroke-dasharray="3,3"/>'
        else:
            dot = ""
        cells.append(
            '<div style="width:38px;height:38px;border:1px solid #333;'
            'display:flex;align-items:center;justify-content:center;">'
            f'<svg width="38" height="38">{dot}</svg></div>'
        )
    row0 = "".join(cells[0:5])
    row1 = "".join(cells[5:10])
    inner = (
        '<div style="display:inline-grid;grid-template-columns:repeat(5,38px);'
        f'grid-template-rows:repeat(2,38px);width:190px;">{row0}{row1}</div>'
    )
    return _wrap(inner, note)


_GROUP_PALETTE = [
    ("#4fa8e8", "#1c6fa8"),
    ("#e8544f", "#a8231c"),
    ("#f2a541", "#b9740a"),
    ("#5cb85c", "#3d8b3d"),
    ("#a15fd1", "#6a2f96"),
]


def repeated_groups(n: int, times: int) -> str:
    """`times` separate towers of `n` stacked cells (each holding a dot),
    all the same colour and placed side by side — a direct picture of the
    repeated addition n + n + ... (`times` times), one tower per addend."""
    fill, stroke = random.choice(_GROUP_PALETTE)
    cell = 34
    dot_size = cell - 12
    dot = (
        f'<svg width="{dot_size}" height="{dot_size}">'
        f'<circle cx="{dot_size / 2}" cy="{dot_size / 2}" r="{dot_size / 2 - 2}" '
        f'fill="none" stroke="#000" stroke-width="2"/></svg>'
    )
    cell_html = (
        f'<div style="width:{cell}px;height:{cell}px;background:{fill};'
        f'border:2px solid {stroke};box-sizing:border-box;'
        f'display:flex;align-items:center;justify-content:center;">{dot}</div>'
    )
    tower = (
        f'<div style="display:flex;flex-direction:column;">'
        + cell_html * n + "</div>"
    )
    towers = "".join(f'<div style="margin-right:16px;">{tower}</div>' for _ in range(times))
    inner = f'<div style="display:flex;align-items:flex-end;">{towers}</div>'
    return _wrap(inner)


# ---------------------------------------------------------------- dienes blocks
_DIENES_UNIT = 18  # a ten-rod is exactly 10 of these squares laid end to end


def _dienes_rod(segments: int = 10, cut: bool = False) -> str:
    """A ten-rod (or, with fewer segments, a rod that's been broken off
    part-way — used for a ten split in half). `cut` draws a dashed line at
    the broken end."""
    u = _DIENES_UNIT
    w = u * segments
    svg = [
        f'<svg width="{w+2}" height="{u+2}" viewBox="0 0 {w+2} {u+2}">',
        f'<rect x="1" y="1" width="{w}" height="{u}" rx="2" fill="#4a90d9" stroke="#2c5d8a"/>',
    ]
    svg += [f'<line x1="{1+u*i}" y1="1" x2="{1+u*i}" y2="{u+1}" stroke="#ffffff"/>' for i in range(1, segments)]
    if cut:
        svg.append(f'<line x1="{w+1}" y1="0" x2="{w+1}" y2="{u+2}" stroke="#333" stroke-width="2" stroke-dasharray="3,2"/>')
    svg.append("</svg>")
    return "".join(svg)


def _dienes_rod_greyed() -> str:
    """A ten-rod drawn hollow and dashed, for the part of a number that's
    being taken away rather than kept."""
    u = _DIENES_UNIT
    w = u * 10
    svg = [
        f'<svg width="{w+2}" height="{u+2}" viewBox="0 0 {w+2} {u+2}">',
        f'<rect x="1" y="1" width="{w}" height="{u}" rx="2" fill="#e4e4e4" stroke="#999" stroke-width="1.5" stroke-dasharray="4,3"/>',
    ]
    svg += [f'<line x1="{1+u*i}" y1="1" x2="{1+u*i}" y2="{u+1}" stroke="#ffffff"/>' for i in range(1, 10)]
    svg.append("</svg>")
    return "".join(svg)


def _dienes_cube() -> str:
    u = _DIENES_UNIT
    return (
        f'<svg width="{u+2}" height="{u+2}" viewBox="0 0 {u+2} {u+2}">'
        f'<rect x="1" y="1" width="{u}" height="{u}" rx="2" fill="#f2a541" stroke="#b9740a"/>'
        "</svg>"
    )


def _dienes_split_cube() -> str:
    """A unit cube cut in half by a dashed line — for an odd units digit
    that can't be shared out evenly."""
    u = _DIENES_UNIT
    half = u / 2
    return (
        f'<svg width="{u+2}" height="{u+2}" viewBox="0 0 {u+2} {u+2}">'
        f'<rect x="1" y="1" width="{half}" height="{u}" fill="#f2a541" stroke="#b9740a"/>'
        f'<rect x="{1+half}" y="1" width="{half}" height="{u}" fill="none" stroke="#b9740a"/>'
        f'<line x1="{1+half}" y1="0" x2="{1+half}" y2="{u+2}" stroke="#333" stroke-width="2" stroke-dasharray="3,2"/>'
        "</svg>"
    )


def _dienes_cube_dashed() -> str:
    """A hollow, dashed unit cube — for a count that's there to be worked
    out (and counted) rather than one that's already known. Sized to
    exactly `_DIENES_UNIT`, matching one rod segment's width, so a loose
    cube reads as the same size as the ones making up a ten-rod rather
    than looking oversized next to them."""
    u = _DIENES_UNIT
    return (
        f'<svg width="{u}" height="{u}" viewBox="0 0 {u} {u}">'
        f'<rect x="1" y="1" width="{u - 2}" height="{u - 2}" rx="2" fill="none" stroke="#999" stroke-width="2" stroke-dasharray="3,3"/>'
        "</svg>"
    )


def _dienes_hundred_flat() -> str:
    """A 10x10 flat — ten ten-rods fused into a square — for when ten rods
    are grouped together as a hundred."""
    u = _DIENES_UNIT
    w = u * 10
    lines = []
    for i in range(1, 10):
        lines.append(f'<line x1="{1+u*i}" y1="1" x2="{1+u*i}" y2="{w+1}" stroke="#ffffff"/>')
        lines.append(f'<line x1="1" y1="{1+u*i}" x2="{w+1}" y2="{1+u*i}" stroke="#ffffff"/>')
    return (
        f'<svg width="{w+2}" height="{w+2}" viewBox="0 0 {w+2} {w+2}">'
        f'<rect x="1" y="1" width="{w}" height="{w}" rx="2" fill="#5cb85c" stroke="#3d8b3d"/>'
        + "".join(lines) + "</svg>"
    )


def _dienes_row(n: int) -> str:
    tens, ones = divmod(n, 10)
    rod = _dienes_rod()
    cube = _dienes_cube()
    rods_html = "".join(f'<div>{rod}</div>' for _ in range(tens))
    ones_html = ""
    if ones:
        # group in fives (like the ten-frames elsewhere) so the count is
        # easy to see at a glance instead of a plain row to tally up
        first_group = "".join(cube for _ in range(min(ones, 5)))
        groups = [f'<div style="display:flex;gap:2px;">{first_group}</div>']
        if ones > 5:
            second_group = "".join(cube for _ in range(ones - 5))
            groups.append(f'<div style="display:flex;gap:2px;">{second_group}</div>')
        ones_html = f'<div style="display:flex;gap:10px;margin-top:4px;">{"".join(groups)}</div>'
    return f'<div style="display:flex;flex-direction:column;gap:3px;">{rods_html}{ones_html}</div>'


def _dienes_full(n: int) -> str:
    """Base-ten blocks for any `n`, with every ten ten-rods regrouped into
    a hundred-flat — so a number that crosses 100 reads as flats + rods +
    cubes instead of an unwieldy run of loose rods."""
    hundreds, rem = divmod(n, 100)
    tens, ones = divmod(rem, 10)
    parts = []
    if hundreds:
        flats = "".join(f'<div>{_dienes_hundred_flat()}</div>' for _ in range(hundreds))
        parts.append(f'<div style="display:flex;gap:6px;flex-wrap:wrap;">{flats}</div>')
    if tens:
        rods = "".join(f'<div>{_dienes_rod()}</div>' for _ in range(tens))
        parts.append(f'<div style="display:flex;flex-direction:column;gap:3px;">{rods}</div>')
    if ones:
        cube = _dienes_cube()
        first_group = "".join(cube for _ in range(min(ones, 5)))
        groups = [f'<div style="display:flex;gap:2px;">{first_group}</div>']
        if ones > 5:
            groups.append(f'<div style="display:flex;gap:2px;">{"".join(cube for _ in range(ones - 5))}</div>')
        parts.append(f'<div style="display:flex;gap:10px;">{"".join(groups)}</div>')
    if not parts:
        parts.append("<div></div>")
    return f'<div style="display:flex;flex-direction:column;gap:8px;">{"".join(parts)}</div>'


def double_dienes(n: int) -> str:
    """Base-ten (Dienes) blocks for a two-digit number, with a second,
    identical set of blocks directly underneath — no caption, just the two
    matching sets of blocks so doubling reads as "this, and the same
    again"."""
    row = _dienes_row(n)
    inner = f'<div style="display:flex;flex-direction:column;gap:16px;">{row}{row}</div>'
    return _wrap(inner)


def dienes_add_tens(n: int, m: int) -> str:
    """`n`'s base-ten blocks, then `m`'s (a multiple of ten, so rods only)
    stacked directly underneath — each regrouped into hundred-flats where
    it has ten or more ten-rods, so crossing 100 is shown as a flat rather
    than an unwieldy row of loose rods."""
    top = _dienes_full(n)
    bottom = _dienes_full(m)
    inner = f'<div style="display:flex;flex-direction:column;gap:16px;">{top}{bottom}</div>'
    return _wrap(inner)


def dienes_subtract_tens(n: int, m: int) -> str:
    """`n` built in base-ten blocks, with the `m` worth of ten-rods being
    taken away drawn hollow and dashed instead of removed outright — so
    the whole starting number stays visible, with the part that's leaving
    clearly marked. `m` must be a multiple of ten no larger than n's tens
    digit alone, so a hundred-flat is never partially greyed."""
    hundreds, rem = divmod(n, 100)
    tens, ones = divmod(rem, 10)
    grey_count = min(m // 10, tens)
    keep_count = tens - grey_count

    parts = []
    if hundreds:
        flats = "".join(f'<div>{_dienes_hundred_flat()}</div>' for _ in range(hundreds))
        parts.append(f'<div style="display:flex;gap:6px;flex-wrap:wrap;">{flats}</div>')
    if tens:
        rods = [f'<div>{_dienes_rod()}</div>' for _ in range(keep_count)]
        rods += [f'<div>{_dienes_rod_greyed()}</div>' for _ in range(grey_count)]
        parts.append(f'<div style="display:flex;flex-direction:column;gap:3px;">{"".join(rods)}</div>')
    if ones:
        cube = _dienes_cube()
        first_group = "".join(cube for _ in range(min(ones, 5)))
        groups = [f'<div style="display:flex;gap:2px;">{first_group}</div>']
        if ones > 5:
            groups.append(f'<div style="display:flex;gap:2px;">{"".join(cube for _ in range(ones - 5))}</div>')
        parts.append(f'<div style="display:flex;gap:10px;">{"".join(groups)}</div>')

    inner = f'<div style="display:flex;flex-direction:column;gap:8px;">{"".join(parts)}</div>'
    return _wrap(inner)


def halving_dienes(n: int) -> str:
    """Base-ten blocks for `n`, split into two equal (stacked) halves. A
    ten-rod that can't be shared out whole is cut into a half-rod (5
    segments) for each half; a leftover unit cube is likewise cut in half —
    so an uneven split is shown as a literal cut, not just a number."""
    tens, ones = divmod(n, 10)
    tens_half, tens_odd = divmod(tens, 2)
    ones_half, ones_odd = divmod(ones, 2)

    def one_half() -> str:
        rods = [_dienes_rod() for _ in range(tens_half)]
        if tens_odd:
            rods.append(_dienes_rod(segments=5, cut=True))
        rods_html = "".join(f"<div>{r}</div>" for r in rods)

        cubes = [_dienes_cube() for _ in range(ones_half)]
        if ones_odd:
            cubes.append(_dienes_split_cube())
        cubes_html = ""
        if cubes:
            first = "".join(cubes[:5])
            groups = [f'<div style="display:flex;gap:2px;">{first}</div>']
            if len(cubes) > 5:
                groups.append(f'<div style="display:flex;gap:2px;">{"".join(cubes[5:])}</div>')
            cubes_html = f'<div style="display:flex;gap:10px;margin-top:4px;">{"".join(groups)}</div>'

        return f'<div style="display:flex;flex-direction:column;gap:3px;">{rods_html}{cubes_html}</div>'

    half = one_half()
    inner = f'<div style="display:flex;flex-direction:column;gap:16px;">{half}{half}</div>'
    return _wrap(inner)


def _dienes_cube_row(cells: list[str]) -> str:
    if not cells:
        return ""
    first = "".join(cells[:5])
    groups = [f'<div style="display:flex;gap:2px;">{first}</div>']
    if len(cells) > 5:
        groups.append(f'<div style="display:flex;gap:2px;">{"".join(cells[5:])}</div>')
    return f'<div style="display:flex;gap:10px;margin-top:4px;">{"".join(groups)}</div>'


def dienes_partition_tens(tens_value: int, ones_value: int) -> str:
    """`tens_value`'s ten-rods, built solid (the given part), with
    `ones_value` hollow dashed cubes underneath standing in for the not-yet
    -found ones part — countable, like the ten-frame's dashed dots
    elsewhere, rather than an opaque placeholder."""
    rods = tens_value // 10
    rods_html = "".join(f'<div>{_dienes_rod()}</div>' for _ in range(rods))
    cubes_html = _dienes_cube_row([_dienes_cube_dashed() for _ in range(ones_value)])
    inner = f'<div style="display:flex;flex-direction:column;gap:3px;">{rods_html}{cubes_html}</div>'
    return _wrap(inner)


def dienes_partition_pair(a_tens: int, a_ones: int, b_tens: int, b_ones: int) -> str:
    """Two base-ten block rows stacked, one per addend — each built as
    solid ten-rods (the rounded-down tens) with that addend's leftover
    ones drawn as hollow dashed cubes underneath. Seeing both rows lets a
    pupil combine the two dashed groups to find the leftover to add back."""
    def one_number(tens: int, ones: int) -> str:
        rods_html = "".join(f'<div>{_dienes_rod()}</div>' for _ in range(tens // 10))
        cubes_html = _dienes_cube_row([_dienes_cube_dashed() for _ in range(ones)])
        return f'<div style="display:flex;flex-direction:column;gap:3px;">{rods_html}{cubes_html}</div>'

    row_a, row_b = one_number(a_tens, a_ones), one_number(b_tens, b_ones)
    inner = f'<div style="display:flex;flex-direction:column;gap:16px;">{row_a}{row_b}</div>'
    return _wrap(inner)


def dienes_partition_near(part: int, extra: int) -> str:
    """`part`'s base-ten blocks, built solid, with `extra` hollow dashed
    cubes tacked on — showing how many more (countable) reach the total,
    for a part that's only a small step away from it."""
    tens, ones = divmod(part, 10)
    rods_html = "".join(f'<div>{_dienes_rod()}</div>' for _ in range(tens))
    cells = [_dienes_cube() for _ in range(ones)] + [_dienes_cube_dashed() for _ in range(extra)]
    cubes_html = _dienes_cube_row(cells)
    inner = f'<div style="display:flex;flex-direction:column;gap:3px;">{rods_html}{cubes_html}</div>'
    return _wrap(inner)


# ------------------------------------------------------------- halving columns
def halving_columns(n: int) -> str:
    """Two matched columns (filled dots vs outline dots) showing `n` split
    into two equal groups. If `n` is odd, the leftover dot is drawn split
    down the middle by a dashed line — straddling both columns — instead of
    being dropped into one side, so a half-remainder is visible rather than
    implied."""
    half = n // 2
    odd = n % 2 == 1

    def full_dot() -> str:
        return '<svg width="28" height="28" viewBox="0 0 28 28"><circle cx="14" cy="14" r="11" fill="#e74c3c" stroke="#a72d1d" stroke-width="2"/></svg>'

    def empty_dot() -> str:
        return '<svg width="28" height="28" viewBox="0 0 28 28"><circle cx="14" cy="14" r="11" fill="none" stroke="#333" stroke-width="2"/></svg>'

    def split_dot() -> str:
        return (
            '<svg width="28" height="28" viewBox="0 0 28 28">'
            '<path d="M14,3 A11,11 0 0,0 14,25 Z" fill="#e74c3c" stroke="#a72d1d" stroke-width="2"/>'
            '<path d="M14,3 A11,11 0 0,1 14,25 Z" fill="none" stroke="#333" stroke-width="2"/>'
            '<line x1="14" y1="2" x2="14" y2="26" stroke="#333" stroke-width="2" stroke-dasharray="3,2"/>'
            "</svg>"
        )

    rows = [f'<div style="display:flex;gap:14px;">{full_dot()}{empty_dot()}</div>' for _ in range(half)]
    if odd:
        rows.append(split_dot())
    inner = f'<div style="display:flex;flex-direction:column;gap:4px;align-items:center;">{"".join(rows)}</div>'
    return _wrap(inner)


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


# ------------------------------------------------------------ near doubles
def near_doubles_dienes(lo: int, extra: int) -> str:
    """Base-ten blocks for `lo`, then the same rods and unit cubes again
    with `extra` highlighted cubes tacked on the end — so the larger
    addend reads as "the smaller one's blocks, plus a couple more" rather
    than two independently-built numbers whose relationship has to be
    inferred."""
    tens, ones = divmod(lo, 10)
    rod = _dienes_rod()
    cube = _dienes_cube()
    cube_hl = (
        f'<svg width="{_DIENES_UNIT+2}" height="{_DIENES_UNIT+2}" viewBox="0 0 {_DIENES_UNIT+2} {_DIENES_UNIT+2}">'
        f'<rect x="1" y="1" width="{_DIENES_UNIT}" height="{_DIENES_UNIT}" rx="2" fill="#e74c3c" stroke="#a72d1d"/>'
        "</svg>"
    )
    rods_html = "".join(f'<div>{rod}</div>' for _ in range(tens))

    def block(extra_count: int) -> str:
        cells = [cube for _ in range(ones)] + [cube_hl for _ in range(extra_count)]
        cubes_html = ""
        if cells:
            first = "".join(cells[:5])
            groups = [f'<div style="display:flex;gap:2px;">{first}</div>']
            if len(cells) > 5:
                groups.append(f'<div style="display:flex;gap:2px;">{"".join(cells[5:])}</div>')
            cubes_html = f'<div style="display:flex;gap:10px;margin-top:4px;">{"".join(groups)}</div>'
        return f'<div style="display:flex;flex-direction:column;gap:3px;">{rods_html}{cubes_html}</div>'

    row_lo = block(0)
    row_hi = block(extra)
    inner = f'<div style="display:flex;flex-direction:column;gap:16px;">{row_lo}{row_hi}</div>'
    return _wrap(inner)


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


# --------------------------------------------------------- column addition
def _chimney_svg(a: int, b: int, fill: bool, decimals: int = 0) -> str:
    """A "chimney sum": `a` and `b` stacked right-aligned with a `+` to
    the left and a line beneath, wide enough for any carried extra
    digit. `a` and `b` are always whole numbers — pass them scaled up
    (e.g. pence instead of pounds) and set `decimals` to how many of
    the rightmost digits are actually after a decimal point, and a
    point is drawn at that position in every row. When `fill` is False
    the space below the line is left blank for the pupil to write the
    total in; when True the total is worked out column by column, with
    any carry shown as a small digit above the column it was carried
    into."""
    a_str, b_str = str(a), str(b)
    total = a + b
    n = max(len(str(total)), decimals + 1)
    cell_w, row_h = 32, 36
    plus_pad = 34
    carry_h = 22 if fill else 0
    dot_gap = 10 if decimals else 0
    dot_col = n - decimals

    width = plus_pad + n * cell_w + dot_gap + 10
    height = carry_h + 3 * row_h + 12
    x0 = plus_pad

    y_carry = carry_h - 6
    y_a = carry_h + row_h - 8
    y_b = carry_h + 2 * row_h - 8
    y_line = carry_h + 2 * row_h + 6
    y_sum = y_line + row_h - 6

    def col_x(i: int) -> float:
        shift = dot_gap if i >= dot_col else 0
        return x0 + i * cell_w + shift + cell_w / 2

    dot_x = x0 + dot_col * cell_w + dot_gap / 2

    svg = [
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
        f'xmlns="http://www.w3.org/2000/svg" font-family="inherit">'
    ]
    a_pad, b_pad = a_str.rjust(n), b_str.rjust(n)
    for i, ch in enumerate(a_pad):
        if ch != " ":
            svg.append(f'<text x="{col_x(i)}" y="{y_a}" text-anchor="middle" font-size="22" font-weight="bold" fill="#222">{ch}</text>')
    for i, ch in enumerate(b_pad):
        if ch != " ":
            svg.append(f'<text x="{col_x(i)}" y="{y_b}" text-anchor="middle" font-size="22" font-weight="bold" fill="#222">{ch}</text>')
    svg.append(f'<text x="{x0 - 20}" y="{y_b}" text-anchor="middle" font-size="22" font-weight="bold" fill="#222">+</text>')
    svg.append(f'<line x1="{x0 - 6}" y1="{y_line}" x2="{x0 + n * cell_w + dot_gap}" y2="{y_line}" stroke="#222" stroke-width="2.5"/>')
    if decimals:
        svg.append(f'<text x="{dot_x}" y="{y_a}" text-anchor="middle" font-size="22" font-weight="bold" fill="#222">.</text>')
        svg.append(f'<text x="{dot_x}" y="{y_b}" text-anchor="middle" font-size="22" font-weight="bold" fill="#222">.</text>')

    if fill:
        carry = 0
        carry_in_by_col = [0] * n
        results = []
        for i in range(n - 1, -1, -1):
            da = int(a_pad[i]) if a_pad[i] != " " else 0
            db = int(b_pad[i]) if b_pad[i] != " " else 0
            carry_in_by_col[i] = carry
            s = da + db + carry
            digit, carry = s % 10, s // 10
            results.append((i, digit))
        for i, digit in results:
            svg.append(f'<text x="{col_x(i)}" y="{y_sum}" text-anchor="middle" font-size="22" font-weight="bold" fill="#2e6da4">{digit}</text>')
            if carry_in_by_col[i] > 0:
                svg.append(f'<text x="{col_x(i)}" y="{y_carry}" text-anchor="middle" font-size="13" fill="#c0392b">{carry_in_by_col[i]}</text>')
        if decimals:
            svg.append(f'<text x="{dot_x}" y="{y_sum}" text-anchor="middle" font-size="22" font-weight="bold" fill="#2e6da4">.</text>')

    svg.append("</svg>")
    return "".join(svg)


def column_addition(a: int, b: int, demo_a: int, demo_b: int, decimals: int = 0) -> str:
    """The question's chimney sum (blank, ready to fill in), set well
    apart from a fully worked example of a different addition that
    exchanges (carries) at least once — the same side-by-side layout
    used for lattice multiplication and bus-stop division. Pass
    `decimals` through when `a`/`b`/the demo values are scaled-up
    decimals (see `_chimney_svg`)."""
    blank = _chimney_svg(a, b, fill=False, decimals=decimals)
    demo = _chimney_svg(demo_a, demo_b, fill=True, decimals=decimals)
    inner = (
        f'<div style="display:flex;align-items:flex-start;flex-wrap:wrap;">'
        f'<div>{blank}</div>'
        f'<div style="margin-left:90px;padding-left:24px;border-left:2px dashed #ccc;">{demo}</div>'
        f'</div>'
    )
    return _wrap(inner)


def _chimney_subtract_svg(a: int, b: int, fill: bool, decimals: int = 0) -> str:
    """A "chimney sum" for subtraction: `a` and `b` stacked right-
    aligned with a `-` to the left and a line beneath. `a` and `b` are
    always whole numbers — pass them scaled up (e.g. pence instead of
    pounds) and set `decimals` to how many of the rightmost digits are
    actually after a decimal point, and a point is drawn at that
    position in every row. When `fill` is False the space below the
    line is left blank; when True the difference is worked out column
    by column, showing an exchange (borrow) the way it's written by
    hand — the lending column's digit struck through with the reduced
    value above it, and a small "1" above the column that borrowed the
    ten."""
    n = max(len(str(a)), decimals + 1)
    a_pad, b_pad = str(a).rjust(n), str(b).rjust(n)
    cell_w, row_h = 32, 36
    plus_pad = 34
    note_h = 26 if fill else 0
    dot_gap = 10 if decimals else 0
    dot_col = n - decimals

    width = plus_pad + n * cell_w + dot_gap + 10
    height = note_h + 3 * row_h + 12
    x0 = plus_pad
    y_a = note_h + row_h - 8
    y_b = note_h + 2 * row_h - 8
    y_line = note_h + 2 * row_h + 6
    y_sum = y_line + row_h - 6

    def col_x(i: int) -> float:
        shift = dot_gap if i >= dot_col else 0
        return x0 + i * cell_w + shift + cell_w / 2

    dot_x = x0 + dot_col * cell_w + dot_gap / 2

    svg = [
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
        f'xmlns="http://www.w3.org/2000/svg" font-family="inherit">'
    ]

    borrowed_in = [0] * n
    borrowed_out = [0] * n
    diffs = [0] * n
    if fill:
        borrow = 0
        for i in range(n - 1, -1, -1):
            borrowed_in[i] = borrow
            ad = int(a_pad[i]) - borrow
            bd = int(b_pad[i]) if b_pad[i] != " " else 0
            if ad < bd:
                ad += 10
                borrowed_out[i] = 1
            diffs[i] = ad - bd
            borrow = borrowed_out[i]

    for i, ch in enumerate(a_pad):
        if ch == " ":
            continue
        x = col_x(i)
        svg.append(f'<text x="{x}" y="{y_a}" text-anchor="middle" font-size="22" font-weight="bold" fill="#222">{ch}</text>')
        if fill and borrowed_in[i]:
            svg.append(f'<line x1="{x - 9}" y1="{y_a + 6}" x2="{x + 9}" y2="{y_a - 16}" stroke="#c0392b" stroke-width="1.5"/>')
            svg.append(f'<text x="{x + 9}" y="{y_a - 18}" text-anchor="middle" font-size="13" fill="#c0392b">{int(ch) - 1}</text>')
        if fill and borrowed_out[i]:
            svg.append(f'<text x="{x - 10}" y="{y_a - 18}" text-anchor="middle" font-size="13" fill="#c0392b">1</text>')

    for i, ch in enumerate(b_pad):
        if ch != " ":
            svg.append(f'<text x="{col_x(i)}" y="{y_b}" text-anchor="middle" font-size="22" font-weight="bold" fill="#222">{ch}</text>')
    svg.append(f'<text x="{x0 - 20}" y="{y_b}" text-anchor="middle" font-size="22" font-weight="bold" fill="#222">-</text>')
    svg.append(f'<line x1="{x0 - 6}" y1="{y_line}" x2="{x0 + n * cell_w + dot_gap}" y2="{y_line}" stroke="#222" stroke-width="2.5"/>')
    if decimals:
        svg.append(f'<text x="{dot_x}" y="{y_a}" text-anchor="middle" font-size="22" font-weight="bold" fill="#222">.</text>')
        svg.append(f'<text x="{dot_x}" y="{y_b}" text-anchor="middle" font-size="22" font-weight="bold" fill="#222">.</text>')

    if fill:
        for i in range(n):
            svg.append(f'<text x="{col_x(i)}" y="{y_sum}" text-anchor="middle" font-size="22" font-weight="bold" fill="#2e6da4">{diffs[i]}</text>')
        if decimals:
            svg.append(f'<text x="{dot_x}" y="{y_sum}" text-anchor="middle" font-size="22" font-weight="bold" fill="#2e6da4">.</text>')

    svg.append("</svg>")
    return "".join(svg)


def column_subtraction(a: int, b: int, demo_a: int, demo_b: int, decimals: int = 0) -> str:
    """The question's chimney sum for subtraction (blank, ready to fill
    in), set well apart from a fully worked example of a different
    subtraction that exchanges (borrows) at least once — the same
    side-by-side layout used for the other written-method scaffolds.
    Pass `decimals` through when `a`/`b`/the demo values are scaled-up
    decimals (see `_chimney_subtract_svg`)."""
    blank = _chimney_subtract_svg(a, b, fill=False, decimals=decimals)
    demo = _chimney_subtract_svg(demo_a, demo_b, fill=True, decimals=decimals)
    inner = (
        f'<div style="display:flex;align-items:flex-start;flex-wrap:wrap;">'
        f'<div>{blank}</div>'
        f'<div style="margin-left:90px;padding-left:24px;border-left:2px dashed #ccc;">{demo}</div>'
        f'</div>'
    )
    return _wrap(inner)


# ------------------------------------------------------ bus stop division
def _bus_stop_svg(dividend: int, divisor: int, fill: bool) -> str:
    """A bus-stop (short) division layout: the divisor to the left of a
    bracket, the dividend's digits laid out under the bracket's
    horizontal line. When `fill` is False only this structure and the
    question's own numbers are drawn, with the quotient row left blank;
    when True the quotient is worked out digit by digit and any
    remainder carried into the next digit is shown as a small digit
    above it, the way it's written by hand."""
    digits = [int(c) for c in str(dividend)]
    n = len(digits)
    divisor_str = str(divisor)
    cell_w = 34
    left_pad = 16 + len(divisor_str) * 15
    width = left_pad + n * cell_w + 12
    height = 90

    y_quotient, y_hline = 20, 30
    y_bracket_top, y_bracket_bottom = y_hline, 72
    y_dividend = 58
    x_bracket = left_pad

    svg = [
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
        f'xmlns="http://www.w3.org/2000/svg" font-family="inherit">',
        f'<text x="{x_bracket - 10}" y="{y_dividend}" text-anchor="end" font-size="22" font-weight="bold" fill="#222">{divisor_str}</text>',
        f'<line x1="{x_bracket}" y1="{y_bracket_top}" x2="{x_bracket}" y2="{y_bracket_bottom}" stroke="#222" stroke-width="2.5"/>',
        f'<line x1="{x_bracket}" y1="{y_hline}" x2="{x_bracket + n * cell_w}" y2="{y_hline}" stroke="#222" stroke-width="2.5"/>',
    ]

    for i, d in enumerate(digits):
        x = x_bracket + i * cell_w + cell_w / 2
        svg.append(f'<text x="{x}" y="{y_dividend}" text-anchor="middle" font-size="22" font-weight="bold" fill="#222">{d}</text>')

    if fill:
        r = 0
        for i, d in enumerate(digits):
            carry_in = r
            current = carry_in * 10 + d
            qd, r = divmod(current, divisor)
            x = x_bracket + i * cell_w + cell_w / 2
            svg.append(f'<text x="{x}" y="{y_quotient}" text-anchor="middle" font-size="22" font-weight="bold" fill="#2e6da4">{qd}</text>')
            if i > 0 and carry_in > 0:
                svg.append(f'<text x="{x - 12}" y="{y_dividend - 16}" text-anchor="middle" font-size="12" fill="#c0392b">{carry_in}</text>')

    svg.append("</svg>")
    return "".join(svg)


def division_bus_stop(a: int, b: int, demo_a: int, demo_b: int) -> str:
    """The question's bus-stop division (blank, ready to fill in), set
    well apart from a fully worked example of a different division —
    the same side-by-side layout used for lattice multiplication."""
    blank = _bus_stop_svg(a, b, fill=False)
    demo = _bus_stop_svg(demo_a, demo_b, fill=True)
    inner = (
        f'<div style="display:flex;align-items:flex-start;flex-wrap:wrap;">'
        f'<div>{blank}</div>'
        f'<div style="margin-left:90px;padding-left:24px;border-left:2px dashed #ccc;">{demo}</div>'
        f'</div>'
    )
    return _wrap(inner)


# --------------------------------------------------------- lattice multiply
def _lattice_svg(a: int, b: int, fill: bool) -> str:
    """One lattice-multiplication grid: `a`'s digits along the top,
    `b`'s digits down the right, each cell split by a diagonal (bottom-
    left to top-right) into a tens triangle (upper-left) and a units
    triangle (lower-right). When `fill` is False the cells are left
    blank for a pupil to complete; when True every cell's partial
    product is written in."""
    a_digits = [int(c) for c in str(a)]
    b_digits = [int(c) for c in str(b)]
    cols, rows = len(a_digits), len(b_digits)
    cell = 44
    top_pad, right_pad = 32, 32
    width = cols * cell + right_pad
    height = top_pad + rows * cell

    svg = [
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
        f'xmlns="http://www.w3.org/2000/svg" font-family="inherit">'
    ]
    for c, d in enumerate(a_digits):
        x = c * cell + cell / 2
        svg.append(f'<text x="{x}" y="{top_pad - 8}" text-anchor="middle" font-size="20" font-weight="bold" fill="#222">{d}</text>')
    for r, d in enumerate(b_digits):
        y = top_pad + r * cell + cell / 2 + 7
        svg.append(f'<text x="{cols * cell + right_pad - 8}" y="{y}" text-anchor="middle" font-size="20" font-weight="bold" fill="#222">{d}</text>')

    for c in range(cols):
        for r in range(rows):
            x0, y0 = c * cell, top_pad + r * cell
            x1, y1 = x0 + cell, y0 + cell
            svg.append(f'<rect x="{x0}" y="{y0}" width="{cell}" height="{cell}" fill="#fff" stroke="#333" stroke-width="1.5"/>')
            svg.append(f'<line x1="{x0}" y1="{y1}" x2="{x1}" y2="{y0}" stroke="#333" stroke-width="1"/>')
            if fill:
                product = a_digits[c] * b_digits[r]
                tens, ones = divmod(product, 10)
                svg.append(f'<text x="{x0 + cell * 0.32}" y="{y0 + cell * 0.4}" text-anchor="middle" font-size="16" fill="#c0392b">{tens}</text>')
                svg.append(f'<text x="{x0 + cell * 0.68}" y="{y0 + cell * 0.82}" text-anchor="middle" font-size="16" fill="#2e6da4">{ones}</text>')
    svg.append("</svg>")
    return "".join(svg)


def _lattice_demo_svg(a: int, b: int) -> str:
    """A fully worked 2-digit x 2-digit lattice, including the diagonal
    sums read off around the outside — with a small carried digit
    written in above whichever sum received one, the way it's normally
    written by hand — rather than the sum's full working."""
    a_digits = [int(c) for c in str(a)]
    b_digits = [int(c) for c in str(b)]
    cols, rows = len(a_digits), len(b_digits)
    assert cols == 2 and rows == 2, "_lattice_demo_svg only lays out a 2x2 grid"
    cell = 44
    top_pad, right_pad, left_pad, bottom_pad = 32, 32, 34, 42
    grid_w, grid_h = cols * cell, rows * cell
    width = left_pad + grid_w + right_pad
    height = top_pad + grid_h + bottom_pad
    ox, oy = left_pad, top_pad

    svg = [
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
        f'xmlns="http://www.w3.org/2000/svg" font-family="inherit">',
    ]
    for c, d in enumerate(a_digits):
        x = ox + c * cell + cell / 2
        svg.append(f'<text x="{x}" y="{oy - 8}" text-anchor="middle" font-size="20" font-weight="bold" fill="#222">{d}</text>')
    for r, d in enumerate(b_digits):
        y = oy + r * cell + cell / 2 + 7
        svg.append(f'<text x="{ox + grid_w + right_pad - 8}" y="{y}" text-anchor="middle" font-size="20" font-weight="bold" fill="#222">{d}</text>')

    products: dict[tuple[int, int], tuple[int, int]] = {}
    for c in range(cols):
        for r in range(rows):
            x0, y0 = ox + c * cell, oy + r * cell
            x1, y1 = x0 + cell, y0 + cell
            svg.append(f'<rect x="{x0}" y="{y0}" width="{cell}" height="{cell}" fill="#fff" stroke="#333" stroke-width="1.5"/>')
            svg.append(f'<line x1="{x0}" y1="{y1}" x2="{x1}" y2="{y0}" stroke="#333" stroke-width="1"/>')
            product = a_digits[c] * b_digits[r]
            tens, ones = divmod(product, 10)
            products[(c, r)] = (tens, ones)
            svg.append(f'<text x="{x0 + cell * 0.32}" y="{y0 + cell * 0.4}" text-anchor="middle" font-size="16" fill="#c0392b">{tens}</text>')
            svg.append(f'<text x="{x0 + cell * 0.68}" y="{y0 + cell * 0.82}" text-anchor="middle" font-size="16" fill="#2e6da4">{ones}</text>')

    # Group each cell's two digits onto the diagonal they belong to
    # (0 = least significant, at the bottom-right corner) and sum each
    # diagonal, carrying any overflow into the next one up.
    n_diag = cols + rows
    diag_sums = [0] * n_diag
    for (c, r), (tens, ones) in products.items():
        dist = (cols - 1 - c) + (rows - 1 - r)
        diag_sums[dist] += ones
        diag_sums[dist + 1] += tens

    digits, carry_ins, carry = [], [], 0
    for total in diag_sums:
        carry_ins.append(carry)
        combined = total + carry
        digit, carry = combined % 10, combined // 10
        digits.append(digit)

    # For this 2x2 layout: diagonal 0 exits bottom-right, diagonal 1
    # exits at the bottom's internal gridline, diagonal 2 exits at the
    # left's internal gridline, diagonal 3 exits top-left.
    label_y = oy + grid_h + 24
    label_x = ox - 18
    anchors = [
        (ox + grid_w, label_y),
        (ox + cell, label_y),
        (label_x, oy + cell + 6),
        (label_x, oy + 6),
    ]
    for i in range(n_diag):
        x, y = anchors[i] if i < len(anchors) else anchors[-1]
        if carry_ins[i] > 0:
            svg.append(f'<text x="{x - 13}" y="{y - 12}" text-anchor="middle" font-size="12" fill="#c0392b">{carry_ins[i]}</text>')
        svg.append(f'<text x="{x}" y="{y}" text-anchor="middle" font-size="18" font-weight="bold" fill="#222">{digits[i]}</text>')

    svg.append("</svg>")
    return "".join(svg)


def lattice_multiplication(a: int, b: int, demo_a: int, demo_b: int) -> str:
    """The question's lattice grid (blank, ready to fill in), set well
    apart from a fully worked example of a different 2-digit x 2-digit
    calculation — including its diagonal sums, with a small carried
    digit shown wherever one occurs — so a pupil can see how the method
    goes before trying their own numbers, without mistaking the demo's
    digits for their own."""
    blank = _lattice_svg(a, b, fill=False)
    demo = _lattice_demo_svg(demo_a, demo_b)
    inner = (
        f'<div style="display:flex;align-items:flex-start;flex-wrap:wrap;">'
        f'<div>{blank}</div>'
        f'<div style="margin-left:90px;padding-left:24px;border-left:2px dashed #ccc;">{demo}</div>'
        f'</div>'
    )
    return _wrap(inner)


# ------------------------------------------------------------- hundred square
def hundred_square(a: int, b: int) -> str:
    """A 1-100 grid (10 per row) with cell `a` and cell `b` highlighted.
    When b = a + 10, b sits directly below a in the same column — showing
    that adding 10 just moves down one row."""
    cells = []
    for i in range(1, 101):
        bg, color = "#ffffff", "#222"
        if i == a:
            bg, color = "#e74c3c", "#ffffff"
        elif i == b:
            bg, color = "#2e6da4", "#ffffff"
        cells.append(
            f'<div style="width:26px;height:26px;display:flex;align-items:center;'
            f'justify-content:center;font-size:11px;border:1px solid #ccc;'
            f'background:{bg};color:{color};font-weight:{"bold" if i in (a, b) else "normal"};">{i}</div>'
        )
    grid = f'<div style="display:grid;grid-template-columns:repeat(10,26px);gap:1px;width:269px;">{"".join(cells)}</div>'
    return _wrap(grid)


# ------------------------------------------------------------ elapsed time
def elapsed_time_line(stops: list[tuple[int, int]], jump_labels: list[str]) -> str:
    """A "counting up" number line for elapsed time: `stops` are (hour24,
    minute) landmarks in order — start time, then each friendly waypoint
    (a round number of minutes, or the top of the hour), then the end
    time — joined by arced jumps labelled with `jump_labels` (one fewer
    than `stops`). Ticks are spaced evenly rather than to scale, matching
    how this strategy is normally drawn by hand."""
    n = len(stops)
    width = max(560, 130 * (n - 1) + 80)
    pad = 60
    usable = width - 2 * pad
    step_x = usable / max(1, n - 1)
    height = 150
    y_line = height - 40

    def fmt(h: int, m: int) -> str:
        h12 = h % 12
        if h12 == 0:
            h12 = 12
        suffix = "am" if h < 12 else "pm"
        return f"{h12}:{m:02d} {suffix}"

    svg = [
        f'<svg viewBox="0 0 {width} {height}" width="100%" height="{height}" '
        f'xmlns="http://www.w3.org/2000/svg" font-family="inherit">',
        f'<line x1="{pad}" y1="{y_line}" x2="{width - pad}" y2="{y_line}" '
        f'stroke="#222" stroke-width="2" marker-end="url(#arrow)"/>',
        '<defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="4" refY="4" '
        'orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#222"/></marker></defs>',
    ]
    xs = [pad + i * step_x for i in range(n)]
    for (h, m), xv in zip(stops, xs):
        svg.append(f'<line x1="{xv}" y1="{y_line - 9}" x2="{xv}" y2="{y_line + 9}" stroke="#222" stroke-width="2.5"/>')
        svg.append(
            f'<text x="{xv}" y="{y_line + 28}" text-anchor="middle" font-size="14" '
            f'font-weight="bold" fill="#222">{html.escape(fmt(h, m))}</text>'
        )
    colors = ["#2e6da4", "#c0392b", "#27ae60", "#8e44ad", "#d18a1b"]
    for i, label in enumerate(jump_labels):
        xa, xb = xs[i], xs[i + 1]
        mid = (xa + xb) / 2
        color = colors[i % len(colors)]
        arc_h = 34
        svg.append(
            f'<path d="M{xa},{y_line} Q{mid},{y_line - arc_h} {xb},{y_line}" '
            f'fill="none" stroke="{color}" stroke-width="2.5" marker-end="url(#arrow)"/>'
        )
        svg.append(
            f'<text x="{mid}" y="{y_line - arc_h - 6}" text-anchor="middle" font-size="13" '
            f'fill="{color}" font-weight="bold">{html.escape(label)}</text>'
        )
    svg.append("</svg>")
    return _wrap("".join(svg))


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
