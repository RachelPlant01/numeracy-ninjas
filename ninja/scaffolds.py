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
import re


CARD_STYLE = (
    "border:2px solid #2b2b2b;border-radius:10px;padding:12px 20px;"
    "background:#fafafa;margin:4px 0;box-sizing:border-box;"
)


def _wrap(inner: str, note: str | None = None) -> str:
    # `note` (a plain-English caption) is intentionally not rendered — the
    # scaffold should be the picture alone, not a worded explanation of it.
    return f'<div style="{CARD_STYLE}">{inner}</div>'


# ------------------------------------------------------- black and white
_HEX = re.compile(r"(?<![&\w])#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b")


def to_black_and_white(scaffold_html: str) -> str:
    """Greyscale version of any scaffold, for black-and-white printing or
    pupils who prefer it. Every hex colour is swapped for the grey of the
    same brightness, so light fills stay light, dark lines stay dark, and
    colours that differ in brightness (e.g. red vs yellow counters) stay
    distinguishable as different greys."""
    def grey(m):
        h = m.group(1)
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
        v = round(0.299 * r + 0.587 * g + 0.114 * b)
        return f"#{v:02x}{v:02x}{v:02x}"
    return _HEX.sub(grey, scaffold_html)


# ---------------------------------------------------------------- number line
def number_line(
    min_v: int,
    max_v: int,
    jumps: list[tuple[float, float, str, bool]] | None = None,
    circle: float | None = None,
    hide_value: float | list[float] | None = None,
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
    on the line that *is* the unknown being solved for — pass a single
    value, or a list when several positions (e.g. a chain of skip-counting
    landings) are all unknowns.
    """
    hide_values = [hide_value] if isinstance(hide_value, (int, float)) else list(hide_value or [])
    circles = [circle] if isinstance(circle, (int, float)) else list(circle or [])
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
    y_line = height - 40  # room underneath for circled values / blank boxes

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
    for special in (*circles, *hide_values):
        if special is not None and min_v <= special <= max_v:
            tick_values.add(special)
    for v in sorted(tick_values):
        xv = x(v)
        on5 = v % 5 == 0
        tick_h = 9 if on5 else 6
        tick_w = 2.5 if on5 else 1.5
        svg_parts.append(f'<line x1="{xv}" y1="{y_line-tick_h}" x2="{xv}" y2="{y_line+tick_h}" stroke="#222" stroke-width="{tick_w}"/>')
        weight = "bold" if on5 else "normal"
        if any(abs(v - hv) < 1e-9 for hv in hide_values):
            svg_parts.append(
                f'<rect x="{xv-11:.1f}" y="{y_line+14}" width="22" height="18" rx="3" '
                f'fill="#fff" stroke="#c0392b" stroke-width="2"/>'
            )
        elif any(abs(v - cv) < 1e-9 for cv in circles):
            cr = 13 if len(f"{v:g}") <= 2 else 17  # wider circle for 3-digit numbers
            svg_parts.append(f'<circle cx="{xv}" cy="{y_line+22}" r="{cr}" fill="none" stroke="#c0392b" stroke-width="2"/>')
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
            # Constant height for every jump — these are read as a chain of
            # equal-sized steps (e.g. skip-counting), so a staircase of
            # increasing arcs would misleadingly suggest growing jump sizes.
            arc_h = 34
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


def _rounding_number_line_core(lower: float, upper: float, fmt, fmt_mid) -> str:
    """Shared core for the two rounding-number-line variants below: a
    short line spanning exactly `lower` to `upper`, midpoint labelled as
    the "5 or more rounds up" landmark, with `fmt`/`fmt_mid` controlling
    how the end/mid labels are printed (decimal places vs. whole powers
    of ten read very differently). Deliberately never marks the actual
    value's position — see `rounding_number_line`'s docstring for why."""
    mid = (lower + upper) / 2
    width, height, pad = 420, 90, 50
    usable = width - 2 * pad

    def x(v: float) -> float:
        return pad + (v - lower) / (upper - lower) * usable

    y_line = height - 42
    xm = x(mid)

    parts = [
        f'<svg viewBox="0 0 {width} {height}" width="100%" height="{height}" '
        f'xmlns="http://www.w3.org/2000/svg" font-family="inherit">',
        f'<line x1="{pad}" y1="{y_line}" x2="{width-pad}" y2="{y_line}" stroke="#222" stroke-width="2"/>',
        f'<line x1="{pad}" y1="{y_line-9}" x2="{pad}" y2="{y_line+9}" stroke="#222" stroke-width="2.5"/>',
        f'<line x1="{width-pad}" y1="{y_line-9}" x2="{width-pad}" y2="{y_line+9}" stroke="#222" stroke-width="2.5"/>',
        f'<text x="{pad}" y="{y_line+28}" text-anchor="middle" font-size="15" font-weight="bold" fill="#222">{fmt(lower)}</text>',
        f'<text x="{width-pad}" y="{y_line+28}" text-anchor="middle" font-size="15" font-weight="bold" fill="#222">{fmt(upper)}</text>',
        f'<line x1="{xm}" y1="{y_line-6}" x2="{xm}" y2="{y_line+6}" stroke="#999" stroke-width="1.5"/>',
        f'<text x="{xm}" y="{y_line+24}" text-anchor="middle" font-size="11" fill="#999">{fmt_mid(mid)}</text>',
        "</svg>",
    ]
    return _wrap("".join(parts))


def rounding_number_line(value: float, dp: int) -> str:
    """A short number line spanning just the two values `value` could
    round to at `dp` decimal places (e.g. 23.64 to 23.65), with the
    midpoint labelled as the "5 or more rounds up" landmark. Deliberately
    does NOT mark `value`'s own position — plotting it would visually
    show which side of the midpoint it falls on, which is the answer;
    the pupil places it themselves."""
    scale = 10 ** dp
    lower = math.floor(value * scale) / scale
    upper = lower + 1 / scale
    return _rounding_number_line_core(lower, upper, lambda v: f"{v:.{dp}f}", lambda v: f"{v:.{dp+1}f}")


def _sig_fig_bounds(value: float, sig: int) -> tuple[float, float, int]:
    d = math.ceil(math.log10(abs(value))) if value != 0 else 1
    power = sig - d
    scale = 10 ** power
    lower = math.floor(value * scale) / scale
    upper = lower + 1 / scale
    return lower, upper, power


def rounding_number_line_sig_figs(value: float, sig: int) -> str:
    """As `rounding_number_line`, but spanning the two values `value`
    could round to at `sig` significant figures — the step between them
    is a whole power of ten (e.g. rounding 13270 to 1 s.f. spans 10000 to
    20000), not a decimal fraction, so bounds are shown as plain integers
    rather than with a fixed decimal-place count."""
    lower, upper, power = _sig_fig_bounds(value, sig)
    if power >= 0:
        fmt = fmt_mid = lambda v: f"{v:.{power}f}"
    else:
        fmt = fmt_mid = lambda v: f"{v:g}"
    return _rounding_number_line_core(lower, upper, fmt, fmt_mid)


def _number_line_with_value_core(lower: float, upper: float, value: float, fmt, fmt_mid=None) -> str:
    """Like `_rounding_number_line_core`, but DOES plot `value`'s own
    position — used only by the heavily-scaffolded sig-figs chart, where
    the chart above already gives away most of the structure (the zero
    columns are pre-filled), so showing exactly where the value sits is a
    deliberate extra level of support, not an inconsistency with the
    lighter-touch number lines elsewhere that hide it."""
    mid = (lower + upper) / 2
    fmt_mid = fmt_mid or fmt
    width, height, pad = 420, 110, 50
    usable = width - 2 * pad

    def x(v: float) -> float:
        return pad + (v - lower) / (upper - lower) * usable

    y_line = height - 42
    xm, xv = x(mid), x(value)

    parts = [
        f'<svg viewBox="0 0 {width} {height}" width="100%" height="{height}" '
        f'xmlns="http://www.w3.org/2000/svg" font-family="inherit">',
        f'<line x1="{pad}" y1="{y_line}" x2="{width-pad}" y2="{y_line}" stroke="#222" stroke-width="2"/>',
        f'<line x1="{pad}" y1="{y_line-9}" x2="{pad}" y2="{y_line+9}" stroke="#222" stroke-width="2.5"/>',
        f'<line x1="{width-pad}" y1="{y_line-9}" x2="{width-pad}" y2="{y_line+9}" stroke="#222" stroke-width="2.5"/>',
        f'<text x="{pad}" y="{y_line+28}" text-anchor="middle" font-size="15" font-weight="bold" fill="#222">{fmt(lower)}</text>',
        f'<text x="{width-pad}" y="{y_line+28}" text-anchor="middle" font-size="15" font-weight="bold" fill="#222">{fmt(upper)}</text>',
        f'<line x1="{xm}" y1="{y_line-6}" x2="{xm}" y2="{y_line+6}" stroke="#999" stroke-width="1.5"/>',
        f'<text x="{xm}" y="{y_line+24}" text-anchor="middle" font-size="11" fill="#999">{fmt_mid(mid)}</text>',
        f'<circle cx="{xv:.1f}" cy="{y_line}" r="6" fill="#c0392b"/>',
        f'<text x="{xv:.1f}" y="{y_line-14}" text-anchor="middle" font-size="14" font-weight="bold" fill="#c0392b">{value:g}</text>',
        "</svg>",
    ]
    return "".join(parts)


# --------------------------------------------------------------------- numicon
def _numicon_circle(dashed: bool) -> str:
    if dashed:
        return '<div style="width:26px;height:26px;border-radius:50%;background:none;border:2px dashed #999;"></div>'
    return '<div style="width:26px;height:26px;border-radius:50%;background:#fff;border:2px solid #333;"></div>'


def _numicon_plate(n: int, dashed: bool, plate_style: str) -> str:
    """A Numicon-style shape plate for `n`: a two-column grid of holes
    filled from the bottom, with an odd leftover hole centred on top —
    matching the shape-plate pattern used in Numicon resources."""
    pairs, odd = divmod(n, 2)
    rows = []
    if odd:
        rows.append(f'<div style="display:flex;justify-content:center;">{_numicon_circle(dashed)}</div>')
    for _ in range(pairs):
        rows.append(f'<div style="display:flex;gap:4px;justify-content:center;">{_numicon_circle(dashed)}{_numicon_circle(dashed)}</div>')
    width = 26 * 2 + 4 + 16
    return (
        f'<div style="{plate_style}border-radius:14px;padding:8px;display:flex;'
        f'flex-direction:column;gap:4px;width:{width}px;box-sizing:border-box;align-items:center;">'
        f'{"".join(rows)}</div>'
    )


def numicon_shape(n: int, color: str) -> str:
    """A solid, coloured Numicon-style shape plate for `n`."""
    return _numicon_plate(n, dashed=False, plate_style=f"background:{color};border:2px solid transparent;")


def numicon_shape_dashed(n: int) -> str:
    """A hollow, dashed Numicon-style shape plate for `n` — for a
    quantity that's there to be worked out, not one already known."""
    return _numicon_plate(n, dashed=True, plate_style="background:none;border:2px dashed #999;")


def numicon_bond(known: int, gap: int) -> str:
    """A solid, coloured Numicon shape for `known`, next to a hollow
    dashed one of the same style for the gap still to be worked out."""
    color = random.choice(["#f2a541", "#5cb85c", "#4a90d9", "#e74c3c", "#a15fd1"])
    inner = f'<div style="display:flex;align-items:flex-end;gap:16px;">{numicon_shape(known, color)}{numicon_shape_dashed(gap)}</div>'
    return _wrap(inner)


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


def bond_frame(first: int, second: int, target: int, unknown: str) -> str:
    """Five-frame (target ≤ 5) or ten-frame for a number-bond question
    `first + second = target`. `unknown` is "first", "second" or "total".
    When an addend is unknown, the given number is solid and the missing
    part is dashed (always solid-then-dashed, whichever side of the + the
    blank is on). When the total is unknown, both parts are solid in two
    different colours, so the pupil counts them all."""
    size = 5 if target <= 5 else 10
    if unknown == "total":
        cells = ["a"] * first + ["b"] * second
    else:
        given, gap = (second, first) if unknown == "first" else (first, second)
        cells = ["a"] * given + ["d"] * gap
    dots = {
        "a": '<circle cx="19" cy="19" r="13" fill="#111"/>',
        "b": '<circle cx="19" cy="19" r="13" fill="#a3c9f9" stroke="#2e6da4" stroke-width="2"/>',
        "d": '<circle cx="19" cy="19" r="13" fill="none" stroke="#999" stroke-width="2" stroke-dasharray="3,3"/>',
    }
    html_cells = "".join(
        '<div style="width:38px;height:38px;border:1px solid #333;display:flex;align-items:center;justify-content:center;">'
        f'<svg width="38" height="38">{dots[cells[i]] if i < len(cells) else ""}</svg></div>'
        for i in range(size)
    )
    rows = size // 5
    grid = (f'<div style="display:inline-grid;grid-template-columns:repeat(5,38px);'
            f'grid-template-rows:repeat({rows},38px);width:190px;">{html_cells}</div>')
    return _wrap(grid)


def bond_number_line(first: int, second: int, target: int, unknown: str) -> str:
    """Number line 0 → target for `first + second = target`, drawn as two
    hops above the line: 0 → first, then first → target. The hop for the
    unknown part is dashed and labelled "?"; known hops are solid and
    labelled with their size.
    - first + ☐ = target: "+first" then a dashed "?" hop; `first` circled.
    - ☐ + second = target: a dashed "?" hop then "+second"; the point
      between them is blanked.
    - first + second = ☐: "+first" then "+second"; the landing point is
      blanked.
    A zero-sized hop (e.g. 0 + 5) is left out."""
    end = target + 1  # one past the target, so the line's own end arrow doesn't sit on a hop's arrowhead
    hop1 = (0, first, "?" if unknown == "first" else f"+{first}", unknown == "first")
    hop2 = (first, target, "?" if unknown == "second" else f"+{second}", unknown == "second")
    jumps = [h for h in (hop1, hop2) if h[0] != h[1]]
    if unknown == "first":
        return number_line(0, end, jumps=jumps, hide_value=first)
    if unknown == "second":
        return number_line(0, end, jumps=jumps, circle=first)
    return number_line(0, end, jumps=jumps, circle=first, hide_value=target)


def bond_dice(first: int, second: int, target: int, unknown: str) -> str:
    """One die showing five pips, for number bonds to 5. The known part is
    solid black pips arranged as that number's own dice pattern (so 3
    looks like a real 3); the rest of the five pips are outlines only.
    - first + ☐ = 5 / ☐ + second = 5: the given number is black, the
      outlined pips are the part to find.
    - first + second = ☐: `first` black and `second` light blue (both
      known), and the pupil counts all the pips."""
    known = second if unknown == "first" else first
    centre, corners = (1, 1), [(0, 0), (2, 2), (2, 0), (0, 2)]
    black = ([centre] if known % 2 else []) + corners[: known - known % 2]
    rest = [pos for pos in [centre] + corners if pos not in black]
    if unknown == "total":
        rest_style = 'fill="#a3c9f9" stroke="#2e6da4" stroke-width="2"'
    else:
        rest_style = 'fill="none" stroke="#333" stroke-width="2"'
    pips = "".join(f'<circle cx="{18 + c * 22}" cy="{18 + r * 22}" r="7" fill="#111"/>' for c, r in black)
    pips += "".join(f'<circle cx="{18 + c * 22}" cy="{18 + r * 22}" r="7" {rest_style}/>' for c, r in rest)
    svg = (
        '<svg width="84" height="84" viewBox="0 0 80 80" style="display:block;margin:0 auto;">'
        f'<rect x="3" y="3" width="74" height="74" rx="12" fill="#fff" stroke="#333" stroke-width="2.5"/>{pips}</svg>'
    )
    return _wrap(svg)


def bond_dice_ok(target: int) -> bool:
    """The single-die scaffold only fits number bonds to 5."""
    return target == 5


def numicon_bond_to_target(known: int, target: int) -> str:
    """Numicon plates for "☐ + known = target" (target a multiple of 10):
    `known` as solid coloured plates (a 10-plate per ten, then the
    rest), then the gap as dashed plates — first the plate that makes
    up the next ten, then dashed 10-plates up to the target."""
    color = "#4a90d9"
    k_tens, k_ones = divmod(known, 10)
    plates = [numicon_shape(10, color) for _ in range(k_tens)]
    if k_ones:
        plates.append(numicon_shape(k_ones, color))
    gap = target - known
    fill_ten = (10 - k_ones) % 10
    if fill_ten:
        plates.append(numicon_shape_dashed(fill_ten))
        gap -= fill_ten
    plates += [numicon_shape_dashed(10) for _ in range(gap // 10)]
    inner = f'<div style="display:flex;align-items:flex-end;gap:12px;flex-wrap:wrap;">{"".join(plates)}</div>'
    return _wrap(inner)


def rekenrek(known: int, rows: int = 2) -> str:
    """A rekenrek (bead rack): `rows` wires of 10 beads, each wire 5 red
    then 5 white. `known` beads are pushed to the left — filling the top
    wire first — and the rest sit at the right-hand end, so the gap to
    the full rack is the beads left on the right."""
    bead_r, step, gap_w = 11, 24, 70
    left_x, wire_len = 30, 10 * step + gap_w
    width, height = left_x * 2 + wire_len, 30 + rows * 44
    red, white = "#e74c3c", "#ffffff"
    parts = [
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">',
        f'<rect x="8" y="6" width="{width - 16}" height="{height - 12}" rx="8" fill="none" stroke="#8a6d3b" stroke-width="5"/>',
    ]
    for r in range(rows):
        y = 34 + r * 44
        on_left = max(0, min(10, known - r * 10))
        parts.append(f'<line x1="10" y1="{y}" x2="{width - 10}" y2="{y}" stroke="#555" stroke-width="2"/>')
        for i in range(10):
            x = left_x + i * step + (gap_w if i >= on_left else 0) + step / 2
            fill = red if i < 5 else white
            parts.append(f'<circle cx="{x:.1f}" cy="{y}" r="{bead_r}" fill="{fill}" stroke="#333" stroke-width="1.5"/>')
    parts.append("</svg>")
    return _wrap("".join(parts))


def dice_fives_bond(known: int, target: int) -> str:
    """For "☐ + known = target" with target a multiple of 5 (e.g. 20 →
    four dice): a row of dice each showing five pips. `known` pips are
    solid black, filling the dice left to right (each part-filled die
    uses that number's own dice pattern); every other pip is an outline,
    for the pupil to count."""
    centre, corners = (1, 1), [(0, 0), (2, 2), (2, 0), (0, 2)]
    dice = []
    for d in range(target // 5):
        k = max(0, min(5, known - d * 5))
        black = ([centre] if k % 2 else []) + corners[: k - k % 2]
        rest = [pos for pos in [centre] + corners if pos not in black]
        pips = "".join(f'<circle cx="{18 + c * 22}" cy="{18 + r * 22}" r="7" fill="#111"/>' for c, r in black)
        pips += "".join(f'<circle cx="{18 + c * 22}" cy="{18 + r * 22}" r="7" fill="none" stroke="#333" stroke-width="2"/>' for c, r in rest)
        dice.append(
            '<svg width="72" height="72" viewBox="0 0 80 80">'
            f'<rect x="3" y="3" width="74" height="74" rx="12" fill="#fff" stroke="#333" stroke-width="2.5"/>{pips}</svg>'
        )
    return _wrap(f'<div style="display:flex;gap:12px;flex-wrap:wrap;">{"".join(dice)}</div>')


def _numicon_plate_svg(n: int, fill: str | None, dashed: bool = False, c: int = 30) -> str:
    """One real-shape Numicon plate for `n` as its own small SVG. `dashed`
    draws it hollow with a dashed outline and dashed holes — for an amount
    that's there to be worked out."""
    r_hole, pad = c / 3, 4
    cells = set(_numicon_cells(n, False, 0))
    rows = (n + 1) // 2
    W, H = 2 * c + 2 * pad, rows * c + 2 * pad

    def xy(col, row):
        return pad + col * c, pad + (rows - 1 - row) * c

    edge_style = 'stroke="#999" stroke-width="2" stroke-dasharray="5,4"' if dashed else 'stroke="#333" stroke-width="2.5" stroke-linecap="round"'
    hole_style = 'fill="none" stroke="#999" stroke-width="1.5" stroke-dasharray="3,3"' if dashed else 'fill="#fff" stroke="#333" stroke-width="1.5"'
    parts = [f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">']
    if not dashed:
        for col, row in cells:
            x, y = xy(col, row)
            parts.append(f'<rect x="{x}" y="{y}" width="{c}" height="{c}" fill="{fill}"/>')
    for col, row in cells:
        x, y = xy(col, row)
        for (dc, dr), (x1, y1, x2, y2) in {
            (0, 1): (x, y, x + c, y), (0, -1): (x, y + c, x + c, y + c),
            (-1, 0): (x, y, x, y + c), (1, 0): (x + c, y, x + c, y + c),
        }.items():
            if (col + dc, row + dr) not in cells:
                parts.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" {edge_style}/>')
    for col, row in cells:
        x, y = xy(col, row)
        parts.append(f'<circle cx="{x + c / 2}" cy="{y + c / 2}" r="{r_hole}" {hole_style}/>')
    parts.append("</svg>")
    return "".join(parts)


def numicon_bond_real(first: int, second: int, unknown: str) -> str:
    """Number bonds with real Numicon shapes. An unknown addend: the given
    number as a solid plate (its Numicon colour), the missing part as a
    dashed plate. Unknown total: both plates solid. A 0 part is left out."""
    if unknown == "total":
        plates = [_numicon_plate_svg(v, NUMICON_COLOURS[v]) for v in (first, second) if v]
    else:
        given, gap = (second, first) if unknown == "first" else (first, second)
        plates = ([_numicon_plate_svg(given, NUMICON_COLOURS[given])] if given else []) + \
                 ([_numicon_plate_svg(gap, None, dashed=True)] if gap else [])
    return _wrap(f'<div style="display:flex;align-items:flex-end;gap:16px;">{"".join(plates)}</div>')


def _dienes_cube_blue() -> str:
    u = _DIENES_UNIT
    return (f'<svg width="{u+2}" height="{u+2}" viewBox="0 0 {u+2} {u+2}">'
            f'<rect x="1" y="1" width="{u}" height="{u}" rx="2" fill="#a3c9f9" stroke="#2e6da4"/></svg>')


def dienes_bond(first: int, second: int, unknown: str) -> str:
    """Number bonds within 10 with Dienes unit cubes (grouped in fives).
    Unknown addend: given cubes solid orange, missing cubes dashed.
    Unknown total: first part orange, second part light blue, both solid."""
    if unknown == "total":
        cells = [_dienes_cube() for _ in range(first)] + [_dienes_cube_blue() for _ in range(second)]
    else:
        given, gap = (second, first) if unknown == "first" else (first, second)
        cells = [_dienes_cube() for _ in range(given)] + [_dienes_cube_dashed() for _ in range(gap)]
    return _wrap(_dienes_cube_row(cells))


def ones_to_ten_frame(n: int) -> str:
    """For "n + ☐ = next ten": one ten frame showing just n's ones digit as
    black dots, with the rest of the frame as dashed dots — the gap to the
    next ten is the dashed dots (a bond to 10 on the ones digit)."""
    ones = n % 10
    return bond_frame(ones, 10 - ones, 10, "second")


def _ten_frame_from_colors(colors: list[str]) -> str:
    cells = []
    for i in range(10):
        edge = ' stroke="#2e6da4" stroke-width="2"' if i < len(colors) and colors[i] == "#a3c9f9" else ""
        dot = f'<circle cx="19" cy="19" r="13" fill="{colors[i]}"{edge}/>' if i < len(colors) else ""
        cells.append(
            f'<div style="width:38px;height:38px;border:1px solid #333;'
            f'display:flex;align-items:center;justify-content:center;">'
            f'<svg width="38" height="38">{dot}</svg></div>'
        )
    return (
        f'<div style="display:inline-grid;grid-template-columns:repeat(5,38px);'
        f'grid-template-rows:repeat(2,38px);width:190px;">{"".join(cells)}</div>'
    )


def bridge_ten_frames(a: int, b: int) -> str:
    """The first addend's dots fill the first ten-frame; the second
    addend's dots — a different colour, so the two amounts are clearly
    separate sets — fill the rest of that frame and then spill into
    the second, showing how they combine to make a ten with a leftover."""
    color_a, color_b = "#111", "#a3c9f9"  # first number black, second light blue (set-wide convention)
    gap = max(0, 10 - a)
    b_in_frame1 = min(b, gap)
    b_in_frame2 = b - b_in_frame1

    frame1 = _ten_frame_from_colors([color_a] * a + [color_b] * b_in_frame1)
    frame2 = _ten_frame_from_colors([color_b] * b_in_frame2)
    inner = f'<div style="display:flex;gap:20px;flex-wrap:wrap;">{frame1}{frame2}</div>'
    return _wrap(inner)


def bridge_number_line(a: int, b: int) -> str:
    """Empty number line for "a + b" bridging 10: `a` circled, 10 marked,
    and a blank landing box; a dashed "?" hop from a to 10, then another
    from 10 to the answer — the pupil works out how to split b. Spacing is
    roughly proportional so the two hops look their relative sizes."""
    W, H, y = 560, 136, 92
    first, second = 10 - a, a + b - 10
    x0, x2 = 60, 500
    x1 = x0 + (x2 - x0) * first / b
    x1 = min(max(x1, x0 + 90), x2 - 90)
    colors = ["#2e6da4", "#c0392b"]
    parts = [
        f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" font-family="inherit">',
        '<defs><marker id="brnl" markerWidth="10" markerHeight="10" refX="8" refY="4" orient="auto" markerUnits="userSpaceOnUse">'
        '<path d="M0,0 L8,4 L0,8 z" fill="#222"/></marker></defs>',
        f'<line x1="10" y1="{y}" x2="{W - 10}" y2="{y}" stroke="#222" stroke-width="2"/>',
    ]
    for i, (xa, xb) in enumerate(((x0, x1), (x1, x2))):
        mid, c = (xa + xb) / 2, colors[i]
        parts.append(f'<path d="M{xa},{y} Q{mid},{y - 70} {xb},{y}" fill="none" stroke="{c}" stroke-width="2.5" stroke-dasharray="5,4" marker-end="url(#brnl)"/>')
        parts.append(f'<text x="{mid}" y="{y - 42}" text-anchor="middle" font-size="16" font-weight="bold" fill="{c}">?</text>')
    for xv in (x0, x1, x2):
        parts.append(f'<line x1="{xv}" y1="{y - 8}" x2="{xv}" y2="{y + 8}" stroke="#222" stroke-width="2"/>')
    parts.append(f'<circle cx="{x0}" cy="{y + 24}" r="15" fill="none" stroke="#c0392b" stroke-width="2"/>')
    parts.append(f'<text x="{x0}" y="{y + 29}" text-anchor="middle" font-size="14" font-weight="bold" fill="#c0392b">{a}</text>')
    parts.append(f'<text x="{x1}" y="{y + 29}" text-anchor="middle" font-size="14" font-weight="bold" fill="#222">10</text>')
    parts.append(f'<rect x="{x2 - 20}" y="{y + 12}" width="40" height="26" rx="4" fill="#fff" stroke="#c0392b" stroke-width="2"/>')
    parts.append("</svg>")
    return _wrap("".join(parts))


def rekenrek_bridge(a: int, b: int) -> str:
    """Rekenrek for "a + b" bridging 10: `a` beads pushed left on the top
    wire, then (a small gap) the rest of the top wire's beads — the part
    of b that makes 10 — then the remainder of b pushed left on the
    bottom wire. Unused beads stay at the right."""
    bead_r, step, gap_w, split = 11, 24, 70, 10
    left_x = 30
    wire_len = 10 * step + gap_w + split
    width, height = left_x * 2 + wire_len, 30 + 2 * 44
    red, white = "#e74c3c", "#ffffff"
    parts = [
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">',
        f'<rect x="8" y="6" width="{width - 16}" height="{height - 12}" rx="8" fill="none" stroke="#8a6d3b" stroke-width="5"/>',
    ]
    on_left_rows = [10, a + b - 10]
    for r in range(2):
        y = 34 + r * 44
        on_left = on_left_rows[r]
        parts.append(f'<line x1="10" y1="{y}" x2="{width - 10}" y2="{y}" stroke="#555" stroke-width="2"/>')
        for i in range(10):
            x = left_x + i * step + step / 2
            if r == 0 and i >= a:
                x += split  # small gap between a and the beads that make 10
            if i >= on_left:
                x += gap_w + (split if r == 1 else 0)
            fill = red if i < 5 else white
            parts.append(f'<circle cx="{x:.1f}" cy="{y}" r="{bead_r}" fill="{fill}" stroke="#333" stroke-width="1.5"/>')
    parts.append("</svg>")
    return _wrap("".join(parts))


def numicon_bridge(a: int, b: int) -> str:
    """Numicon for "a + b" bridging 10: the real plates for a and b side
    by side, with a dashed line across b's plate splitting off the part
    that makes 10 with a (the bottom 10−a holes) from the rest."""
    c, r_hole, pad, gap = 30, 10, 6, 18
    make10 = set(_numicon_cells(10 - a, False, 0))
    plates = [(set(_numicon_cells(a, False, 0)), NUMICON_COLOURS.get(a), None),
              (set(_numicon_cells(b, False, 0)), NUMICON_COLOURS.get(b), make10)]
    rows = max((n + 1) // 2 for n in (a, b))
    W = 2 * (2 * c) + gap + 2 * pad
    H = rows * c + 2 * pad
    parts = [f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">']
    for p_i, (cells, fill, split) in enumerate(plates):
        ox = pad + p_i * (2 * c + gap)

        def xy(col, row):
            return ox + col * c, pad + (rows - 1 - row) * c

        for col, row in cells:
            x, y = xy(col, row)
            parts.append(f'<rect x="{x}" y="{y}" width="{c}" height="{c}" fill="{fill}"/>')
        for col, row in cells:
            x, y = xy(col, row)
            for (dc, dr), (x1, y1, x2, y2) in {
                (0, 1): (x, y, x + c, y), (0, -1): (x, y + c, x + c, y + c),
                (-1, 0): (x, y, x, y + c), (1, 0): (x + c, y, x + c, y + c),
            }.items():
                nb = (col + dc, row + dr)
                if nb not in cells:
                    parts.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#333" stroke-width="2.5" stroke-linecap="round"/>')
                elif split and ((col, row) in split) != (nb in split) and (col, row) in split:
                    parts.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#111" stroke-width="3" stroke-dasharray="6,4"/>')
        for col, row in cells:
            x, y = xy(col, row)
            parts.append(f'<circle cx="{x + c / 2}" cy="{y + c / 2}" r="{r_hole}" fill="#fff" stroke="#333" stroke-width="1.5"/>')
    parts.append("</svg>")
    return _wrap("".join(parts))


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
    dots; the bottom row holds `n` light-blue dots directly underneath —
    same column, same count — so doubling reads as "this row, and the same
    again below it" rather than a plain count. `n` must be 1-5 so both rows
    fit within the frame's 5 columns."""
    cells = []
    for i in range(10):
        row, col = divmod(i, 5)
        if col < n and row == 0:
            dot = '<circle cx="19" cy="19" r="13" fill="#111"/>'
        elif col < n and row == 1:
            # the same number again — known, so solid (light blue), not dashed
            dot = '<circle cx="19" cy="19" r="13" fill="#a3c9f9" stroke="#2e6da4" stroke-width="2"/>'
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


# Standard Numicon plate colours, 1–10.
NUMICON_COLOURS = {
    1: "#f39c12", 2: "#5dade2", 3: "#7dcea0", 4: "#f7dc6f", 5: "#aed6f1",
    6: "#a569bd", 7: "#ffffff", 8: "#e74c3c", 9: "#a0522d", 10: "#2874a6",
}


def _numicon_cells(n: int, flipped: bool, row_offset: int) -> list[tuple[int, int]]:
    """Grid cells (col, row-from-bottom) for a true Numicon plate of `n`:
    holes in pairs, two columns wide, with an odd number's extra hole
    sticking up on the left. `flipped=True` is the plate turned through
    180° — the odd hole then hangs down on the right, which is what lets
    two equal odd plates lock together."""
    pairs, odd = divmod(n, 2)
    if not flipped:
        cells = [(c, r) for r in range(pairs) for c in (0, 1)]
        if odd:
            cells.append((0, pairs))
    else:
        cells = [(1, 0)] if odd else []
        cells += [(c, r + odd) for r in range(pairs) for c in (0, 1)]
    return [(c, r + row_offset) for c, r in cells]


def double_numicon(n: int) -> str:
    """Doubling with real Numicon shapes, tessellated: one plate for `n`
    the right way up, a second identical plate turned through 180° and
    fitted on top. Together they make a solid 2-wide rectangle — the
    shape of the double — so the total can be read off as pairs. Each
    plate keeps its own outline so both copies of `n` are still visible."""
    c, r_hole, pad = 34, 11, 6
    pairs, odd = divmod(n, 2)
    a = _numicon_cells(n, False, 0)
    b = _numicon_cells(n, True, pairs)  # sits on top, its odd hole filling A's gap
    rows = n  # 2n holes, two per row
    W, H = 2 * c + 2 * pad, rows * c + 2 * pad
    fill = NUMICON_COLOURS.get(n, "#4a90d9")

    def xy(col, row):
        return pad + col * c, pad + (rows - 1 - row) * c

    parts = [f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">']
    for cells in (a, b):
        cs = set(cells)
        for col, row in cells:
            x, y = xy(col, row)
            parts.append(f'<rect x="{x}" y="{y}" width="{c}" height="{c}" fill="{fill}"/>')
        for col, row in cells:
            x, y = xy(col, row)
            # outline only the edges not shared with another cell of the same plate
            for (dc, dr), (x1, y1, x2, y2) in {
                (0, 1): (x, y, x + c, y), (0, -1): (x, y + c, x + c, y + c),
                (-1, 0): (x, y, x, y + c), (1, 0): (x + c, y, x + c, y + c),
            }.items():
                if (col + dc, row + dr) not in cs:
                    parts.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#333" stroke-width="2.5" stroke-linecap="round"/>')
        for col, row in cells:
            x, y = xy(col, row)
            parts.append(f'<circle cx="{x + c / 2}" cy="{y + c / 2}" r="{r_hole}" fill="#fff" stroke="#333" stroke-width="1.5"/>')
    parts.append("</svg>")
    return _wrap("".join(parts))


def double_number_line(n: int) -> str:
    """Doubling: number line from 0 with two equal "+n" hops (0 → n →
    2n); the landing point is blanked."""
    return number_line(0, 2 * n + 1, jumps=[(0, n, f"+{n}", False), (n, 2 * n, f"+{n}", False)], hide_value=2 * n)


def halve_partition(n: int) -> str:
    """Halving a two-digit number by partitioning — the same layout as
    `double_partition`, with "÷2" arrows instead of "×2"."""
    return double_partition(n, op="÷2")


def double_partition(n: int, op: str = "×2") -> str:
    """Doubling a two-digit number by partitioning: `n` at the top,
    branching into its tens and ones; each part doubled ("×2") into a
    blank box; the two blanks then joined into a final "☐ + ☐ = ☐" line.
    Only `n` and its parts are printed — every doubled value is blank."""
    tens, ones = (n // 10) * 10, n % 10
    W, H = 300, 210
    lx, rx, cx = 85, 215, 150
    box = lambda x, y, w=54, h=34: (f'<rect x="{x - w / 2}" y="{y - h / 2}" width="{w}" height="{h}" rx="5" '
                                    'fill="#fff" stroke="#2b2b2b" stroke-width="2"/>')
    txt = lambda x, y, t, size=22, col="#222": (f'<text x="{x}" y="{y}" text-anchor="middle" font-size="{size}" '
                                                f'font-weight="bold" fill="{col}">{t}</text>')
    parts = [
        f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" font-family="inherit">',
        '<defs><marker id="dparr" markerWidth="8" markerHeight="8" refX="4" refY="4" orient="auto">'
        '<path d="M0,0 L8,4 L0,8 z" fill="#2e6da4"/></marker></defs>',
        txt(cx, 30, n, 26),
        f'<line x1="{cx - 12}" y1="40" x2="{lx + 6}" y2="66" stroke="#333" stroke-width="2"/>',
        f'<line x1="{cx + 12}" y1="40" x2="{rx - 6}" y2="66" stroke="#333" stroke-width="2"/>',
        txt(lx, 90, tens), txt(rx, 90, ones),
    ]
    for x in (lx, rx):
        parts.append(f'<line x1="{x}" y1="98" x2="{x}" y2="128" stroke="#2e6da4" stroke-width="2" marker-end="url(#dparr)"/>')
        parts.append(txt(x + 22, 118, op, 14, "#2e6da4"))
        parts.append(box(x, 150))
    parts.append("</svg>")
    blank = ('<span style="display:inline-block;width:46px;height:30px;border:2px solid #2b2b2b;'
             'border-radius:5px;vertical-align:middle;box-sizing:border-box;"></span>')
    total = (f'<div style="text-align:center;font-size:1.3rem;font-weight:700;margin-top:-30px;">'
             f'{blank} + {blank} = {blank}</div>')
    return _wrap("".join(parts) + total)


def double_empty_number_line(n: int) -> str:
    """Doubling a two-digit number on an empty (not-to-scale) number
    line: marks at 0, `n` and the landing point, two equal "+n" hops,
    and the landing point left as a blank box."""
    W, H, y = 560, 136, 92
    xs = [40, 280, 520]
    colors = ["#2e6da4", "#c0392b"]
    parts = [
        f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" font-family="inherit">',
        '<defs><marker id="denl" markerWidth="10" markerHeight="10" refX="8" refY="4" orient="auto" markerUnits="userSpaceOnUse">'
        '<path d="M0,0 L8,4 L0,8 z" fill="#222"/></marker></defs>',
        f'<line x1="10" y1="{y}" x2="{W - 10}" y2="{y}" stroke="#222" stroke-width="2"/>',
    ]
    for i in range(2):
        xa, xb = xs[i], xs[i + 1]
        mid, c = (xa + xb) / 2, colors[i]
        parts.append(f'<path d="M{xa},{y} Q{mid},{y - 70} {xb},{y}" fill="none" stroke="{c}" stroke-width="2.5" marker-end="url(#denl)"/>')
        parts.append(f'<text x="{mid}" y="{y - 42}" text-anchor="middle" font-size="16" font-weight="bold" fill="{c}">+{n}</text>')
    for i, xv in enumerate(xs):
        parts.append(f'<line x1="{xv}" y1="{y - 8}" x2="{xv}" y2="{y + 8}" stroke="#222" stroke-width="2"/>')
        if i < 2:
            parts.append(f'<text x="{xv}" y="{y + 29}" text-anchor="middle" font-size="14" font-weight="bold" fill="#222">{0 if i == 0 else n}</text>')
        else:
            parts.append(f'<rect x="{xv - 20}" y="{y + 12}" width="40" height="26" rx="4" fill="#fff" stroke="#c0392b" stroke-width="2"/>')
    parts.append("</svg>")
    return _wrap("".join(parts))


def halve_empty_number_line(n: int) -> str:
    """Halving a two-digit number on an empty (not-to-scale) number line:
    0, a blank box at the halfway point, and `n` (circled), with two
    equal dashed "?" hops."""
    W, H, y = 560, 136, 92
    xs = [40, 280, 520]
    colors = ["#2e6da4", "#c0392b"]
    parts = [
        f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" font-family="inherit">',
        '<defs><marker id="henl" markerWidth="10" markerHeight="10" refX="8" refY="4" orient="auto" markerUnits="userSpaceOnUse">'
        '<path d="M0,0 L8,4 L0,8 z" fill="#222"/></marker></defs>',
        f'<line x1="10" y1="{y}" x2="{W - 10}" y2="{y}" stroke="#222" stroke-width="2"/>',
    ]
    for i in range(2):
        xa, xb = xs[i], xs[i + 1]
        mid, c = (xa + xb) / 2, colors[i]
        parts.append(f'<path d="M{xa},{y} Q{mid},{y - 70} {xb},{y}" fill="none" stroke="{c}" stroke-width="2.5" stroke-dasharray="5,4" marker-end="url(#henl)"/>')
        parts.append(f'<text x="{mid}" y="{y - 42}" text-anchor="middle" font-size="16" font-weight="bold" fill="{c}">?</text>')
    for i, xv in enumerate(xs):
        parts.append(f'<line x1="{xv}" y1="{y - 8}" x2="{xv}" y2="{y + 8}" stroke="#222" stroke-width="2"/>')
    parts.append(f'<text x="{xs[0]}" y="{y + 29}" text-anchor="middle" font-size="14" font-weight="bold" fill="#222">0</text>')
    parts.append(f'<rect x="{xs[1] - 20}" y="{y + 12}" width="40" height="26" rx="4" fill="#fff" stroke="#c0392b" stroke-width="2"/>')
    parts.append(f'<circle cx="{xs[2]}" cy="{y + 24}" r="15" fill="none" stroke="#c0392b" stroke-width="2"/>')
    parts.append(f'<text x="{xs[2]}" y="{y + 29}" text-anchor="middle" font-size="14" font-weight="bold" fill="#c0392b">{n}</text>')
    parts.append("</svg>")
    return _wrap("".join(parts))


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


def equal_hops_line(step: int, count: int, end_label: str | None = None) -> str:
    """Empty number line from 0 with `count` equal hops, each labelled
    "+step" (alternating colours), plain ticks in between. The end mark
    shows `end_label` circled if given (e.g. the total in a division),
    otherwise it's left unlabelled — the pupil counts the hops."""
    W, H, y = 600, 136, 92
    xs = [40 + 520 * i / count for i in range(count + 1)]
    colors = ["#2e6da4", "#c0392b"]
    arc = min(60, 20 + 260 / count)
    parts = [
        f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" font-family="inherit">',
        '<defs><marker id="eqhl" markerWidth="10" markerHeight="10" refX="8" refY="4" orient="auto" markerUnits="userSpaceOnUse">'
        '<path d="M0,0 L8,4 L0,8 z" fill="#222"/></marker></defs>',
        f'<line x1="10" y1="{y}" x2="{W - 10}" y2="{y}" stroke="#222" stroke-width="2"/>',
    ]
    for i in range(count):
        xa, xb = xs[i], xs[i + 1]
        mid, c = (xa + xb) / 2, colors[i % 2]
        parts.append(f'<path d="M{xa:.1f},{y} Q{mid:.1f},{y - arc:.1f} {xb:.1f},{y}" fill="none" stroke="{c}" stroke-width="2.5" marker-end="url(#eqhl)"/>')
        parts.append(f'<text x="{mid:.1f}" y="{y - arc / 2 - 8:.1f}" text-anchor="middle" font-size="{14 if count > 5 else 16}" font-weight="bold" fill="{c}">+{step}</text>')
    for xv in xs:
        parts.append(f'<line x1="{xv:.1f}" y1="{y - 8}" x2="{xv:.1f}" y2="{y + 8}" stroke="#222" stroke-width="2"/>')
    parts.append(f'<text x="{xs[0]}" y="{y + 29}" text-anchor="middle" font-size="14" font-weight="bold" fill="#222">0</text>')
    if end_label is not None:
        parts.append(f'<circle cx="{xs[-1]}" cy="{y + 24}" r="15" fill="none" stroke="#c0392b" stroke-width="2"/>')
        parts.append(f'<text x="{xs[-1]}" y="{y + 29}" text-anchor="middle" font-size="14" font-weight="bold" fill="#c0392b">{end_label}</text>')
    parts.append("</svg>")
    return _wrap("".join(parts))


def dot_array(rows: int, cols: int) -> str:
    """`rows` × `cols` array of black dots, each row ringed in a rounded
    outline so it reads as `rows` lots of `cols`."""
    dot = '<svg width="26" height="26"><circle cx="13" cy="13" r="10" fill="#111"/></svg>'
    # each row ringed in its own rounded outline, so it reads as "rows lots of cols"
    row = (f'<div style="display:inline-flex;gap:6px;padding:5px 9px;border:2.5px solid #2e6da4;'
           f'border-radius:22px;">{dot * cols}</div>')
    return _wrap(f'<div style="display:flex;flex-direction:column;align-items:flex-start;gap:8px;">{row * rows}</div>')


def cube_number_stack(n: int) -> str:
    """For "what is n³?" (n ≤ 4 only — past that the grid lines on each
    face get too fine to read): the rewrite `n³ = n×n×n` above a true
    isometric cube, n unit-cubes along each edge, with the top, left and
    right faces each ruled into an n×n grid of unit squares — so the
    total of n³ unit cubes is visible without ever being printed as a
    number. A single colour is used for all three faces (no
    light/shadow shading) to keep it consistent with the flat, untinted
    style used elsewhere in this file."""
    rewrite = (
        '<div style="text-align:center;font-size:1.4rem;font-weight:700;margin-bottom:14px;">'
        f'{n}³ = {n}&times;{n}&times;{n}</div>'
    )
    s = 26  # projected length of one unit-cube edge, in pixels

    def iso(i: float, j: float, k: float) -> tuple[float, float]:
        # Standard isometric projection: i/j are the two horizontal axes,
        # k is height. The shared corner nearest the viewer (and highest
        # on screen) is (i=n, j=0, k=n).
        return (i - j) * 0.866 * s, (i + j) * 0.5 * s - k * s

    def face(fixed_axis: str, fixed_val: int, fill: str) -> str:
        # One n×n grid face: `fixed_axis` ("i", "j", or "k") is pinned at
        # `fixed_val` while the other two range over [0, n].
        def p(a, b):
            if fixed_axis == "k":
                return iso(a, b, fixed_val)
            if fixed_axis == "j":
                return iso(a, fixed_val, b)
            return iso(fixed_val, a, b)

        corners = [p(0, 0), p(n, 0), p(n, n), p(0, n)]
        outline = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in corners) + " Z"
        parts = [f'<path d="{outline}" fill="{fill}" stroke="#2e6da4" stroke-width="2"/>']
        for i in range(1, n):
            a0, a1 = p(i, 0), p(i, n)
            b0, b1 = p(0, i), p(n, i)
            parts.append(f'<line x1="{a0[0]:.1f}" y1="{a0[1]:.1f}" x2="{a1[0]:.1f}" y2="{a1[1]:.1f}" stroke="#2e6da4" stroke-width="1"/>')
            parts.append(f'<line x1="{b0[0]:.1f}" y1="{b0[1]:.1f}" x2="{b1[0]:.1f}" y2="{b1[1]:.1f}" stroke="#2e6da4" stroke-width="1"/>')
        return "".join(parts)

    # The two front faces (meeting the top face at its single lowest
    # corner, and each other along the cube's nearest vertical edge) are
    # i=n and j=n — NOT j=0, which actually sits almost entirely behind
    # the i=n face from this viewpoint and was swallowing the drawing.
    body = face("k", n, "#c9e0fd") + face("j", n, "#a3c9f9") + face("i", n, "#7fb0eb")

    # Bounding box over all eight cube corners, so the canvas fits with a
    # small margin regardless of n.
    corners = [iso(i, j, k) for i in (0, n) for j in (0, n) for k in (0, n)]
    xs, ys = [c[0] for c in corners], [c[1] for c in corners]
    pad = 4
    minx, maxx = min(xs) - pad, max(xs) + pad
    miny, maxy = min(ys) - pad, max(ys) + pad
    width, height = maxx - minx, maxy - miny

    svg = (
        f'<svg width="{width:.0f}" height="{height:.0f}" style="display:block;margin:0 auto;" '
        f'viewBox="{minx:.1f} {miny:.1f} {width:.1f} {height:.1f}" xmlns="http://www.w3.org/2000/svg">'
        f'{body}</svg>'
    )
    return _wrap(rewrite + svg)


def cube_root_volume(total: int) -> str:
    """For "what is ∛total?": "Volume = total" above a plain isometric cube
    (no grid lines — counting squares along an edge would give the answer
    away, and leaving them off means it works at any size up to ∛1000),
    with a measuring line parallel to the bottom-right edge and a "?" box in
    its middle, so it's clear the side length is what's being found. The
    blank check `☐×☐×☐=total` sits underneath."""
    s, n = 40, 3  # fixed drawing size — the picture never encodes the answer

    def iso(i: float, j: float, k: float) -> tuple[float, float]:
        return (i - j) * 0.866 * s, (i + j) * 0.5 * s - k * s

    def face(pts, fill):
        d = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts) + " Z"
        return f'<path d="{d}" fill="{fill}" stroke="#2e6da4" stroke-width="2"/>'

    body = (
        face([iso(0, 0, n), iso(n, 0, n), iso(n, n, n), iso(0, n, n)], "#c9e0fd")
        + face([iso(0, n, 0), iso(n, n, 0), iso(n, n, n), iso(0, n, n)], "#a3c9f9")
        + face([iso(n, 0, 0), iso(n, n, 0), iso(n, n, n), iso(n, 0, n)], "#7fb0eb")
    )
    # Measuring line: offset outward from the bottom edge of the right face.
    a, b = iso(n, n, 0), iso(n, 0, 0)
    nx, ny, off, t = 0.5, 0.866, 24, 7
    p0 = (a[0] + nx * off, a[1] + ny * off)
    p1 = (b[0] + nx * off, b[1] + ny * off)
    bx, by = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2
    w, h = 40, 30
    dim = f'<line x1="{p0[0]:.1f}" y1="{p0[1]:.1f}" x2="{p1[0]:.1f}" y2="{p1[1]:.1f}" stroke="#2b2b2b" stroke-width="2"/>'
    dim += "".join(
        f'<line x1="{p[0]-nx*t:.1f}" y1="{p[1]-ny*t:.1f}" x2="{p[0]+nx*t:.1f}" y2="{p[1]+ny*t:.1f}" stroke="#2b2b2b" stroke-width="2"/>'
        for p in (p0, p1)
    )
    dim += (
        f'<rect x="{bx-w/2:.1f}" y="{by-h/2:.1f}" width="{w}" height="{h}" rx="4" fill="#fff" stroke="#2b2b2b" stroke-width="2"/>'
        f'<text x="{bx:.1f}" y="{by+7:.1f}" text-anchor="middle" font-family="Arial,sans-serif" font-size="20" font-weight="700">?</text>'
    )
    pts = [iso(i, j, k) for i in (0, n) for j in (0, n) for k in (0, n)]
    xs, ys = [q[0] for q in pts], [q[1] for q in pts]
    x0, y0 = min(xs) - 6, min(ys) - 6
    x1 = max(max(xs), bx + w / 2, p1[0] + t) + 6
    y1 = max(max(ys), by + h / 2, p0[1] + t, p1[1] + t) + 6
    svg = (
        f'<svg width="{x1-x0:.0f}" height="{y1-y0:.0f}" style="display:block;margin:0 auto;" '
        f'viewBox="{x0:.1f} {y0:.1f} {x1-x0:.1f} {y1-y0:.1f}" xmlns="http://www.w3.org/2000/svg">{body}{dim}</svg>'
    )
    blank = ('<span style="display:inline-block;min-width:34px;height:1.1em;border:2px solid #2b2b2b;'
             'border-radius:4px;vertical-align:middle;margin:0 2px;"></span>')
    head = f'<div style="text-align:center;font-size:1.4rem;font-weight:700;margin-bottom:14px;">Volume = {total}</div>'
    eq = f'<div style="text-align:center;font-size:1.3rem;font-weight:600;margin-top:14px;">{blank}×{blank}×{blank}={total}</div>'
    return _wrap(head + svg + eq)


def square_root_area(total: int) -> str:
    """For "what is √total?": "Area = total" above a plain square (no grid
    lines, fixed size — so it never gives the side length away), with a
    measuring line under the bottom edge and a "?" box in its middle, so
    it's clear the side length is what's being found. The blank check
    `☐×☐=total` sits underneath. The flat version of `cube_root_volume`."""
    side, pad, off, t = 130, 24, 22, 7
    W = side + 2 * pad
    H = side + off + 40
    x0, y0 = pad, 6
    ly = y0 + side + off
    bx, w, h = x0 + side / 2, 40, 30
    svg = (
        f'<svg width="{W}" height="{H}" style="display:block;margin:0 auto;" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">'
        f'<rect x="{x0}" y="{y0}" width="{side}" height="{side}" fill="#a3c9f9" stroke="#2e6da4" stroke-width="2.5"/>'
        f'<line x1="{x0}" y1="{ly}" x2="{x0 + side}" y2="{ly}" stroke="#2b2b2b" stroke-width="2"/>'
        f'<line x1="{x0}" y1="{ly - t}" x2="{x0}" y2="{ly + t}" stroke="#2b2b2b" stroke-width="2"/>'
        f'<line x1="{x0 + side}" y1="{ly - t}" x2="{x0 + side}" y2="{ly + t}" stroke="#2b2b2b" stroke-width="2"/>'
        f'<rect x="{bx - w / 2}" y="{ly - h / 2}" width="{w}" height="{h}" rx="4" fill="#fff" stroke="#2b2b2b" stroke-width="2"/>'
        f'<text x="{bx}" y="{ly + 7}" text-anchor="middle" font-family="Arial,sans-serif" font-size="20" font-weight="700">?</text>'
        "</svg>"
    )
    blank = ('<span style="display:inline-block;min-width:34px;height:1.1em;border:2px solid #2b2b2b;'
             'border-radius:4px;vertical-align:middle;margin:0 2px;"></span>')
    head = f'<div style="text-align:center;font-size:1.4rem;font-weight:700;margin-bottom:14px;">Area = {total}</div>'
    eq = f'<div style="text-align:center;font-size:1.3rem;font-weight:600;margin-top:10px;">{blank}×{blank}={total}</div>'
    return _wrap(head + svg + eq)


def _function_machine(op_label: str, output: str, back_label: str) -> str:
    """Function machine in the standard textbook style: dark purple
    input/output boxes joined by a line through a light-purple, arrow-
    shaped machine. The input is the unknown ("?"); a dashed arrow
    underneath runs from the output back to the input, labelled with the
    inverse operation — "run the machine backwards"."""
    dark, light, stroke = "#5b2c8f", "#e3d5f5", "#5b2c8f"
    W, H, y = 470, 175, 50
    bw, bh = 96, 40
    ix, ox = 20, W - 20 - bw
    mw, mh = 110, 56
    mx = (W - mw) / 2
    tip = 16
    machine = (f"M{mx},{y - mh / 2} L{mx + mw - tip},{y - mh / 2} L{mx + mw},{y} "
               f"L{mx + mw - tip},{y + mh / 2} L{mx},{y + mh / 2} Z")
    parts = [
        f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" style="display:block;margin:0 auto;" xmlns="http://www.w3.org/2000/svg" font-family="Arial,sans-serif">',
        f'<defs><marker id="fmback" markerWidth="10" markerHeight="10" refX="8" refY="4" orient="auto" markerUnits="userSpaceOnUse">'
        f'<path d="M0,0 L8,4 L0,8 z" fill="{dark}"/></marker></defs>',
        f'<line x1="{ix + bw}" y1="{y}" x2="{mx}" y2="{y}" stroke="{dark}" stroke-width="3"/>',
        f'<line x1="{mx + mw}" y1="{y}" x2="{ox}" y2="{y}" stroke="{dark}" stroke-width="3"/>',
        f'<rect x="{ix}" y="{y - bh / 2}" width="{bw}" height="{bh}" rx="3" fill="{dark}"/>',
        f'<text x="{ix + bw / 2}" y="{y + 9}" text-anchor="middle" font-size="26" font-weight="700" fill="#fff">?</text>',
        f'<path d="{machine}" fill="{light}" stroke="{stroke}" stroke-width="2.5" stroke-linejoin="round"/>',
        f'<text x="{mx + (mw - tip) / 2}" y="{y + 8}" text-anchor="middle" font-size="22" font-weight="700" fill="{dark}">{op_label}</text>',
        f'<rect x="{ox}" y="{y - bh / 2}" width="{bw}" height="{bh}" rx="3" fill="{dark}"/>',
        f'<text x="{ox + bw / 2}" y="{y + 8}" text-anchor="middle" font-size="22" font-weight="700" fill="#fff">{output}</text>',
        f'<path d="M{ox + bw / 2},{y + bh / 2 + 4} Q{W / 2},{y + 125} {ix + bw / 2},{y + bh / 2 + 6}" fill="none" stroke="{dark}" stroke-width="2.5" stroke-dasharray="6,4" marker-end="url(#fmback)"/>',
        f'<text x="{W / 2}" y="{y + 100}" text-anchor="middle" font-size="16" font-weight="700" fill="{dark}">{back_label}</text>',
        "</svg>",
    ]
    return _wrap("".join(parts))


def square_root_function_machine(total: int) -> str:
    """√total as a function machine: ? → [square it ( )²] → total, with
    "go backwards: unsquare (√)" on the return arrow."""
    return _function_machine("( )²", str(total), "go backwards: unsquare ( √ )")


def cube_root_function_machine(total: int) -> str:
    """∛total as a function machine: ? → [cube it ( )³] → total, with
    "go backwards: uncube (∛)" on the return arrow."""
    return _function_machine("( )³", str(total), "go backwards: uncube ( ∛ )")


def square_number_array(n: int) -> str:
    """For "what is n²?": the rewrite `n² = n×n` above an actual n-by-n
    grid of solid cells — the array IS n², so counting it (or just
    seeing the square shape) gives the answer without it ever being
    printed as a number."""
    rewrite = (
        '<div style="text-align:center;font-size:1.4rem;font-weight:700;margin-bottom:10px;">'
        f'{n}² = {n}&times;{n}</div>'
    )
    cell = 30
    row = "".join(
        f'<div style="width:{cell}px;height:{cell}px;background:#a3c9f9;border:2px solid #2e6da4;box-sizing:border-box;"></div>'
        for _ in range(n)
    )
    grid = f'<div style="display:grid;grid-template-columns:repeat({n},{cell}px);gap:2px;">' + row * n + "</div>"
    return _wrap(rewrite + grid)


def square_root_array(total: int) -> str:
    """For "what is √total?" (total a perfect square): the `total` cells
    arranged as an actual square (side length = isqrt(total)) — the
    picture IS the square, and the pupil counts one side to answer,
    rather than being told the number. The inverse of
    `square_number_array`, which starts from the side length instead and
    is shown alongside its n×n×n rewrite."""
    n = math.isqrt(total)
    cell = 28
    row = "".join(
        f'<div style="width:{cell}px;height:{cell}px;background:#a3c9f9;border:1.5px solid #2e6da4;box-sizing:border-box;"></div>'
        for _ in range(n)
    )
    grid = f'<div style="display:grid;grid-template-columns:repeat({n},{cell}px);gap:2px;">' + row * n + "</div>"
    blank = (
        '<div style="display:flex;align-items:center;gap:8px;margin-top:10px;">'
        '<span style="font-size:1.1rem;font-weight:700;">side length =</span>'
        '<span style="display:inline-block;width:40px;height:34px;border:2px solid #2b2b2b;border-radius:4px;"></span></div>'
    )
    return _wrap(grid + blank)


def multiples_array(step: int, count: int, prefill: int = 0) -> str:
    """Array model for listing multiples of `step`: `count` rows, each
    `step` cells wide and fully solid (every row is a clean multiple, no
    remainder involved the way a factor check has) — with a box beside
    each row for that row's running total (step, 2×step, 3×step, ...).
    `prefill` (a heavier level of support) writes the correct total into
    that many leading rows' boxes, leaving the rest blank; 0 (the
    default) leaves every box blank."""
    cell = 30
    rows = []
    for r in range(count):
        cells = "".join(
            f'<div style="width:{cell}px;height:{cell}px;background:#a3c9f9;border:2px solid #2e6da4;box-sizing:border-box;"></div>'
            for _ in range(step)
        )
        total_text = str(step * (r + 1)) if r < prefill else ""
        blank = (
            f'<div style="width:40px;height:{cell}px;border:2px solid #2b2b2b;border-radius:4px;'
            'margin-left:10px;flex:none;display:flex;align-items:center;justify-content:center;'
            f'font-size:1rem;font-weight:bold;">{total_text}</div>'
        )
        rows.append(
            f'<div style="display:flex;align-items:center;margin-bottom:4px;">'
            f'<div style="display:flex;gap:2px;">{cells}</div>{blank}</div>'
        )
    return _wrap("".join(rows))


def factor_array(n: int, candidate: int) -> str:
    """The "can you make a rectangle?" model for whether `candidate` is a
    factor of `n`: a grid `candidate` squares wide, filled solid for the
    first `n` cells and left as dashed outlines for whatever's left over
    to complete the final row. A clean rectangle (no dashed cells) means
    it divides exactly; a short last row shows the remainder visually
    without ever stating the yes/no answer in words."""
    rows = math.ceil(n / candidate)
    total = rows * candidate
    cell = 34
    cells = []
    for i in range(total):
        if i < n:
            cells.append(f'<div style="width:{cell}px;height:{cell}px;background:#a3c9f9;border:2px solid #2e6da4;box-sizing:border-box;"></div>')
        else:
            cells.append(f'<div style="width:{cell}px;height:{cell}px;background:none;border:2px dashed #bbb;box-sizing:border-box;"></div>')
    grid = f'<div style="display:grid;grid-template-columns:repeat({candidate},{cell}px);gap:3px;">{"".join(cells)}</div>'
    return _wrap(grid)


def factor_multiples_number_line(n: int, candidate: int, width: int = 640) -> str:
    """Whether `candidate` is a factor of `n`, shown by marking every
    multiple of `candidate` on a number line (up to just past `n`) with a
    circle, and `n` itself with a downward arrow — so the pupil can read
    off whether the arrow lands on a circled tick or between two of
    them, without the picture ever stating the answer directly."""
    top = ((n // candidate) + 2) * candidate
    pad = 36
    usable = width - 2 * pad
    height = 110

    def x(v: int) -> float:
        return pad + v / top * usable

    y_line = height - 42
    svg = [
        f'<svg viewBox="0 0 {width} {height}" width="100%" height="{height}" '
        f'xmlns="http://www.w3.org/2000/svg" font-family="inherit">',
        '<defs><marker id="famarrow" markerWidth="8" markerHeight="8" refX="4" refY="4" '
        'orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#c0392b"/></marker></defs>',
        f'<line x1="{pad}" y1="{y_line}" x2="{width-pad}" y2="{y_line}" stroke="#222" stroke-width="2"/>',
    ]
    for v in range(0, top + 1):
        xv = x(v)
        is_mult = v != 0 and v % candidate == 0
        tick_h = 8 if is_mult else 5
        svg.append(f'<line x1="{xv:.1f}" y1="{y_line-tick_h}" x2="{xv:.1f}" y2="{y_line+tick_h}" stroke="#222" stroke-width="{1.5 if is_mult else 1}"/>')
        svg.append(f'<text x="{xv:.1f}" y="{y_line+22}" text-anchor="middle" font-size="12" fill="#222">{v}</text>')
        if is_mult:
            svg.append(f'<circle cx="{xv:.1f}" cy="{y_line}" r="9" fill="none" stroke="#2e6da4" stroke-width="2.5"/>')
    xn = x(n)
    svg.append(f'<line x1="{xn:.1f}" y1="{y_line-34}" x2="{xn:.1f}" y2="{y_line-10}" stroke="#c0392b" stroke-width="2.5" marker-end="url(#famarrow)"/>')
    svg.append(f'<text x="{xn:.1f}" y="{y_line-38}" text-anchor="middle" font-size="14" font-weight="bold" fill="#c0392b">{n}</text>')
    svg.append("</svg>")
    return _wrap("".join(svg))


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
        f'<svg width="{u+2}" height="{u+2}" viewBox="0 0 {u+2} {u+2}">'
        f'<rect x="1" y="1" width="{u}" height="{u}" rx="2" fill="none" stroke="#999" stroke-width="2" stroke-dasharray="3,3"/>'
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


def dienes_bonds_to_100(known: int, target: int = 100) -> str:
    """`known` built solid with Dienes blocks, then the gap up to 100
    shown as dashed (countable) rods and cubes: the solid rods first,
    then the ones row (solid and dashed cubes together), then the rest
    of the dashed rods underneath that."""
    gap = target - known
    k_tens, k_ones = divmod(known, 10)
    g_tens, g_ones = divmod(gap, 10)

    solid_rods_html = "".join(f'<div>{_dienes_rod()}</div>' for _ in range(k_tens))
    dashed_rods_html = "".join(f'<div>{_dienes_rod_greyed()}</div>' for _ in range(g_tens))
    ones_cells = [_dienes_cube() for _ in range(k_ones)] + [_dienes_cube_dashed() for _ in range(g_ones)]
    ones_html = _dienes_cube_row(ones_cells)

    inner = f'<div style="display:flex;flex-direction:column;gap:3px;">{solid_rods_html}{ones_html}{dashed_rods_html}</div>'
    return _wrap(inner)


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
    """Two matched columns (black dots vs light-blue dots) showing `n` split
    into two equal groups. If `n` is odd, the leftover dot is drawn split
    down the middle by a dashed line — straddling both columns — instead of
    being dropped into one side, so a half-remainder is visible rather than
    implied."""
    half = n // 2
    odd = n % 2 == 1

    def full_dot() -> str:
        return '<svg width="28" height="28" viewBox="0 0 28 28"><circle cx="14" cy="14" r="11" fill="#111" stroke="#111" stroke-width="2"/></svg>'

    def empty_dot() -> str:
        return '<svg width="28" height="28" viewBox="0 0 28 28"><circle cx="14" cy="14" r="11" fill="#a3c9f9" stroke="#2e6da4" stroke-width="2"/></svg>'

    def split_dot() -> str:
        return (
            '<svg width="28" height="28" viewBox="0 0 28 28">'
            '<path d="M14,3 A11,11 0 0,0 14,25 Z" fill="#111" stroke="#111" stroke-width="2"/>'
            '<path d="M14,3 A11,11 0 0,1 14,25 Z" fill="#a3c9f9" stroke="#2e6da4" stroke-width="2"/>'
            '<line x1="14" y1="2" x2="14" y2="26" stroke="#333" stroke-width="2" stroke-dasharray="3,2"/>'
            "</svg>"
        )

    rows = [f'<div style="display:flex;gap:14px;">{full_dot()}{empty_dot()}</div>' for _ in range(half)]
    if odd:
        rows.append(split_dot())
    inner = f'<div style="display:flex;flex-direction:column;gap:4px;align-items:center;">{"".join(rows)}</div>'
    return _wrap(inner)


def halve_numicon(n: int) -> str:
    """Halving with a real Numicon plate for `n`: the plate is drawn whole,
    with a dashed line marking where it splits into two equal halves —
    the doubling picture (SC-055) in reverse, so each half is itself the
    Numicon shape for n÷2. Even numbers only: an odd plate's extra hole
    only touches one of the two halves, so the split can't be shown
    fairly (the generator uses the other halving scaffolds for odd n)."""
    c, r_hole, pad = 34, 11, 6
    pairs, odd = divmod(n, 2)
    k = pairs  # n = 2k (+1)
    a = set(_numicon_cells(k, False, 0)) if k else set()
    b = set(_numicon_cells(k, True, k // 2)) if k else set()
    plate = set(_numicon_cells(n, False, 0))
    rows = pairs + odd
    W, H = 2 * c + 2 * pad, rows * c + 2 * pad
    fill = NUMICON_COLOURS.get(n, "#4a90d9")

    def xy(col, row):
        return pad + col * c, pad + (rows - 1 - row) * c

    edges = {(0, 1): lambda x, y: (x, y, x + c, y), (0, -1): lambda x, y: (x, y + c, x + c, y + c),
             (-1, 0): lambda x, y: (x, y, x, y + c), (1, 0): lambda x, y: (x + c, y, x + c, y + c)}
    parts = [f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">']
    for col, row in plate:
        x, y = xy(col, row)
        parts.append(f'<rect x="{x}" y="{y}" width="{c}" height="{c}" fill="{fill}"/>')
    for col, row in plate:
        x, y = xy(col, row)
        for (dc, dr), f in edges.items():
            nb = (col + dc, row + dr)
            x1, y1, x2, y2 = f(x, y)
            if nb not in plate:
                parts.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#333" stroke-width="2.5" stroke-linecap="round"/>')
            elif (col, row) in a and nb in b:
                parts.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#111" stroke-width="3" stroke-dasharray="6,4"/>')
    for col, row in plate:
        x, y = xy(col, row)
        parts.append(f'<circle cx="{x + c / 2}" cy="{y + c / 2}" r="{r_hole}" fill="#fff" stroke="#333" stroke-width="1.5"/>')
    parts.append("</svg>")
    return _wrap("".join(parts))


def halve_number_line(n: int) -> str:
    """Halving on a number line: 0 to `n` (circled), split into two equal
    dashed "?" hops; the halfway point is a blank box."""
    return number_line(0, n + 1, jumps=[(0, n / 2, "?", True), (n / 2, n, "?", True)], circle=n, hide_value=n / 2)


# -------------------------------------------------------------------- bar model
def bar_model(whole_label: str, parts: list[tuple[str, float]], note: str | None = None, single_color: str | None = None) -> str:
    """parts: list of (label, weight) — rendered as proportional segments.
    Pass `single_color` to fill every segment the same colour instead of
    cycling through the default palette (e.g. when the segments are all
    equal, same-sized parts rather than distinct labelled quantities)."""
    total_weight = sum(w for _, w in parts) or 1
    colors = ["#f6c453", "#a3c9f9", "#b7e4c7", "#f7a5a5", "#d8bfd8"]
    segs = []
    for i, (label, w) in enumerate(parts):
        pct = 100 * w / total_weight
        color = single_color if single_color else colors[i % len(colors)]
        if single_color and label == "?":
            color = "#fff"  # the unknown part stays white
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


def _fmt_seg(v: float) -> str:
    return str(int(v)) if v == int(v) else f"{v:g}"


def percentage_bar_model(amount, pct) -> str:
    """A "pct% of amount" bar: a double-headed arrow labelled with the
    whole amount, a "100%" track, then equal parts each labelled with the
    percentage it stands for (not its value — working that out is the
    pupil's job). Percentages that are a multiple of 25 use quarters;
    everything else uses tenths ("find 10% first"). The parts making up
    the target are shaded, with a blank box under each for its value. A
    leftover 5% (e.g. 15%) is shown as half of the next tenth, shaded
    and labelled 5%, so it looks half the size it is."""
    blue = "#a3c9f9"
    n_segments = 4 if int(pct) % 25 == 0 else 10
    step = 100 // n_segments
    whole = int(pct) // step
    remainder = int(pct) % step
    bar_w = 340
    seg_w = bar_w / n_segments

    arrow_svg = (
        f'<svg width="{bar_w}" height="34" viewBox="0 0 {bar_w} 34">'
        '<defs><marker id="pbarrow" markerWidth="7" markerHeight="7" refX="3.5" refY="3.5" '
        'orient="auto"><path d="M0,0 L7,3.5 L0,7 z" fill="#222"/></marker></defs>'
        f'<text x="{bar_w/2}" y="14" text-anchor="middle" font-size="16" font-weight="bold" fill="#222">{amount}</text>'
        f'<line x1="4" y1="26" x2="{bar_w-4}" y2="26" stroke="#222" stroke-width="1.5" '
        'marker-start="url(#pbarrow)" marker-end="url(#pbarrow)"/>'
        "</svg>"
    )
    track = (
        f'<div style="width:{bar_w}px;height:20px;background:#eee;border:1px solid #999;'
        'display:flex;align-items:center;justify-content:center;color:#888;font-size:0.8rem;'
        'box-sizing:border-box;">100%</div>'
    )
    box = ('<span style="display:inline-block;width:30px;height:26px;border:2px solid #2b2b2b;'
           'border-radius:4px;box-sizing:border-box;"></span>')
    cell_style = ("height:42px;border:1px solid #333;box-sizing:border-box;display:flex;"
                  "align-items:center;justify-content:center;font-weight:bold;font-size:0.8rem;")
    cells, boxes = [], []
    for i in range(n_segments):
        if i < whole:
            cells.append(f'<div style="width:{seg_w}px;{cell_style}background:{blue};color:#222;">{step}%</div>')
            boxes.append(f'<div style="width:{seg_w}px;display:flex;justify-content:center;">{box}</div>')
        elif i == whole and remainder:
            half = seg_w * remainder / step
            cells.append(
                f'<div style="width:{seg_w}px;height:42px;border:1px solid #333;box-sizing:border-box;display:flex;">'
                f'<div style="width:{half}px;background:{blue};border-right:1px dashed #333;display:flex;'
                f'align-items:center;justify-content:center;font-weight:bold;font-size:0.7rem;color:#222;">{remainder}%</div>'
                '<div style="flex:1;background:#fff;"></div></div>'
            )
            boxes.append(f'<div style="width:{seg_w}px;display:flex;justify-content:center;">{box}</div>')
        else:
            cells.append(f'<div style="width:{seg_w}px;{cell_style}background:#fff;color:#999;">{step}%</div>')
            boxes.append(f'<div style="width:{seg_w}px;"></div>')
    row = f'<div style="display:flex;width:{bar_w}px;">{"".join(cells)}</div>'
    box_row = f'<div style="display:flex;width:{bar_w}px;margin-top:4px;">{"".join(boxes)}</div>'
    inner = (
        '<div style="display:flex;flex-direction:column;align-items:center;gap:4px;">'
        + arrow_svg + track + row + box_row + "</div>"
    )
    return _wrap(inner)


def percentage_table(amount, pct) -> str:
    """Table method for "pct% of amount": a two-row table with 100% → the
    amount in the first column, then the stepping-stone percentages
    (10%, 5% — or 50%/25% for multiples of 25) and finally the target
    percentage, each with a blank box underneath. Only the given amount
    is printed; every value the pupil works out is left blank."""
    pct = int(pct)
    if pct % 25 == 0:
        cols = [100, 50] if pct == 50 else [100, 25] + ([pct] if pct != 25 else [])
    else:
        cols = [100, 10]
        if pct % 10:
            cols.append(5)
        if pct not in cols:
            cols.append(pct)
    blank = ('<span style="display:inline-block;width:46px;height:30px;border:2px solid #2b2b2b;'
             'border-radius:4px;vertical-align:middle;box-sizing:border-box;"></span>')
    td = "border:2px solid #333;padding:8px 14px;text-align:center;font-size:1.15rem;font-weight:700;"
    head = "".join(
        f'<td style="{td}background:{"#a3c9f9" if c == pct else "#eaf2fd"};">{c}%</td>' for c in cols
    )
    vals = "".join(
        f'<td style="{td}background:#fff;">{amount if c == 100 else blank}</td>' for c in cols
    )
    table = (
        '<table style="border-collapse:collapse;margin:0 auto;">'
        f'<tr>{head}</tr><tr>{vals}</tr></table>'
    )
    return _wrap(table)


def fraction_of_amount_bar(total: int, den: int, num: int) -> str:
    """For "what is num/den of total?": the whole (labelled `total`) above
    `den` equal parts, with only the first `num` shaded so it's clear
    which parts are wanted, and a blank box under every part for the
    pupil to write how much one part is worth. Never prints the unit or
    the answer."""
    top = (
        '<div style="border:1px solid #333;min-height:40px;display:flex;align-items:center;'
        f'justify-content:center;background:#eee;font-weight:bold;">{total}</div>'
    )
    parts = "".join(
        f'<div style="flex:1;min-height:44px;background:{"#a3c9f9" if i < num else "#fff"};'
        'border:1px solid #333;box-sizing:border-box;"></div>'
        for i in range(den)
    )
    boxes = "".join(
        '<div style="flex:1;display:flex;justify-content:center;">'
        '<span style="display:inline-block;width:34px;max-width:90%;height:28px;border:2px solid #2b2b2b;'
        'border-radius:4px;box-sizing:border-box;"></span></div>'
        for _ in range(den)
    )
    inner = (
        '<div style="display:flex;flex-direction:column;gap:4px;">'
        f'{top}<div style="display:flex;width:100%;">{parts}</div>'
        f'<div style="display:flex;width:100%;margin-top:4px;">{boxes}</div></div>'
    )
    return _wrap(inner)


def fraction_array(total: int, den: int, num: int) -> str:
    """`den` equal columns of dots (each holding `total / den` items),
    all the same colour, with a pill-shaped outline drawn around the
    first `num` of them — the array-model equivalent of the bar model,
    with no numbers printed on the picture itself."""
    unit = total // den
    cell = 22
    dot = f'<svg width="{cell}" height="{cell}"><circle cx="{cell / 2}" cy="{cell / 2}" r="{cell / 2 - 3}" fill="#a3c9f9" stroke="#2e6da4" stroke-width="1.5"/></svg>'

    def column() -> str:
        return f'<div style="display:flex;flex-direction:column;gap:2px;">{dot * unit}</div>'

    selected = "".join(f'<div style="margin-right:8px;">{column()}</div>' for _ in range(num))
    rest = "".join(f'<div style="margin-right:8px;">{column()}</div>' for _ in range(den - num))
    inner = (
        f'<div style="display:flex;align-items:center;">'
        f'<div style="display:flex;border:3px solid #2b2b2b;border-radius:40px;padding:6px 10px;margin-right:12px;">{selected}</div>'
        f'<div style="display:flex;">{rest}</div>'
        f'</div>'
    )
    return _wrap(inner)


# ------------------------------------------------------- equivalent fractions
def fraction_html(num, den) -> str:
    """An inline "true" fraction — numerator stacked over denominator
    with a bar — for embedding directly in a question prompt instead of
    writing it as plain `num/den` text."""
    return (
        '<span style="display:inline-flex;flex-direction:column;align-items:center;'
        'vertical-align:middle;margin:0 8px;">'
        f'<span style="line-height:1.1;">{num}</span>'
        '<span style="border-top:4px solid currentColor;width:100%;height:0;'
        'font-size:0;line-height:0;">&nbsp;</span>'
        f'<span style="line-height:1.1;">{den}</span></span>'
    )


def fraction_equation_html(left_num, left_den, right_num, right_den) -> str:
    """A full `a/b = c/d` question line built from stacked `fraction_html`
    fractions, all wrapped in one flex row so the "=" sign lines up with
    the fraction bars instead of the browser's default baseline (which
    otherwise sits the "=" awkwardly against the numerator alone)."""
    return (
        '<span style="display:inline-flex;align-items:center;justify-content:center;">'
        f'{fraction_html(left_num, left_den)}'
        '<span style="margin:0 6px;">=</span>'
        f'{fraction_html(right_num, right_den)}'
        '</span>'
    )


def _fraction_row_cells(n: int, d: int, total_w: int = 320, row_h: int = 40, color: str = "#a3c9f9") -> str:
    seg_w = total_w / d
    cells = [
        f'<div style="width:{seg_w}px;height:{row_h}px;background:{color if i < n else "#fff"};'
        f'border:1px solid #333;box-sizing:border-box;"></div>'
        for i in range(d)
    ]
    return f'<div style="display:flex;width:{total_w}px;">{"".join(cells)}</div>'


def _fraction_wall_two_rows_inner(num1: int, den1: int, num2: int, den2: int) -> str:
    return (
        '<div style="display:flex;flex-direction:column;gap:6px;">'
        f'{_fraction_row_cells(num1, den1)}{_fraction_row_cells(num2, den2)}</div>'
    )


def fraction_wall_two_rows(num1: int, den1: int, num2: int, den2: int) -> str:
    """A two-row fraction wall: both rows are the same total length, the
    top row split into `den1` equal parts with `num1` shaded, the
    bottom row split into `den2` equal parts with `num2` shaded — so
    the matching shaded length shows the two fractions are equal."""
    return _wrap(_fraction_wall_two_rows_inner(num1, den1, num2, den2))


def fraction_bar_single(num: int, den: int) -> str:
    """A single bar for the actual `num/den` in question — divided into
    visible unit cells when there are few enough to stay readable,
    otherwise a plain proportional fill (no per-cell borders). Only ever
    shows the fraction as given, never a simplified/scaled result, so it
    never leaks an answer."""
    if den <= 24:
        return _fraction_row_cells(num, den)
    total_w, row_h = 320, 40
    fill_w = round(total_w * num / den, 1)
    return (
        f'<div style="position:relative;width:{total_w}px;height:{row_h}px;'
        'border:2px solid #333;border-radius:4px;overflow:hidden;background:#fff;'
        'box-sizing:border-box;">'
        f'<div style="position:absolute;left:0;top:0;bottom:0;width:{fill_w}px;background:#a3c9f9;"></div>'
        "</div>"
    )


def fraction_matches_question(real_num: int, real_den: int, demo_inner_html: str) -> str:
    """The question's own fraction shown as a real, correctly-sized bar,
    plus a worked example of the method (different numbers) kept visually
    separate via a dashed divider — so the picture always relates to the
    actual question, and the generic demo is clearly a separate example
    rather than a confusing mismatch."""
    inner = (
        '<div style="display:flex;align-items:center;gap:20px;flex-wrap:wrap;">'
        f'<div>{fraction_bar_single(real_num, real_den)}</div>'
        '<div style="margin-left:6px;padding-left:20px;border-left:2px dashed #ccc;">'
        f"{demo_inner_html}</div></div>"
    )
    return _wrap(inner)


def _pie_svg(num: int, den: int, r: int = 50) -> str:
    cx = cy = r + 4
    size = 2 * (r + 4)
    parts = [f'<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}">']
    for i in range(den):
        a0 = math.radians(-90 + i * 360 / den)
        a1 = math.radians(-90 + (i + 1) * 360 / den)
        x0, y0 = cx + r * math.cos(a0), cy + r * math.sin(a0)
        x1, y1 = cx + r * math.cos(a1), cy + r * math.sin(a1)
        large = 1 if (360 / den) > 180 else 0
        fill = "#a3c9f9" if i < num else "#fff"
        parts.append(f'<path d="M{cx},{cy} L{x0:.2f},{y0:.2f} A{r},{r} 0 {large} 1 {x1:.2f},{y1:.2f} Z" fill="{fill}" stroke="#333" stroke-width="1.5"/>')
    parts.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#333" stroke-width="2"/>')
    parts.append("</svg>")
    return "".join(parts)


def _fraction_circles_pair_inner(num1: int, den1: int, num2: int, den2: int) -> str:
    return (
        f'<div style="display:flex;align-items:center;gap:20px;">'
        f'{_pie_svg(num1, den1)}'
        f'<div style="font-size:1.8rem;font-weight:800;">=</div>'
        f'{_pie_svg(num2, den2)}'
        f'</div>'
    )


def fraction_circles_pair(num1: int, den1: int, num2: int, den2: int) -> str:
    """Two shaded circles side by side (the first split into `den1`
    slices with `num1` shaded, the second into `den2` slices with
    `num2` shaded) joined by an "=" — the same shaded amount shown
    two different ways."""
    return _wrap(_fraction_circles_pair_inner(num1, den1, num2, den2))


def _fraction_scale_arrows_inner(num: int, den: int, scale: int, direction: str = "up", blank_right: bool = False) -> str:
    """`num/den` and its scaled equivalent side by side, with a curved
    arrow above joining the two numerators and one below joining the two
    denominators, each labelled with the scale factor. `direction="up"`
    scales `num/den` up (×scale, left→right); `direction="down"` starts
    from the larger, unsimplified fraction and simplifies down (÷scale,
    left→right). `blank_right=True` shows the arrows and the ÷/× factor
    but leaves the resulting fraction as empty boxes (☐) for the pupil
    to work out, rather than giving it away."""
    if direction == "up":
        left_n, left_d = num, den
        right_n, right_d = num * scale, den * scale
        op = "×"
    else:
        left_n, left_d = num * scale, den * scale
        right_n, right_d = num, den
        op = "÷"
    if blank_right:
        right_n, right_d = "☐", "☐"
    width, height = 260, 170
    x1, x2 = 60, 200
    # Numerator baseline sits just above the rule; denominator baseline
    # sits the same visual distance below it (digits have no descenders,
    # so the two gaps only look equal if the denominator offset is
    # smaller than the numerator's — do not "balance" these by eye as
    # equal numbers, that's what put the denominator too far down before.
    y_line = 70
    y_num, y_den = y_line - 12, y_line + 24
    top_arc_y, bot_arc_y = 20, 148
    mid_x = (x1 + x2) / 2

    def frac_block(x: float, n, d) -> str:
        return (
            f'<text x="{x}" y="{y_num}" text-anchor="middle" font-size="26" font-weight="bold" fill="#222">{n}</text>'
            f'<line x1="{x - 16}" y1="{y_line}" x2="{x + 16}" y2="{y_line}" stroke="#222" stroke-width="2.5"/>'
            f'<text x="{x}" y="{y_den}" text-anchor="middle" font-size="26" font-weight="bold" fill="#222">{d}</text>'
        )

    svg = [
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
        f'xmlns="http://www.w3.org/2000/svg" font-family="inherit">',
        '<defs><marker id="fracarrow" markerWidth="7" markerHeight="7" refX="3.5" refY="3.5" '
        'orient="auto"><path d="M0,0 L7,3.5 L0,7 z" fill="#c0392b"/></marker></defs>',
        frac_block(x1, left_n, left_d),
        f'<text x="{mid_x}" y="{y_line + 8}" text-anchor="middle" font-size="26" font-weight="bold" fill="#222">=</text>',
        frac_block(x2, right_n, right_d),
        f'<path d="M{x1},{y_num - 28} Q{mid_x},{top_arc_y} {x2},{y_num - 28}" fill="none" stroke="#c0392b" stroke-width="2" marker-end="url(#fracarrow)"/>',
        f'<text x="{mid_x}" y="{top_arc_y - 6}" text-anchor="middle" font-size="14" fill="#c0392b" font-weight="bold">{op}{scale}</text>',
        f'<path d="M{x1},{y_den + 26} Q{mid_x},{bot_arc_y} {x2},{y_den + 26}" fill="none" stroke="#c0392b" stroke-width="2" marker-end="url(#fracarrow)"/>',
        f'<text x="{mid_x}" y="{bot_arc_y + 18}" text-anchor="middle" font-size="14" fill="#c0392b" font-weight="bold">{op}{scale}</text>',
        "</svg>",
    ]
    return "".join(svg)


def fraction_scale_arrows(num: int, den: int, scale: int, direction: str = "up") -> str:
    return _wrap(_fraction_scale_arrows_inner(num, den, scale, direction))


def _fraction_simplify_single_arrow_inner(big_num: int, big_den: int) -> str:
    hcf = math.gcd(big_num, big_den)
    return _fraction_scale_arrows_inner(big_num // hcf, big_den // hcf, hcf, direction="down", blank_right=True)


def fraction_simplify_single_arrow(big_num: int, big_den: int) -> str:
    """An unsimplified fraction going straight to its simplest form in one
    step — a single ÷HCF arrow pair, rather than a multi-step chain of
    smaller common factors."""
    return _wrap(_fraction_simplify_single_arrow_inner(big_num, big_den))


def _fraction_simplify_wall_inner(big_num: int, big_den: int) -> str:
    """The question's own fraction as a shaded wall row (given), above a
    second row already split into the *simplified* number of parts but
    left unshaded — the pupil counts the parts and works out how many to
    shade themselves; no digits are written anywhere for the second row,
    including the denominator. Never shades the second row itself, unlike
    `fraction_wall_two_rows`, which would give the answer away outright."""
    hcf = math.gcd(big_num, big_den)
    small_den = big_den // hcf
    top = _fraction_row_cells(big_num, big_den)
    bottom = _fraction_row_cells(0, small_den)
    return (
        '<div style="display:flex;flex-direction:column;gap:10px;">'
        f'<div>{top}</div>'
        f'<div>{bottom}</div>'
        '</div>'
    )


def fraction_simplify_wall(big_num: int, big_den: int) -> str:
    return _wrap(_fraction_simplify_wall_inner(big_num, big_den))


def _fraction_simplify_circles_inner(big_num: int, big_den: int) -> str:
    """As `_fraction_simplify_wall_inner`, but two circles instead of two
    wall rows — the second circle is split into the simplified number of
    slices but left unshaded, with no digits written for it at all."""
    hcf = math.gcd(big_num, big_den)
    small_den = big_den // hcf
    left = _pie_svg(big_num, big_den)
    right_pie = _pie_svg(0, small_den)
    return (
        '<div style="display:flex;align-items:center;gap:24px;">'
        f'{left}<div style="font-size:1.8rem;font-weight:800;">=</div>{right_pie}</div>'
    )


def fraction_simplify_circles(big_num: int, big_den: int) -> str:
    return _wrap(_fraction_simplify_circles_inner(big_num, big_den))


def _fraction_double_number_line_inner(num: int, den: int, scale: int) -> str:
    """Worked example as a double number line: the scaled fraction on the
    top line (den×scale divisions, every tick labelled) and the original
    on the bottom line (den divisions), both shaded from 0 to the same
    point so the two fractions visibly line up — then `num/den × s/s =
    scaled` underneath. Always used with demo numbers, never the
    question's own, so it never gives the answer away."""
    big_n, big_d = num * scale, den * scale
    W, pad = 400, 22
    L, R = pad, W - pad

    def x(frac: float) -> float:
        return L + frac * (R - L)

    def label(xp: float, y: float, n, d) -> str:
        if d is None:
            return f'<text x="{xp:.1f}" y="{y + 12}" text-anchor="middle" font-size="14" fill="#222">{n}</text>'
        return (
            f'<text x="{xp:.1f}" y="{y}" text-anchor="middle" font-size="13" fill="#222">{n}</text>'
            f'<line x1="{xp - 6:.1f}" y1="{y + 4}" x2="{xp + 6:.1f}" y2="{y + 4}" stroke="#222" stroke-width="1.2"/>'
            f'<text x="{xp:.1f}" y="{y + 18}" text-anchor="middle" font-size="13" fill="#222">{d}</text>'
        )

    def line(y: int, parts: int, shade_to: int) -> str:
        out = [
            f'<rect x="{L}" y="{y - 6}" width="{x(shade_to / parts) - L:.1f}" height="12" fill="#a3c9f9" stroke="#2e6da4" stroke-width="1.5"/>',
            f'<line x1="{L}" y1="{y}" x2="{R}" y2="{y}" stroke="#222" stroke-width="2"/>',
        ]
        for i in range(parts + 1):
            xp = x(i / parts)
            end = i in (0, parts)
            out.append(f'<line x1="{xp:.1f}" y1="{y - (11 if end else 8)}" x2="{xp:.1f}" y2="{y + (11 if end else 8)}" stroke="#222" stroke-width="{2 if end else 1.5}"/>')
            if i == 0:
                out.append(label(xp, y + 16, 0, None))
            elif i == parts:
                out.append(label(xp, y + 16, 1, None))
            else:
                out.append(label(xp, y + 24, i, parts))
        return "".join(out)

    y1, y2 = 24, 94
    nl = (
        f'<svg width="{W}" height="148" viewBox="0 0 {W} 148" xmlns="http://www.w3.org/2000/svg" font-family="inherit">'
        + line(y1, big_d, big_n) + line(y2, den, num) + "</svg>"
    )
    eq = (
        '<div style="display:flex;align-items:center;justify-content:center;font-size:1.5rem;font-weight:700;margin-top:6px;">'
        f'{fraction_html(num, den)}<span style="margin:0 4px;">&times;</span>'
        f'{fraction_html(scale, scale)}<span style="margin:0 4px;">=</span>{fraction_html(big_n, big_d)}</div>'
    )
    return f'<div>{nl}{eq}</div>'


def fraction_equivalent_scaffold(real_num: int, real_den: int, kind: str) -> str:
    """'Equivalent fractions' scaffold, rotating between three generic
    demo styles. The wall is already a two-row "before/after" picture on
    its own, so it's shown alone; circles and arrows aren't a natural
    pair by themselves, so those are paired with the question's own
    known fraction as a real bar (kept visually separate) so the
    picture still relates to the actual question. None of the styles
    ever give away the missing value."""
    demo_num, demo_den, demo_scale = 3, 5, 3
    if kind == "wall":
        demo = _fraction_wall_two_rows_inner(demo_num, demo_den, demo_num * demo_scale, demo_den * demo_scale)
        return _wrap(demo)
    elif kind == "circles":
        demo = _fraction_circles_pair_inner(demo_num, demo_den, demo_num * demo_scale, demo_den * demo_scale)
    elif kind == "numberline":
        demo = _fraction_double_number_line_inner(3, 4, 2)
    else:
        demo = _fraction_scale_arrows_inner(demo_num, demo_den, demo_scale, direction="up")
    return fraction_matches_question(real_num, real_den, demo)


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
        f'<rect x="1" y="1" width="{_DIENES_UNIT}" height="{_DIENES_UNIT}" rx="2" fill="#a3c9f9" stroke="#2e6da4"/>'
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


def near_double_partition(lo: int, extra: int) -> str:
    """Near doubles as a two-step flow: "double lo" → blank box → "+extra"
    arrow → blank box. Only the smaller number and the extra are printed."""
    box = ('<span style="display:inline-block;width:52px;height:36px;border:2px solid #2b2b2b;'
           'border-radius:5px;vertical-align:middle;box-sizing:border-box;"></span>')

    def arrow(label: str) -> str:
        return ('<div style="display:flex;flex-direction:column;align-items:center;margin:0 10px;">'
                f'<span style="font-size:0.95rem;font-weight:700;color:#2e6da4;">{label}</span>'
                '<svg width="56" height="14" viewBox="0 0 56 14"><line x1="2" y1="7" x2="46" y2="7" stroke="#2e6da4" stroke-width="2.5"/>'
                '<path d="M44,1 L54,7 L44,13 z" fill="#2e6da4"/></svg></div>')

    inner = (
        '<div style="display:flex;align-items:center;flex-wrap:wrap;font-size:1.3rem;font-weight:700;">'
        f'<span>double {lo}</span>{arrow("&nbsp;")}{box}{arrow(f"+{extra}")}{box}</div>'
    )
    return _wrap(inner)


def near_double_number_line(lo: int, extra: int) -> str:
    """Empty number line for near doubles: 0, two equal "+lo" hops, then a
    small "+extra" hop. `lo` is printed; the double (blue box) and the
    final answer (red box) are blank."""
    W, H, y = 580, 136, 92
    xs = [40, 245, 450, 540]
    labels = [f"+{lo}", f"+{lo}", f"+{extra}"]
    colors = ["#2e6da4", "#2e6da4", "#c0392b"]
    parts = [
        f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" font-family="inherit">',
        '<defs><marker id="ndnl" markerWidth="10" markerHeight="10" refX="8" refY="4" orient="auto" markerUnits="userSpaceOnUse">'
        '<path d="M0,0 L8,4 L0,8 z" fill="#222"/></marker></defs>',
        f'<line x1="10" y1="{y}" x2="{W - 10}" y2="{y}" stroke="#222" stroke-width="2"/>',
    ]
    for i in range(3):
        xa, xb = xs[i], xs[i + 1]
        mid, arc = (xa + xb) / 2, (70 if i < 2 else 40)
        parts.append(f'<path d="M{xa},{y} Q{mid},{y - arc} {xb},{y}" fill="none" stroke="{colors[i]}" stroke-width="2.5" marker-end="url(#ndnl)"/>')
        parts.append(f'<text x="{mid}" y="{y - arc / 2 - 8}" text-anchor="middle" font-size="16" font-weight="bold" fill="{colors[i]}">{labels[i]}</text>')
    for xv in xs:
        parts.append(f'<line x1="{xv}" y1="{y - 8}" x2="{xv}" y2="{y + 8}" stroke="#222" stroke-width="2"/>')
    parts.append(f'<text x="{xs[0]}" y="{y + 29}" text-anchor="middle" font-size="14" font-weight="bold" fill="#222">0</text>')
    parts.append(f'<text x="{xs[1]}" y="{y + 29}" text-anchor="middle" font-size="14" font-weight="bold" fill="#222">{lo}</text>')
    parts.append(f'<rect x="{xs[2] - 20}" y="{y + 12}" width="40" height="26" rx="4" fill="#fff" stroke="#2e6da4" stroke-width="2"/>')
    parts.append(f'<rect x="{xs[3] - 20}" y="{y + 12}" width="40" height="26" rx="4" fill="#fff" stroke="#c0392b" stroke-width="2"/>')
    parts.append("</svg>")
    return _wrap("".join(parts))


# ------------------------------------------------------------- place value grid
def _place_value_grid_inner(number_str: str, headers: list[str], highlight: int | None = None,
                             blank: bool = False) -> str:
    digits = list(number_str)
    cells_h, cells_d = [], []
    for i, h in enumerate(headers):
        d = "" if blank else digits[i]
        bg = "#ffe08a" if highlight == i else "#f0f0f0"
        cells_h.append(f'<div style="border:1px solid #333;padding:8px 12px;text-align:center;font-size:1.05rem;background:#ddd;">{html.escape(h)}</div>')
        cells_d.append(f'<div style="border:1px solid #333;padding:14px;text-align:center;font-size:1.8rem;min-height:1.4em;background:{bg};font-weight:bold;">{html.escape(d)}</div>')
    n = len(headers)
    # `width`, not `max-width` — see rounding_sig_figs_chart_decimal's
    # `grid()` helper for why max-width lets rows of different intrinsic
    # content width drift out of column alignment with each other.
    grid_h = f'<div style="display:grid;grid-template-columns:repeat({n},1fr);width:{n*92}px;">{"".join(cells_h)}</div>'
    grid_d = f'<div style="display:grid;grid-template-columns:repeat({n},1fr);width:{n*92}px;">{"".join(cells_d)}</div>'
    return grid_h + grid_d


def place_value_grid(number_str: str, headers: list[str], highlight: int | None = None,
                      note: str | None = None, blank: bool = False) -> str:
    return _wrap(_place_value_grid_inner(number_str, headers, highlight, blank), note)


_PV_HEADERS_WHOLE = ["M", "HTh", "TTh", "Th", "H", "T", "O"]


def rounding_sig_figs_chart_whole(value: int, sig: int, scaffolded: bool = False,
                                   with_number_line: bool = False) -> str:
    """For rounding a whole number (≥1) to `sig` significant figures: a
    place-value grid with the number's own digits on one line and a
    second line below for the rounded answer — the `sig` leftmost (most
    significant) columns are shaded, since those are the ones that will
    hold a real digit; the remaining columns to the right are left
    unshaded, since rounding to `sig` figures always turns them to zero.
    Never fills in a shaded (significant) cell or states the rounded
    value. With `scaffolded=True` (a heavier level of support), the
    unshaded zero columns are pre-filled with "0" in the answer row,
    leaving only the shaded, actually-changing digits blank — rather than
    leaving the whole answer row empty. With `with_number_line=True` (only
    sensible alongside `scaffolded=True`, where the chart has already
    given away most of the structure), a number line spanning the two
    rounding bounds is added below, WITH the value's own position marked
    — unlike the standalone rounding number lines elsewhere, which hide
    it; here it's a deliberate extra rung of support, not an oversight."""
    number_str = str(value)
    n = len(number_str)
    headers = _PV_HEADERS_WHOLE[-n:] if n <= len(_PV_HEADERS_WHOLE) else [str(i) for i in range(n)]

    def row(digits: str | None, prefill_zeros: bool = False) -> str:
        cells = []
        for i, h in enumerate(headers):
            shaded = i < sig
            bg = "#ffe08a" if shaded else "#f0f0f0"
            if digits is not None:
                d = digits[i]
            elif prefill_zeros and not shaded:
                d = "0"
            else:
                d = ""
            cells.append(
                f'<div style="border:1px solid #333;padding:14px;text-align:center;'
                f'font-size:1.8rem;min-height:1.4em;background:{bg};font-weight:bold;">{html.escape(d)}</div>'
            )
        return f'<div style="display:grid;grid-template-columns:repeat({n},1fr);width:{n*92}px;">{"".join(cells)}</div>'

    header_cells = "".join(
        f'<div style="border:1px solid #333;padding:8px 12px;text-align:center;font-size:1.05rem;background:#ddd;">{html.escape(h)}</div>'
        for h in headers
    )
    header_row = f'<div style="display:grid;grid-template-columns:repeat({n},1fr);width:{n*92}px;">{header_cells}</div>'
    inner = header_row + row(number_str) + row(None, prefill_zeros=scaffolded)
    if with_number_line:
        lower, upper, power = _sig_fig_bounds(float(value), sig)
        fmt = (lambda v: f"{v:.{power}f}") if power >= 0 else (lambda v: f"{v:g}")
        fmt_mid = (lambda v: f"{v:.{power+1}f}") if power >= 0 else fmt
        line = _number_line_with_value_core(lower, upper, float(value), fmt, fmt_mid)
        inner += f'<div style="margin-top:14px;">{line}</div>'
    return _wrap(inner)


_PV_HEADERS_DECIMAL = ["t", "h", "th", "tth", "hth", "mth"]


def rounding_sig_figs_chart_decimal(value: float, sig: int, scaffolded: bool = False,
                                     with_number_line: bool = False) -> str:
    """As `rounding_sig_figs_chart_whole`, but for a value strictly
    between 0 and 1 — here the leading zeros right after the decimal
    point don't count as significant figures at all; the pupil has to
    skip over them and start counting from the first non-zero digit.
    Those leading-zero columns are shown unshaded and (when
    `scaffolded=True`) pre-filled with "0" since they're fixed
    place-holders, not something to work out — exactly parallel to the
    trailing zero columns in the whole-number version, just at the other
    end of the number. One extra digit beyond the `sig` significant
    columns is shown (unshaded) in the given row — it's the digit the
    pupil needs to look at to decide whether to round up — but in
    `scaffolded` mode its answer-row cell is blacked out rather than left
    merely blank, since (unlike the other blank cells) there's nothing
    to write there at all: the rounded value simply stops before that
    column, so an ordinary blank cell would wrongly suggest a digit still
    belongs there. `with_number_line` adds the same value-marked number
    line as the heavily-scaffolded whole-number version, reusing the same
    `_sig_fig_bounds` math — it already generalises correctly to values
    below 1."""
    digits_str = f"{value:.10f}".split(".")[1]
    leading_zeros = 0
    for ch in digits_str:
        if ch == "0":
            leading_zeros += 1
        else:
            break
    n = min(leading_zeros + sig + 1, len(digits_str))
    digits = digits_str[:n]
    headers = _PV_HEADERS_DECIMAL[:n] if n <= len(_PV_HEADERS_DECIMAL) else [str(i + 1) for i in range(n)]
    answer_cols = leading_zeros + sig  # the extra context digit has no answer-row cell at all

    def cell(bg: str, d: str) -> str:
        return (
            f'<div style="border:1px solid #333;padding:14px;text-align:center;'
            f'font-size:1.8rem;min-height:1.4em;background:{bg};font-weight:bold;">{html.escape(d)}</div>'
        )

    header_cells = "".join(
        f'<div style="border:1px solid #333;padding:8px 12px;text-align:center;font-size:1.05rem;background:#ddd;">{html.escape(h)}</div>'
        for h in headers
    )
    given_cells, answer_cells = [], []
    for i in range(n):
        shaded = leading_zeros <= i < leading_zeros + sig
        bg = "#ffe08a" if shaded else "#f0f0f0"
        given_cells.append(cell(bg, digits[i]))
        if i >= answer_cols:
            if scaffolded:
                answer_cells.append(
                    '<div style="border:1px solid #333;background:#222;min-height:1.4em;"></div>'
                )
            else:
                answer_cells.append(cell(bg, ""))
        elif i < leading_zeros and scaffolded:
            answer_cells.append(cell(bg, "0"))
        else:
            answer_cells.append(cell(bg, ""))

    def grid(cells: list[str]) -> str:
        # `width` (not `max-width`) — a grid container otherwise shrinks to
        # fit its content, so the header row (smaller padding/font than
        # the digit rows) would render narrower and the columns would
        # drift out of alignment with the row below.
        return f'<div style="display:grid;grid-template-columns:repeat({n},1fr);width:{n*92}px;">{"".join(cells)}</div>'

    header_row = grid([
        f'<div style="border:1px solid #333;padding:8px 12px;text-align:center;font-size:1.05rem;background:#ddd;">{html.escape(h)}</div>'
        for h in headers
    ])
    zero_point_style = 'font-size:1.8rem;font-weight:bold;padding:14px 6px 14px 0;'
    zero_point = f'<div style="{zero_point_style}">0.</div>'
    # An invisible twin of the "0." prefix, same width, so the header row
    # (which has no prefix of its own) still lines up column-for-column
    # with the digit rows below it rather than guessing a margin.
    zero_point_ghost = f'<div style="{zero_point_style}visibility:hidden;">0.</div>'
    # "0." is repeated on both digit rows (not shared/centred across
    # them) — each row is its own number and reads as one, "0. 0 0 4 5 3".
    rows = (
        f'<div style="display:flex;align-items:stretch;">{zero_point_ghost}{header_row}</div>'
        f'<div style="display:flex;align-items:stretch;">{zero_point}{grid(given_cells)}</div>'
        f'<div style="display:flex;align-items:stretch;">{zero_point}{grid(answer_cells)}</div>'
    )
    if with_number_line:
        lower, upper, power = _sig_fig_bounds(value, sig)
        fmt = (lambda v: f"{v:.{power}f}") if power >= 0 else (lambda v: f"{v:g}")
        fmt_mid = (lambda v: f"{v:.{power+1}f}") if power >= 0 else fmt
        line = _number_line_with_value_core(lower, upper, value, fmt, fmt_mid)
        rows += f'<div style="margin-top:14px;">{line}</div>'
    return _wrap(rows)


def place_value_grid_with_demo(number_str: str, headers: list[str],
                                demo_number_str: str, demo_words: str) -> str:
    """The question's place-value grid (blank, ready to fill in) set apart
    from a fully worked example of a different number, so a pupil can see
    the method — write each group's digits into its column — before
    tackling their own, without mistaking the demo's digits for theirs."""
    blank_grid = _place_value_grid_inner(number_str, headers, blank=True)
    demo_headers = headers[-len(demo_number_str):]
    demo_grid = _place_value_grid_inner(demo_number_str, demo_headers)
    inner = (
        '<div style="display:flex;align-items:flex-start;flex-wrap:wrap;gap:24px;">'
        f'<div>{blank_grid}</div>'
        f'<div style="padding-left:24px;border-left:2px dashed #ccc;">'
        f'<div style="font-size:1.05rem;color:#666;margin-bottom:6px;">{html.escape(demo_words)}</div>'
        f'{demo_grid}</div>'
        '</div>'
    )
    return _wrap(inner)


# --------------------------------------------------- place value (periods)
_PERIOD_NAMES = ["", "thousand", "million", "billion"]
_PERIOD_COLORS = ["#e8b93d", "#e0793a", "#c0392b", "#8e44ad"]


def _period_groups(number_str: str) -> list[str]:
    digits, groups = number_str, []
    while digits:
        groups.insert(0, digits[-3:])
        digits = digits[:-3]
    return groups


def _period_block(group: str, color: str, label: str, blank: bool) -> str:
    cells = []
    for ch in group:
        val = "" if blank else ch
        cells.append(
            '<div style="border:2px solid #333;width:56px;height:70px;display:flex;'
            'align-items:center;justify-content:center;font-size:2.4rem;font-weight:bold;'
            f'background:#fff;">{html.escape(val)}</div>'
        )
    row = f'<div style="display:flex;gap:3px;">{"".join(cells)}</div>'
    if label:
        label_html = (
            f'<div style="margin-top:6px;background:{color};color:#fff;text-align:center;'
            f'font-size:1.05rem;font-weight:bold;padding:5px 6px;border-radius:5px;">{html.escape(label)}</div>'
        )
    else:
        label_html = '<div style="margin-top:6px;height:1.9em;"></div>'
    return f'<div>{row}{label_html}</div>'


def _place_value_periods_inner(number_str: str, blank: bool) -> str:
    groups = _period_groups(number_str)
    n = len(groups)
    parts = []
    for i, g in enumerate(groups):
        idx_from_right = n - 1 - i
        color = _PERIOD_COLORS[idx_from_right % len(_PERIOD_COLORS)]
        label = _PERIOD_NAMES[idx_from_right] if idx_from_right < len(_PERIOD_NAMES) else ""
        if i > 0:
            parts.append('<div style="font-size:2.6rem;font-weight:bold;align-self:flex-start;margin:10px 6px 0;">,</div>')
        parts.append(_period_block(g, color, label, blank))
    return f'<div style="display:flex;align-items:flex-start;">{"".join(parts)}</div>'


def place_value_periods(number_str: str, note: str | None = None, blank: bool = False) -> str:
    """A place-value scaffold that groups digits into colour-coded periods
    of three (ones / thousand / million / ...) rather than one column per
    digit — the "big numbers" reading/writing method: split into periods,
    then read or write each period as its own 3-digit chunk."""
    return _wrap(_place_value_periods_inner(number_str, blank), note)


def place_value_periods_with_demo(number_str: str, demo_number_str: str, demo_words: str) -> str:
    """The question's period-grouped place-value scaffold (blank, ready to
    fill in) set apart from a fully worked example of a different number."""
    blank_grid = _place_value_periods_inner(number_str, blank=True)
    demo_grid = _place_value_periods_inner(demo_number_str, blank=False)
    inner = (
        '<div style="display:flex;align-items:flex-start;flex-wrap:wrap;gap:24px;">'
        f'<div>{blank_grid}</div>'
        f'<div style="padding-left:24px;border-left:2px dashed #ccc;">'
        f'<div style="font-size:1.05rem;color:#666;margin-bottom:6px;">{html.escape(demo_words)}</div>'
        f'{demo_grid}</div>'
        '</div>'
    )
    return _wrap(inner)


# --------------------------------------------------------- place value shift
def place_value_shift(int_part: list[int], dec_part: list[int], shift: int, direction: str) -> str:
    """A bordered place-value grid (ten-thousands down to thousandths,
    with its own narrow column for the decimal point) — a green header
    row, the number's digits placed in their columns underneath, and a
    second, blank row below with a straight arrow from each digit down
    into the column it moves to: `shift` places left (multiplying by a
    power of 10) or right (dividing). The second row is left for the
    pupil to fill in themselves."""
    labels = ["TTh", "Th", "H", "T", "O", "•", "t", "h", "th"]
    point_digit_index = 5  # the point sits between digit-index 4 (O) and 5 (t)
    widths = [46, 46, 46, 46, 46, 26, 46, 46, 46]
    n_vis = len(labels)
    x0 = 10

    def vis(digit_index: int) -> int:
        return digit_index if digit_index < point_digit_index else digit_index + 1

    xs = [x0]
    for w in widths:
        xs.append(xs[-1] + w)
    def col_left(vis_i: int) -> float:
        return xs[vis_i]
    def col_center(vis_i: int) -> float:
        return xs[vis_i] + widths[vis_i] / 2

    width = xs[-1] + 10
    header_h, row_h = 32, 42
    y_header0, y_row1_0, y_row2_0 = 6, 6 + header_h, 6 + header_h + row_h
    height = y_row2_0 + row_h + 6

    def cell_rect(vis_i: int, y0: float, h: float, fill: str) -> str:
        return (
            f'<rect x="{col_left(vis_i)}" y="{y0}" width="{widths[vis_i]}" height="{h}" '
            f'fill="{fill}" stroke="#333" stroke-width="1.5"/>'
        )

    svg = [
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
        f'xmlns="http://www.w3.org/2000/svg" font-family="inherit">',
        '<defs><marker id="pvarrow" markerWidth="7" markerHeight="7" refX="3.5" refY="3.5" '
        'orient="auto"><path d="M0,0 L7,3.5 L0,7 z" fill="#3d8b3d"/></marker></defs>',
    ]

    for vis_i in range(n_vis):
        svg.append(cell_rect(vis_i, y_header0, header_h, "#a9d8a6"))
        svg.append(cell_rect(vis_i, y_row1_0, row_h, "#fff"))
        svg.append(cell_rect(vis_i, y_row2_0, row_h, "#fff"))
        svg.append(f'<text x="{col_center(vis_i)}" y="{y_header0 + header_h / 2 + 5}" text-anchor="middle" font-size="15" font-weight="bold" fill="#1c1c1c">{labels[vis_i]}</text>')

    point_vis = point_digit_index
    svg.append(f'<text x="{col_center(point_vis)}" y="{y_row1_0 + row_h / 2 + 6}" text-anchor="middle" font-size="20" font-weight="bold" fill="#222">•</text>')
    svg.append(f'<text x="{col_center(point_vis)}" y="{y_row2_0 + row_h / 2 + 6}" text-anchor="middle" font-size="20" font-weight="bold" fill="#222">•</text>')

    digit_cols: dict[int, int] = {}
    offset = 4 - (len(int_part) - 1)
    for i, d in enumerate(int_part):
        digit_cols[offset + i] = d
    for i, d in enumerate(dec_part):
        digit_cols[5 + i] = d

    for c, d in digit_cols.items():
        svg.append(f'<text x="{col_center(vis(c))}" y="{y_row1_0 + row_h / 2 + 6}" text-anchor="middle" font-size="20" font-weight="bold" fill="#222">{d}</text>')

    for c in sorted(digit_cols):
        target = c - shift if direction == "left" else c + shift
        xa, ya = col_center(vis(c)), y_row1_0 + row_h - 6
        xb, yb = col_center(vis(target)), y_row2_0 + 8
        svg.append(f'<line x1="{xa}" y1="{ya}" x2="{xb}" y2="{yb}" stroke="#3d8b3d" stroke-width="2" marker-end="url(#pvarrow)"/>')

    svg.append("</svg>")
    return _wrap("".join(svg))


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


def factor_check_prompt(n: int, candidate: int) -> str:
    """A factors question: just the worded rule on its own, no picture —
    a deliberate exception to the usual "no text" scaffolds (same
    reasoning as `subtract_negative_number_line`), and deliberately
    without the bus-stop division visual too: tried paired with one
    during review and the text alone was preferred."""
    rule = (
        '<div style="text-align:center;font-size:1.3rem;font-weight:700;'
        f'color:#1b3a5c;">If it divides exactly (no remainder), {candidate} is a factor of {n}.</div>'
    )
    return _wrap(rule)


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
                svg.append(f'<text x="{x0 + cell * 0.32}" y="{y0 + cell * 0.4}" text-anchor="middle" font-size="16" fill="#1a1a1a">{tens}</text>')
                svg.append(f'<text x="{x0 + cell * 0.68}" y="{y0 + cell * 0.82}" text-anchor="middle" font-size="16" fill="#1a1a1a">{ones}</text>')
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
            svg.append(f'<text x="{x0 + cell * 0.32}" y="{y0 + cell * 0.4}" text-anchor="middle" font-size="16" fill="#1a1a1a">{tens}</text>')
            svg.append(f'<text x="{x0 + cell * 0.68}" y="{y0 + cell * 0.82}" text-anchor="middle" font-size="16" fill="#1a1a1a">{ones}</text>')

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

    # Each digit sits on the actual continuation of its own diagonal line,
    # a short tail past the real point where that diagonal meets the grid's
    # edge — not at an arbitrary fixed row/column offset. Diagonal 0's line
    # meets the bottom edge one cell in from the left; diagonal 1's line
    # runs corner-to-corner and meets the bottom-left corner itself;
    # diagonals 2 and 3 meet the left edge at one and zero cells down. All
    # four tails point the same way (down-left), following the line's slope.
    tail = 16
    boundary_points = [
        (ox + cell, oy + grid_h),
        (ox, oy + grid_h),
        (ox, oy + cell),
        (ox, oy),
    ]
    anchors = [
        (ox + cell - tail, oy + grid_h + tail),
        (ox - tail, oy + grid_h + tail),
        (ox - tail, oy + cell + tail),
        (ox - tail, oy + tail),
    ]
    for (bx, by), (ax, ay) in zip(boundary_points, anchors):
        svg.append(f'<line x1="{bx}" y1="{by}" x2="{ax}" y2="{ay}" stroke="#333" stroke-width="1"/>')
    for i in range(n_diag):
        x, y = anchors[i] if i < len(anchors) else anchors[-1]
        if carry_ins[i] > 0:
            if i == 2:
                # Carried into the hundreds diagonal: shown in the same
                # tens-triangle as the bottom-left cell's tens digit (one of
                # that diagonal's own contributors), tucked into the far
                # (bottom-left) corner of that triangle rather than crowding
                # the digit itself.
                cx, cy = ox + 10, oy + 2 * cell - 12
            elif i == 3:
                # Carried into the thousands diagonal: shown in the far
                # corner of the top-left cell's tens-triangle.
                cx, cy = ox + 10, oy + cell - 12
            else:
                cx, cy = x - 13, y - 12
            svg.append(f'<text x="{cx}" y="{cy}" text-anchor="middle" font-size="11" fill="#c0392b">{carry_ins[i]}</text>')
        # Per-digit nudge off the line tip: the bottom two sit further right
        # of their line, the left two sit down-and-left of theirs.
        dx, dy = {0: (16, 6), 1: (16, 6), 2: (-2, 14), 3: (-2, 14)}.get(i, (6, 6))
        svg.append(f'<text x="{x + dx}" y="{y + dy}" text-anchor="start" font-size="18" font-weight="bold" fill="#222">{digits[i]}</text>')

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


def hundred_square_bond(known: int) -> str:
    """For "known + ☐ = 100": a 1–100 grid with 1 to `known` shaded light
    blue (`known` itself in bold with a dark outline) and the rest left
    white — the white squares are the gap to 100, for the pupil to count
    (a row at a time once they reach a ten)."""
    cells = []
    for i in range(1, 101):
        shaded = i <= known
        edge = "2px solid #2e6da4" if i == known else "1px solid #ccc"
        cells.append(
            f'<div style="width:26px;height:26px;display:flex;align-items:center;justify-content:center;'
            f'font-size:11px;border:{edge};box-sizing:border-box;background:{"#a3c9f9" if shaded else "#fff"};'
            f'color:#222;font-weight:{"bold" if i == known else "normal"};">{i}</div>'
        )
    grid = f'<div style="display:grid;grid-template-columns:repeat(10,26px);gap:1px;width:269px;">{"".join(cells)}</div>'
    return _wrap(grid)


def bridge_to_100_number_line(known: int) -> str:
    """For "known + ☐ = 100": an empty (not-to-scale) number line with
    just three marks — `known` (circled), the next ten, and 100 — and a
    dashed "?" hop between each, the "make the next ten, then count on in
    tens" method. Not to scale on purpose: at true scale the hop to the
    next ten is too small to see. If `known` is already a multiple of 10
    there's one hop straight to 100."""
    next_ten = -(-known // 10) * 10
    W, H, y = 560, 136, 92
    marks = [(known, 40)]
    if next_ten not in (known, 100):
        marks.append((next_ten, 210))
    marks.append((100, 520))
    colors = ["#2e6da4", "#c0392b"]
    parts = [
        f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" font-family="inherit">',
        '<defs><marker id="ennl" markerWidth="10" markerHeight="10" refX="8" refY="4" orient="auto" markerUnits="userSpaceOnUse">'
        '<path d="M0,0 L8,4 L0,8 z" fill="#222"/></marker></defs>',
        f'<line x1="10" y1="{y}" x2="{W - 10}" y2="{y}" stroke="#222" stroke-width="2"/>',
    ]
    for i in range(len(marks) - 1):
        (_, xa), (_, xb) = marks[i], marks[i + 1]
        mid, c = (xa + xb) / 2, colors[i % 2]
        parts.append(f'<path d="M{xa},{y} Q{mid},{y - 70} {xb},{y}" fill="none" stroke="{c}" stroke-width="2.5" stroke-dasharray="5,4" marker-end="url(#ennl)"/>')
        parts.append(f'<text x="{mid}" y="{y - 42}" text-anchor="middle" font-size="16" font-weight="bold" fill="{c}">?</text>')
    for v, xv in marks:
        parts.append(f'<line x1="{xv}" y1="{y - 8}" x2="{xv}" y2="{y + 8}" stroke="#222" stroke-width="2"/>')
        if v == known:
            parts.append(f'<circle cx="{xv}" cy="{y + 24}" r="15" fill="none" stroke="#c0392b" stroke-width="2"/>')
            parts.append(f'<text x="{xv}" y="{y + 29}" text-anchor="middle" font-size="14" font-weight="bold" fill="#c0392b">{v}</text>')
        else:
            parts.append(f'<text x="{xv}" y="{y + 29}" text-anchor="middle" font-size="14" font-weight="bold" fill="#222">{v}</text>')
    parts.append("</svg>")
    return _wrap("".join(parts))


def hundred_square_step(n: int, step: int) -> str:
    """For "n + 10" / "n − 10" (step = ±10): a 1–100 square with `n`
    shaded light blue and bold, an arrow one row down (+10) or up (−10),
    and the square it lands on left blank with a red outline — so the
    "same column, next row" pattern is visible without the answer being
    printed."""
    target = n + step
    c, gap, pad = 26, 1, 4
    W = H = 10 * (c + gap) + 2 * pad

    def centre(v):
        r, col = divmod(v - 1, 10)
        return pad + col * (c + gap) + c / 2, pad + r * (c + gap) + c / 2

    parts = [f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" font-family="inherit">',
             '<defs><marker id="hsarr" markerWidth="10" markerHeight="10" refX="8" refY="4" orient="auto" markerUnits="userSpaceOnUse">'
             '<path d="M0,0 L8,4 L0,8 z" fill="#c0392b"/></marker></defs>']
    for v in range(1, 101):
        x, y = centre(v)
        x0, y0 = x - c / 2, y - c / 2
        if v == target:
            parts.append(f'<rect x="{x0}" y="{y0}" width="{c}" height="{c}" fill="#fff" stroke="#c0392b" stroke-width="2.5"/>')
            continue
        fill, weight = ("#a3c9f9", "bold") if v == n else ("#fff", "normal")
        edge = 'stroke="#2e6da4" stroke-width="2"' if v == n else 'stroke="#ccc" stroke-width="1"'
        parts.append(f'<rect x="{x0}" y="{y0}" width="{c}" height="{c}" fill="{fill}" {edge}/>')
        parts.append(f'<text x="{x}" y="{y + 4}" text-anchor="middle" font-size="11" font-weight="{weight}" fill="#222">{v}</text>')
    (x1, y1), (x2, y2) = centre(n), centre(target)
    side = c / 2 + 6  # arrow runs just to the right of the column
    sy = 1 if y2 > y1 else -1
    parts.append(f'<path d="M{x1 + c / 2 - 2},{y1} C{x1 + side + 8},{y1} {x2 + side + 8},{y2} {x2 + c / 2 + 1},{y2}" '
                 f'fill="none" stroke="#c0392b" stroke-width="2" marker-end="url(#hsarr)"/>')
    parts.append("</svg>")
    return _wrap("".join(parts))


def ten_step_number_line(n: int, step: int) -> str:
    """Empty (not-to-scale) number line for "n + 10" / "n − 10": `n`
    circled, one solid hop labelled "+10" or "−10", landing on a blank box
    (to the right for +10, to the left for −10)."""
    W, H, y = 560, 136, 92
    xn, xt = (140, 420) if step > 0 else (420, 140)
    label = f"+{step}" if step > 0 else f"−{-step}"
    parts = [
        f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" font-family="inherit">',
        '<defs><marker id="tsnl" markerWidth="10" markerHeight="10" refX="8" refY="4" orient="auto" markerUnits="userSpaceOnUse">'
        '<path d="M0,0 L8,4 L0,8 z" fill="#222"/></marker></defs>',
        f'<line x1="10" y1="{y}" x2="{W - 10}" y2="{y}" stroke="#222" stroke-width="2"/>',
        f'<path d="M{xn},{y} Q{(xn + xt) / 2},{y - 70} {xt},{y}" fill="none" stroke="#2e6da4" stroke-width="2.5" marker-end="url(#tsnl)"/>',
        f'<text x="{(xn + xt) / 2}" y="{y - 42}" text-anchor="middle" font-size="16" font-weight="bold" fill="#2e6da4">{label}</text>',
    ]
    for xv in (xn, xt):
        parts.append(f'<line x1="{xv}" y1="{y - 8}" x2="{xv}" y2="{y + 8}" stroke="#222" stroke-width="2"/>')
    parts.append(f'<circle cx="{xn}" cy="{y + 24}" r="15" fill="none" stroke="#c0392b" stroke-width="2"/>')
    parts.append(f'<text x="{xn}" y="{y + 29}" text-anchor="middle" font-size="14" font-weight="bold" fill="#c0392b">{n}</text>')
    parts.append(f'<rect x="{xt - 20}" y="{y + 12}" width="40" height="26" rx="4" fill="#fff" stroke="#c0392b" stroke-width="2"/>')
    parts.append("</svg>")
    return _wrap("".join(parts))


def add_9_number_line(n: int) -> str:
    """Empty (not-to-scale) number line for "n + 9" as "+10, then −1":
    `n` circled; a "+10" hop above the line to a blank box; then a "−1"
    hop back underneath the line to a second blank box (the answer).
    The two hops sit on opposite sides of the line so they never overlap."""
    W, H, y = 560, 190, 80
    xn, x9, x10 = 60, 400, 500
    parts = [
        f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" font-family="inherit">',
        '<defs><marker id="a9nl" markerWidth="10" markerHeight="10" refX="8" refY="4" orient="auto" markerUnits="userSpaceOnUse">'
        '<path d="M0,0 L8,4 L0,8 z" fill="#222"/></marker></defs>',
        f'<line x1="10" y1="{y}" x2="{W - 10}" y2="{y}" stroke="#222" stroke-width="2"/>',
        f'<path d="M{xn},{y} Q{(xn + x10) / 2},{y - 70} {x10},{y}" fill="none" stroke="#2e6da4" stroke-width="2.5" marker-end="url(#a9nl)"/>',
        f'<text x="{(xn + x10) / 2}" y="{y - 42}" text-anchor="middle" font-size="16" font-weight="bold" fill="#2e6da4">+10</text>',
        f'<path d="M{x10},{y} Q{(x9 + x10) / 2},{y + 50} {x9},{y}" fill="none" stroke="#c0392b" stroke-width="2.5" marker-end="url(#a9nl)"/>',
        f'<text x="{(x9 + x10) / 2}" y="{y + 52}" text-anchor="middle" font-size="16" font-weight="bold" fill="#c0392b">−1</text>',
    ]
    for xv in (xn, x9, x10):
        parts.append(f'<line x1="{xv}" y1="{y - 8}" x2="{xv}" y2="{y + 8}" stroke="#222" stroke-width="2"/>')
    parts.append(f'<circle cx="{xn}" cy="{y + 24}" r="15" fill="none" stroke="#c0392b" stroke-width="2"/>')
    parts.append(f'<text x="{xn}" y="{y + 29}" text-anchor="middle" font-size="14" font-weight="bold" fill="#c0392b">{n}</text>')
    for xv, col in ((x9, "#c0392b"), (x10, "#2e6da4")):
        parts.append(f'<rect x="{xv - 20}" y="{y + 64}" width="40" height="26" rx="4" fill="#fff" stroke="{col}" stroke-width="2"/>')
        parts.append(f'<line x1="{xv}" y1="{y + 10}" x2="{xv}" y2="{y + 62}" stroke="#bbb" stroke-width="1" stroke-dasharray="3,3"/>')
    parts.append("</svg>")
    return _wrap("".join(parts))


def hundred_square_add_9(n: int) -> str:
    """Hundred square for "n + 9": `n` shaded light blue, an arrow down a
    row to n+10 (dashed outline, number hidden), then an arrow back one
    square to the answer (blank, red outline). Only for n where n+10 ≤ 100
    and n doesn't end in 1 (so the step back stays on the same row)."""
    c, gap, pad = 26, 1, 4
    W = H = 10 * (c + gap) + 2 * pad
    mid, ans = n + 10, n + 9

    def centre(v):
        r, col = divmod(v - 1, 10)
        return pad + col * (c + gap) + c / 2, pad + r * (c + gap) + c / 2

    parts = [f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" font-family="inherit">',
             '<defs><marker id="hs9" markerWidth="10" markerHeight="10" refX="8" refY="4" orient="auto" markerUnits="userSpaceOnUse">'
             '<path d="M0,0 L8,4 L0,8 z" fill="#c0392b"/></marker></defs>']
    for v in range(1, 101):
        x, y = centre(v)
        x0, y0 = x - c / 2, y - c / 2
        if v == ans:
            parts.append(f'<rect x="{x0}" y="{y0}" width="{c}" height="{c}" fill="#fff" stroke="#c0392b" stroke-width="2.5"/>')
            continue
        if v == mid:
            parts.append(f'<rect x="{x0}" y="{y0}" width="{c}" height="{c}" fill="#fff" stroke="#2e6da4" stroke-width="2" stroke-dasharray="3,2"/>')
            continue
        fill, weight = ("#a3c9f9", "bold") if v == n else ("#fff", "normal")
        edge = 'stroke="#2e6da4" stroke-width="2"' if v == n else 'stroke="#ccc" stroke-width="1"'
        parts.append(f'<rect x="{x0}" y="{y0}" width="{c}" height="{c}" fill="{fill}" {edge}/>')
        parts.append(f'<text x="{x}" y="{y + 4}" text-anchor="middle" font-size="11" font-weight="{weight}" fill="#222">{v}</text>')
    (x1, y1), (x2, y2), (x3, y3) = centre(n), centre(mid), centre(ans)
    parts.append(f'<path d="M{x1 + c / 2 - 2},{y1} C{x1 + c / 2 + 14},{y1} {x2 + c / 2 + 14},{y2} {x2 + c / 2 + 1},{y2}" '
                 'fill="none" stroke="#c0392b" stroke-width="2" marker-end="url(#hs9)"/>')
    parts.append(f'<path d="M{x2},{y2 + c / 2 - 2} C{x2},{y2 + c / 2 + 12} {x3},{y3 + c / 2 + 12} {x3},{y3 + c / 2 + 1}" '
                 'fill="none" stroke="#c0392b" stroke-width="2" marker-end="url(#hs9)"/>')
    parts.append("</svg>")
    return _wrap("".join(parts))


def hundred_square_add_9_ok(n: int) -> bool:
    return n + 10 <= 100 and n % 10 != 1


def _dienes_rod_nine() -> str:
    """A ten-rod with its last segment dashed — "10 take away 1"."""
    u = _DIENES_UNIT
    w = u * 10
    svg = [f'<svg width="{w+2}" height="{u+2}" viewBox="0 0 {w+2} {u+2}">',
           f'<rect x="1" y="1" width="{u*9}" height="{u}" rx="2" fill="#4a90d9" stroke="#2c5d8a"/>',
           f'<rect x="{1+u*9}" y="1" width="{u}" height="{u}" rx="2" fill="#e4e4e4" stroke="#999" stroke-width="1.5" stroke-dasharray="3,2"/>']
    svg += [f'<line x1="{1+u*i}" y1="1" x2="{1+u*i}" y2="{u+1}" stroke="#ffffff"/>' for i in range(1, 9)]
    svg.append("</svg>")
    return "".join(svg)


def dienes_add_9(n: int) -> str:
    """Dienes for "n + 9": `n` in blocks, with a ten-rod underneath whose
    last segment is dashed — add a ten, take one away."""
    inner = (f'<div style="display:flex;flex-direction:column;gap:16px;">'
             f'{_dienes_full(n)}<div>{_dienes_rod_nine()}</div></div>')
    return _wrap(inner)


def tens_jumps_number_line(n: int, m: int) -> str:
    """Empty number line for "n ± m" (m a multiple of 10): `n` circled,
    then one equal hop per ten, each labelled "+10" or "−10" (right for
    adding, left for subtracting); the in-between points are plain ticks
    and the landing point is a blank box."""
    W, H, y = 600, 136, 92
    hops = abs(m) // 10
    x_start, x_end = (40, 560) if m > 0 else (560, 40)
    xs = [x_start + (x_end - x_start) * i / hops for i in range(hops + 1)]
    label = "+10" if m > 0 else "−10"
    colors = ["#2e6da4", "#c0392b"]
    parts = [
        f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" font-family="inherit">',
        '<defs><marker id="tjnl" markerWidth="10" markerHeight="10" refX="8" refY="4" orient="auto" markerUnits="userSpaceOnUse">'
        '<path d="M0,0 L8,4 L0,8 z" fill="#222"/></marker></defs>',
        f'<line x1="10" y1="{y}" x2="{W - 10}" y2="{y}" stroke="#222" stroke-width="2"/>',
    ]
    arc = min(60, 20 + 260 / hops)
    for i in range(hops):
        xa, xb = xs[i], xs[i + 1]
        mid, c = (xa + xb) / 2, colors[i % 2]
        parts.append(f'<path d="M{xa:.1f},{y} Q{mid:.1f},{y - arc} {xb:.1f},{y}" fill="none" stroke="{c}" stroke-width="2.5" marker-end="url(#tjnl)"/>')
        parts.append(f'<text x="{mid:.1f}" y="{y - arc / 2 - 8:.1f}" text-anchor="middle" font-size="{14 if hops > 5 else 16}" font-weight="bold" fill="{c}">{label}</text>')
    for xv in xs:
        parts.append(f'<line x1="{xv:.1f}" y1="{y - 8}" x2="{xv:.1f}" y2="{y + 8}" stroke="#222" stroke-width="2"/>')
    parts.append(f'<circle cx="{xs[0]}" cy="{y + 24}" r="15" fill="none" stroke="#c0392b" stroke-width="2"/>')
    parts.append(f'<text x="{xs[0]}" y="{y + 29}" text-anchor="middle" font-size="{14 if n < 100 else 12}" font-weight="bold" fill="#c0392b">{n}</text>')
    parts.append(f'<rect x="{xs[-1] - 20}" y="{y + 12}" width="40" height="26" rx="4" fill="#fff" stroke="#c0392b" stroke-width="2"/>')
    parts.append("</svg>")
    return _wrap("".join(parts))


def empty_hop_line(start: int, end: int) -> str:
    """Empty (not-to-scale) number line with just two marks, `start` and
    `end`, both circled, and one dashed "?" hop between them — for "end =
    start + ☐" when a to-scale line would be too crowded."""
    W, H, y = 560, 136, 92
    xa, xb = 120, 440
    parts = [
        f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" font-family="inherit">',
        '<defs><marker id="ehnl" markerWidth="10" markerHeight="10" refX="8" refY="4" orient="auto" markerUnits="userSpaceOnUse">'
        '<path d="M0,0 L8,4 L0,8 z" fill="#222"/></marker></defs>',
        f'<line x1="10" y1="{y}" x2="{W - 10}" y2="{y}" stroke="#222" stroke-width="2"/>',
        f'<path d="M{xa},{y} Q{(xa + xb) / 2},{y - 70} {xb},{y}" fill="none" stroke="#2e6da4" stroke-width="2.5" stroke-dasharray="5,4" marker-end="url(#ehnl)"/>',
        f'<text x="{(xa + xb) / 2}" y="{y - 42}" text-anchor="middle" font-size="16" font-weight="bold" fill="#2e6da4">?</text>',
    ]
    for xv, v in ((xa, start), (xb, end)):
        parts.append(f'<line x1="{xv}" y1="{y - 8}" x2="{xv}" y2="{y + 8}" stroke="#222" stroke-width="2"/>')
        parts.append(f'<circle cx="{xv}" cy="{y + 24}" r="15" fill="none" stroke="#c0392b" stroke-width="2"/>')
        parts.append(f'<text x="{xv}" y="{y + 29}" text-anchor="middle" font-size="14" font-weight="bold" fill="#c0392b">{v}</text>')
    parts.append("</svg>")
    return _wrap("".join(parts))


def bridge_ten_empty_line(a: int, step1: int, sign: int) -> str:
    """Empty number line for "a ± b = a ± step1 ± ☐" (bridging a ten):
    `a` circled; a solid hop labelled "+step1"/"−step1" to the ten (marked
    and labelled); then a dashed "?" hop on to an unlabelled end mark.
    Adding runs left→right, subtracting right→left."""
    W, H, y = 560, 136, 92
    ten = a + sign * step1
    xs = [60, 260, 500] if sign > 0 else [500, 300, 60]
    sym = "+" if sign > 0 else "−"
    parts = [
        f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" font-family="inherit">',
        '<defs><marker id="btel" markerWidth="10" markerHeight="10" refX="8" refY="4" orient="auto" markerUnits="userSpaceOnUse">'
        '<path d="M0,0 L8,4 L0,8 z" fill="#222"/></marker></defs>',
        f'<line x1="10" y1="{y}" x2="{W - 10}" y2="{y}" stroke="#222" stroke-width="2"/>',
        f'<path d="M{xs[0]},{y} Q{(xs[0] + xs[1]) / 2},{y - 70} {xs[1]},{y}" fill="none" stroke="#2e6da4" stroke-width="2.5" marker-end="url(#btel)"/>',
        f'<text x="{(xs[0] + xs[1]) / 2}" y="{y - 42}" text-anchor="middle" font-size="16" font-weight="bold" fill="#2e6da4">{sym}{step1}</text>',
        f'<path d="M{xs[1]},{y} Q{(xs[1] + xs[2]) / 2},{y - 70} {xs[2]},{y}" fill="none" stroke="#c0392b" stroke-width="2.5" stroke-dasharray="5,4" marker-end="url(#btel)"/>',
        f'<text x="{(xs[1] + xs[2]) / 2}" y="{y - 42}" text-anchor="middle" font-size="16" font-weight="bold" fill="#c0392b">{sym}?</text>',
    ]
    for xv in xs:
        parts.append(f'<line x1="{xv}" y1="{y - 8}" x2="{xv}" y2="{y + 8}" stroke="#222" stroke-width="2"/>')
    parts.append(f'<circle cx="{xs[0]}" cy="{y + 24}" r="15" fill="none" stroke="#c0392b" stroke-width="2"/>')
    parts.append(f'<text x="{xs[0]}" y="{y + 29}" text-anchor="middle" font-size="14" font-weight="bold" fill="#c0392b">{a}</text>')
    parts.append(f'<text x="{xs[1]}" y="{y + 29}" text-anchor="middle" font-size="14" font-weight="bold" fill="#222">{ten}</text>')
    parts.append("</svg>")
    return _wrap("".join(parts))


def dienes_bridge_add(a: int, b: int) -> str:
    """Dienes for "a + b" bridging a ten: `a` in blocks, then b's cubes in
    light blue — the first few fill up a's last ten (in the same row as
    a's ones), the rest sit in a new row underneath to be counted."""
    tens, ones = divmod(a, 10)
    fill = min(b, 10 - ones)
    rods = "".join(f'<div>{_dienes_rod()}</div>' for _ in range(tens))
    row1 = _dienes_cube_row([_dienes_cube() for _ in range(ones)] + [_dienes_cube_blue() for _ in range(fill)])
    row2 = _dienes_cube_row([_dienes_cube_blue() for _ in range(b - fill)])
    inner = f'<div style="display:flex;flex-direction:column;gap:3px;">{rods}{row1}<div style="height:8px"></div>{row2}</div>'
    return _wrap(inner)


def dienes_bridge_subtract(a: int, b: int) -> str:
    """Dienes for "a − b" bridging a ten: `a` in blocks with its loose
    ones dashed (taken first, back to the ten), and the rest of b dashed
    on the end of the last ten-rod."""
    tens, ones = divmod(a, 10)
    take_ones = min(b, ones)
    rest = b - take_ones
    u = _DIENES_UNIT
    rods = [f'<div>{_dienes_rod()}</div>' for _ in range(tens - (1 if rest else 0))]
    if rest:
        w = u * 10
        svg = [f'<svg width="{w+2}" height="{u+2}" viewBox="0 0 {w+2} {u+2}">',
               f'<rect x="1" y="1" width="{u*(10-rest)}" height="{u}" rx="2" fill="#4a90d9" stroke="#2c5d8a"/>']
        for i in range(10 - rest, 10):
            svg.append(f'<rect x="{1+u*i}" y="1" width="{u}" height="{u}" fill="#e4e4e4" stroke="#999" stroke-width="1.5" stroke-dasharray="3,2"/>')
        svg += [f'<line x1="{1+u*i}" y1="1" x2="{1+u*i}" y2="{u+1}" stroke="#ffffff"/>' for i in range(1, 10 - rest)]
        svg.append("</svg>")
        rods.append(f'<div>{"".join(svg)}</div>')
    cubes = _dienes_cube_row([_dienes_cube() for _ in range(ones - take_ones)] + [_dienes_cube_dashed() for _ in range(take_ones)])
    inner = f'<div style="display:flex;flex-direction:column;gap:3px;">{"".join(rods)}{cubes}</div>'
    return _wrap(inner)


def two_hop_empty_line(start: int, hop1: str, hop2: str = "+?") -> str:
    """Empty number line: `start` circled, a solid hop labelled `hop1`
    to an unlabelled mark, then a dashed hop labelled `hop2` to an
    unlabelled end mark. For "a + b = a + tens + ☐"-style splits."""
    W, H, y = 560, 136, 92
    xs = [60, 340, 500]
    parts = [
        f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" font-family="inherit">',
        '<defs><marker id="thel" markerWidth="10" markerHeight="10" refX="8" refY="4" orient="auto" markerUnits="userSpaceOnUse">'
        '<path d="M0,0 L8,4 L0,8 z" fill="#222"/></marker></defs>',
        f'<line x1="10" y1="{y}" x2="{W - 10}" y2="{y}" stroke="#222" stroke-width="2"/>',
        f'<path d="M{xs[0]},{y} Q{(xs[0] + xs[1]) / 2},{y - 70} {xs[1]},{y}" fill="none" stroke="#2e6da4" stroke-width="2.5" marker-end="url(#thel)"/>',
        f'<text x="{(xs[0] + xs[1]) / 2}" y="{y - 42}" text-anchor="middle" font-size="16" font-weight="bold" fill="#2e6da4">{hop1}</text>',
        f'<path d="M{xs[1]},{y} Q{(xs[1] + xs[2]) / 2},{y - 50} {xs[2]},{y}" fill="none" stroke="#c0392b" stroke-width="2.5" stroke-dasharray="5,4" marker-end="url(#thel)"/>',
        f'<text x="{(xs[1] + xs[2]) / 2}" y="{y - 32}" text-anchor="middle" font-size="16" font-weight="bold" fill="#c0392b">{hop2}</text>',
    ]
    for xv in xs:
        parts.append(f'<line x1="{xv}" y1="{y - 8}" x2="{xv}" y2="{y + 8}" stroke="#222" stroke-width="2"/>')
    parts.append(f'<circle cx="{xs[0]}" cy="{y + 24}" r="15" fill="none" stroke="#c0392b" stroke-width="2"/>')
    parts.append(f'<text x="{xs[0]}" y="{y + 29}" text-anchor="middle" font-size="14" font-weight="bold" fill="#c0392b">{start}</text>')
    parts.append("</svg>")
    return _wrap("".join(parts))


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
        # 24-hour, to match the question wording
        return f"{h:02d}:{m:02d}"

    svg = [
        f'<svg viewBox="0 0 {width} {height}" width="100%" height="{height}" '
        f'xmlns="http://www.w3.org/2000/svg" font-family="inherit">',
        f'<line x1="{pad}" y1="{y_line}" x2="{width - pad}" y2="{y_line}" '
        f'stroke="#222" stroke-width="2" marker-end="url(#arrow)"/>',
        '<defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="4" refY="4" '
        'orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#222"/></marker>'
        '<marker id="tlhop" markerWidth="10" markerHeight="10" refX="8" refY="4" orient="auto" markerUnits="userSpaceOnUse">'
        '<path d="M0,0 L8,4 L0,8 z" fill="#222"/></marker></defs>',
    ]
    xs = [pad + i * step_x for i in range(n)]
    for (h, m), xv in zip(stops, xs):
        svg.append(f'<line x1="{xv}" y1="{y_line - 9}" x2="{xv}" y2="{y_line + 9}" stroke="#222" stroke-width="2.5"/>')
        svg.append(
            f'<text x="{xv}" y="{y_line + 28}" text-anchor="middle" font-size="14" '
            f'font-weight="bold" fill="#222">{html.escape(fmt(h, m))}</text>'
        )
    colors = ["#2e6da4", "#c0392b"]
    for i, label in enumerate(jump_labels):
        xa, xb = xs[i], xs[i + 1]
        mid = (xa + xb) / 2
        color = colors[i % len(colors)]
        arc_h = 34
        svg.append(
            f'<path d="M{xa},{y_line} Q{mid},{y_line - arc_h} {xb},{y_line}" '
            f'fill="none" stroke="{color}" stroke-width="2.5" marker-end="url(#tlhop)"/>'
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
    mx, my = point(cx, cy, 48, minute_angle)  # inside the numerals
    hx, hy = point(cx, cy, 32, hour_angle)
    ticks = []
    for i in range(12):
        ang = math.radians(i * 30 - 90)
        x1, y1 = cx + 72 * math.cos(ang), cy + 72 * math.sin(ang)
        x2, y2 = cx + 78 * math.cos(ang), cy + 78 * math.sin(ang)
        ticks.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#333" stroke-width="2"/>')
    numerals = []
    for i in range(1, 13):
        ang = math.radians(i * 30 - 90)
        nx, ny = cx + 60 * math.cos(ang), cy + 60 * math.sin(ang) + 5
        numerals.append(f'<text x="{nx:.1f}" y="{ny:.1f}" text-anchor="middle" font-size="14" font-weight="bold" fill="#222">{i}</text>')
    svg = (
        f'<svg width="180" height="180" viewBox="0 0 180 180">'
        f'<circle cx="{cx}" cy="{cy}" r="80" fill="#fff" stroke="#222" stroke-width="3"/>'
        f'{"".join(ticks)}{"".join(numerals)}'
        f'<line x1="{cx}" y1="{cy}" x2="{hx:.1f}" y2="{hy:.1f}" stroke="#111" stroke-width="5" stroke-linecap="round"/>'
        f'<line x1="{cx}" y1="{cy}" x2="{mx:.1f}" y2="{my:.1f}" stroke="#111" stroke-width="3" stroke-linecap="round"/>'
        f'<circle cx="{cx}" cy="{cy}" r="4" fill="#111"/>'
        f'</svg>'
    )
    return _wrap(svg, note)


def hour_conversion_strip(hour24: int, given: str) -> str:
    """12-hour ↔ 24-hour conversion strip: a header row of 12-hour
    labels (12, 1, …, 11) over an "am" row (00–11) and a "pm" row
    (12–23). The question's hour column is highlighted. given="24": the
    24-hour cell is shown highlighted and the 12-hour header in that column
    is a blank box. given="12": the 12-hour header (with am/pm row label
    highlighted) is shown and the 24-hour cell is a blank box."""
    col = hour24 % 12
    row = "am" if hour24 < 12 else "pm"
    cw = 38
    box = ('<span style="display:inline-block;width:26px;height:20px;border:2px solid #c0392b;'
           'border-radius:4px;vertical-align:middle;box-sizing:border-box;background:#fff;"></span>')
    cell = ("width:%dpx;height:32px;display:flex;align-items:center;justify-content:center;"
            "font-size:0.85rem;box-sizing:border-box;border:1px solid #ccc;" % cw)

    def header(c):
        lab = 12 if c == 0 else c
        if c == col and given == "24":
            return f'<div style="{cell}background:#fff;">{box}</div>'
        hl = "background:#a3c9f9;font-weight:700;border:2px solid #2e6da4;" if c == col and given == "12" else "background:#eee;font-weight:700;"
        return f'<div style="{cell}{hl}">{lab}</div>'

    def body(r, c):
        v = c if r == "am" else c + 12
        if c == col and r == row:
            if given == "12":
                return f'<div style="{cell}background:#fff;">{box}</div>'
            return f'<div style="{cell}background:#a3c9f9;font-weight:700;border:2px solid #2e6da4;">{v:02d}</div>'
        return f'<div style="{cell}background:#fff;">{v:02d}</div>'

    def label(t, hl=False):
        style = "background:#a3c9f9;border:2px solid #2e6da4;" if hl else ""
        return f'<div style="width:46px;height:32px;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:0.85rem;box-sizing:border-box;{style}">{t}</div>'

    rows = [
        label("") + "".join(header(c) for c in range(12)),
        label("am", given == "12" and row == "am") + "".join(body("am", c) for c in range(12)),
        label("pm", given == "12" and row == "pm") + "".join(body("pm", c) for c in range(12)),
    ]
    inner = "".join(f'<div style="display:flex;">{r}</div>' for r in rows)
    return _wrap(f'<div style="display:flex;flex-direction:column;">{inner}</div>')


# ------------------------------------------------------------------ hint list
def hint_list(steps: list[str], note: str | None = None) -> str:
    items = "".join(f"<li style='margin-bottom:6px;'>{s}</li>" for s in steps)
    return _wrap(f'<ol style="margin:0;padding-left:1.3em;">{items}</ol>', note)


def fact_list(lines: list[str], note: str | None = None) -> str:
    items = "".join(f"<div style='margin-bottom:4px;font-size:1.05rem;'>{s}</div>" for s in lines)
    return _wrap(items, note)


# ------------------------------------------------------------- working lines
def _working_lines_inner(lines: list[str | tuple[str, str]]) -> str:
    blank = (
        '<span style="display:inline-block;min-width:34px;height:1.1em;'
        'border:2px solid #2b2b2b;border-radius:4px;vertical-align:middle;'
        'margin:0 2px;"></span>'
    )
    rows = []
    for item in lines:
        prefix, line = item if isinstance(item, tuple) else ("", item)
        text = html.escape(line).replace("[]", blank)
        prefix_html = html.escape(prefix)
        rows.append(
            '<div style="display:flex;align-items:center;padding:5px 0;">'
            f'<span style="width:30px;flex-shrink:0;font-size:1rem;font-weight:600;'
            f'color:#666;text-align:right;margin-right:8px;">{prefix_html}</span>'
            f'<span style="font-size:1.3rem;font-weight:600;">{text}</span>'
            '</div>'
        )
    return "".join(rows)


def working_lines(lines: list[str | tuple[str, str]]) -> str:
    """A worked walkthrough of any step-by-step method: one re-written line
    per step, each showing the full expression/calculation with just the
    piece worked out on that step swapped for a blank box — so a pupil
    fills each blank in turn and copies the rest forward, rather than
    jumping to the answer. Write "[]" in a line wherever a blank belongs.
    Used for order-of-operations walkthroughs and for "ignore the decimal
    point, multiply, then put it back" style methods alike.

    An item may be a plain expression string, or a (prefix, expression)
    tuple when a short side-label like "so" should sit in its own narrow
    column instead of pushing that line's expression out of alignment with
    the others."""
    return _wrap(_working_lines_inner(lines))


def _html_fraction(num_html: str, den_html: str, font_size: str = "1.3rem") -> str:
    """An inline stacked fraction (numerator / rule / denominator) for use
    inside a line of prose HTML — NEVER render a fraction as inline
    "n/d" text; always stack it like this, numerator centred over a rule
    over the denominator."""
    return (
        '<span style="display:inline-flex;flex-direction:column;align-items:center;'
        f'vertical-align:middle;line-height:1.25;margin:0 3px;font-size:{font_size};font-weight:600;">'
        f'<span>{num_html}</span>'
        '<span style="border-top:3px solid #2b2b2b;width:100%;height:0;"></span>'
        f'<span>{den_html}</span>'
        '</span>'
    )


_BLANK_BOX = ('<span style="display:inline-block;min-width:30px;min-height:0.9em;'
              'border:2px solid #2b2b2b;border-radius:4px;"></span>')


def percent_to_fraction_over_100_then_simplify(p: int) -> str:
    """For a percentage that doesn't land on a clean tenth (e.g. 25%, 75%):
    a line putting it over 100 as a real stacked fraction with a blank
    numerator, followed by a ÷HCF simplify-arrows prompt for reducing that
    fraction — reusing `fraction_simplify_single_arrow`'s arrows-and-HCF
    pattern rather than inventing a second one."""
    line1 = (
        '<div style="font-size:1.3rem;font-weight:600;display:flex;align-items:center;">'
        f'{p}%&nbsp;=&nbsp;{_html_fraction(_BLANK_BOX, "100")}'
        '</div>'
    )
    simplify = _fraction_simplify_single_arrow_inner(p, 100)
    inner = (
        f'<div>{line1}</div>'
        f'<div style="margin-top:10px;padding-top:10px;border-top:2px dashed #ccc;">{simplify}</div>'
    )
    return _wrap(inner)


# --------------------------------------------------------- multiply/divide signs
def _counter(color: str) -> str:
    return (
        f'<div style="width:30px;height:30px;border-radius:50%;background:{color};'
        'border:2px solid rgba(0,0,0,0.25);flex:none;"></div>'
    )


def _counter_row(color: str, count: int) -> str:
    # Single line, never wraps — with a wider gap after every 5th counter
    # so the count is grouped visually (5s) rather than one long strip.
    cells = []
    for i in range(count):
        gap = "22px" if i > 0 and i % 5 == 0 else "8px"
        cells.append(f'<div style="margin-left:{gap};">{_counter(color)}</div>')
    return f'<div style="display:flex;flex-wrap:nowrap;">{"".join(cells)}</div>'


def subtract_negative_number_line(a: int, b: int, width: int = 640) -> str:
    """Subtracting a negative, e.g. `a - (-b)`: unlike almost every other
    scaffold here, this one leads with a short worded rule — "subtracting
    a negative is the same as adding" — because the number-line mechanics
    alone are visually IDENTICAL to plain addition and don't explain why;
    that one sentence is the actual content being taught here, not
    decoration. Below the rule, the rewritten sum and the jump number
    line make the "same as adding" claim concrete."""
    ans = a + b
    lo, hi = min(a, ans), max(a, ans)
    line = number_line(lo - 3, hi + 3, jumps=[(a, ans, f"+{b}", True)], circle=a, hide_value=ans, width=width)
    rule = (
        '<div style="text-align:center;font-size:1.05rem;font-weight:700;'
        'color:#1b3a5c;margin-bottom:6px;">Subtracting a negative is the same as adding</div>'
    )
    rewrite = (
        '<div style="text-align:center;font-size:1.4rem;font-weight:700;'
        f'margin-bottom:10px;">{a} − ({-b}) = {a} + {b}</div>'
    )
    # `line` is already its own bordered card (number_line wraps itself);
    # stack the rule/rewrite text above it rather than nesting another
    # card around everything.
    return f'<div style="display:flex;flex-direction:column;align-items:center;">{rule}{rewrite}{line}</div>'


def directed_number_counters(neg_count: int, pos_count: int) -> str:
    """The two-colour-counter ("zero pair") model for adding directed
    numbers: `neg_count` red counters and `pos_count` yellow counters,
    shown as given — never pre-cancelled or pre-counted down — so the
    pupil pairs up one red with one yellow (each pair cancels to zero)
    and counts whatever colour is left over themselves. Each row stays on
    one line, grouped in 5s for easy subitising."""
    red_row = _counter_row("#c0392b", neg_count)
    yellow_row = _counter_row("#e8b93d", pos_count)
    return _wrap(
        '<div style="display:flex;flex-direction:column;gap:12px;">'
        f'{red_row}{yellow_row}</div>'
    )


def directed_number_counters_subtract_negative(start: int, sub: int) -> str:
    """The two-colour-counter model for `start - (-sub)` (sub > 0) —
    subtracting a negative means physically removing red counters, so the
    board must already show at least `sub` red counters to make that
    possible. Where the starting value alone doesn't provide enough (the
    usual case when start is 0 or positive), the board is padded with
    "zero pairs" (equal red+yellow, net zero) until there are exactly
    `sub` red counters to take away — the standard version of this
    manipulative, not a shortcut that skips the zero-pair step. Still
    never performs the removal itself or shows the answer."""
    if start >= 0:
        red, yellow = sub, start + sub
    else:
        have = -start
        if have >= sub:
            red, yellow = have, 0
        else:
            red, yellow = sub, sub - have
    return directed_number_counters(red, yellow)


def counters_subtract_negative_steps(start: int, sub: int) -> str:
    """Two-colour counters for `start − (−sub)` shown as a step-by-step
    strip of panels joined by arrows, rather than one pre-padded board:
      1. the starting number as counters (yellow = +1, red = −1);
      2. (only if there aren't enough red counters to take away) the same
         board with zero pairs added — each red+yellow pair ringed with a
         dashed outline, since a pair is worth 0;
      3. the same board with `sub` red counters crossed out (taken away).
    The pupil counts what's left in the last panel; the answer is never
    printed."""
    red_c, yel_c = "#c0392b", "#e8b93d"

    def counter(color, crossed=False):
        x = ('<svg width="30" height="30" style="position:absolute;left:0;top:0;">'
             '<line x1="4" y1="4" x2="26" y2="26" stroke="#111" stroke-width="3"/>'
             '<line x1="26" y1="4" x2="4" y2="26" stroke="#111" stroke-width="3"/></svg>') if crossed else ""
        return (f'<div style="position:relative;width:30px;height:30px;border-radius:50%;background:{color};'
                f'border:2px solid rgba(0,0,0,0.25);box-sizing:border-box;flex:none;">{x}</div>')

    def row(items):
        return f'<div style="display:flex;gap:6px;flex-wrap:wrap;min-height:30px;">{"".join(items)}</div>'

    def pair(crossed_red=False):
        return ('<div style="display:flex;flex-direction:column;gap:4px;padding:4px;border:2px dashed #666;border-radius:20px;">'
                f'{counter(red_c, crossed_red)}{counter(yel_c)}</div>')

    have_red = max(0, -start)
    have_yel = max(0, start)
    pairs = max(0, sub - have_red)

    def board(stage):
        crossed_left = sub if stage == 3 else 0
        reds = []
        for _ in range(have_red):
            reds.append(counter(red_c, crossed_left > 0))
            crossed_left -= 1 if crossed_left > 0 else 0
        yels = [counter(yel_c) for _ in range(have_yel)]
        prs = []
        if stage >= 2:
            for _ in range(pairs):
                prs.append(pair(crossed_left > 0))
                crossed_left -= 1 if crossed_left > 0 else 0
        parts = []
        if reds:
            parts.append(row(reds))
        if yels:
            parts.append(row(yels))
        if prs:
            parts.append(f'<div style="display:flex;gap:6px;flex-wrap:wrap;">{"".join(prs)}</div>')
        if not parts:
            parts.append('<div style="height:30px;"></div>')
        return ('<div style="border:1.5px solid #bbb;border-radius:8px;padding:10px;background:#fff;'
                f'display:flex;flex-direction:column;gap:8px;">{"".join(parts)}</div>')

    arrow = ('<svg width="34" height="20" viewBox="0 0 34 20" style="flex:none;align-self:center;">'
             '<line x1="2" y1="10" x2="24" y2="10" stroke="#2e6da4" stroke-width="3"/>'
             '<path d="M22,3 L32,10 L22,17 z" fill="#2e6da4"/></svg>')
    stages = [1, 2, 3] if pairs else [1, 3]
    panels = arrow.join(board(st) for st in stages)
    return _wrap(f'<div style="display:flex;align-items:stretch;gap:8px;flex-wrap:wrap;">{panels}</div>')


def _sign_circle(sign: str) -> str:
    color = "#1b3a5c" if sign == "+" else "#e0457b"
    return (
        '<span style="display:inline-flex;align-items:center;justify-content:center;'
        f'width:26px;height:26px;border-radius:50%;background:{color};color:#fff;'
        f'font-weight:bold;font-size:15px;flex:none;">{sign}</span>'
    )


def percent_fraction_number_line(target: int, denominator: int = 10, hide: str = "fraction", width: int = 640) -> str:
    """Two aligned number lines — Fraction (in `denominator`ths, drawn as
    real stacked fractions) above Percentage below — with a downward arrow
    and a small dot marking the target tick on both, so the two scales
    read as literally the same point. Whichever row is the thing being
    solved for has its label at that tick replaced with a blank box; the
    other row shows its value plainly, since it's given in the question."""
    n = denominator
    pad = 100
    usable = width - 2 * pad
    height = 210

    def x(k: int) -> float:
        return pad + k / n * usable

    y_frac_num, y_frac_rule, y_frac_den = 42, 54, 76
    y_line1 = 96
    y_line2 = 156
    y_pct_label = y_line2 + 26

    svg = [
        f'<svg viewBox="0 0 {width} {height}" width="100%" height="{height}" '
        f'xmlns="http://www.w3.org/2000/svg" font-family="inherit">',
        '<defs><marker id="pfarrow" markerWidth="8" markerHeight="8" refX="4" refY="4" '
        'orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#c0392b"/></marker></defs>',
        f'<text x="6" y="{y_frac_rule+5}" font-size="13" font-weight="bold" fill="#333">Fraction</text>',
        f'<line x1="{pad}" y1="{y_line1}" x2="{width-pad}" y2="{y_line1}" stroke="#222" stroke-width="2"/>',
        f'<text x="6" y="{y_line2+5}" font-size="13" font-weight="bold" fill="#333">Percentage</text>',
        f'<line x1="{pad}" y1="{y_line2}" x2="{width-pad}" y2="{y_line2}" stroke="#222" stroke-width="2"/>',
    ]
    for k in range(n + 1):
        xv = x(k)
        svg.append(f'<line x1="{xv}" y1="{y_line1-6}" x2="{xv}" y2="{y_line1+6}" stroke="#222" stroke-width="1.5"/>')
        svg.append(f'<line x1="{xv}" y1="{y_line2-6}" x2="{xv}" y2="{y_line2+6}" stroke="#222" stroke-width="1.5"/>')
        if hide == "fraction" and k == target:
            svg.append(f'<rect x="{xv-17:.1f}" y="{y_frac_num-18}" width="34" height="46" rx="4" fill="#fff" stroke="#c0392b" stroke-width="2.5"/>')
        else:
            svg.append(f'<text x="{xv}" y="{y_frac_num}" text-anchor="middle" font-size="15" font-weight="bold" fill="#222">{k}</text>')
            svg.append(f'<line x1="{xv-11:.1f}" y1="{y_frac_rule}" x2="{xv+11:.1f}" y2="{y_frac_rule}" stroke="#222" stroke-width="1.5"/>')
            svg.append(f'<text x="{xv}" y="{y_frac_den}" text-anchor="middle" font-size="15" font-weight="bold" fill="#222">{n}</text>')
        pct = k * 100 // n
        if hide == "percentage" and k == target:
            svg.append(f'<rect x="{xv-22:.1f}" y="{y_line2+10}" width="44" height="28" rx="4" fill="#fff" stroke="#c0392b" stroke-width="2.5"/>')
        else:
            svg.append(f'<text x="{xv}" y="{y_pct_label}" text-anchor="middle" font-size="14" font-weight="bold" fill="#222">{pct}%</text>')
    tx = x(target)
    svg.append(f'<circle cx="{tx:.1f}" cy="{y_line1}" r="4" fill="#2e8b6e"/>')
    svg.append(f'<circle cx="{tx:.1f}" cy="{y_line2}" r="4" fill="#2e8b6e"/>')
    svg.append(f'<line x1="{tx:.1f}" y1="{y_line1-42}" x2="{tx:.1f}" y2="{y_line1-16}" stroke="#c0392b" stroke-width="2.5" marker-end="url(#pfarrow)"/>')
    svg.append("</svg>")
    return _wrap("".join(svg))


def _sign_eq_row(s1: str, op: str, s2: str, s3: str) -> str:
    return (
        '<div style="display:flex;align-items:center;gap:5px;">'
        f'{_sign_circle(s1)}<span style="font-weight:bold;">{op}</span>{_sign_circle(s2)}'
        f'<span style="font-weight:bold;">=</span>{_sign_circle(s3)}</div>'
    )


def sign_rules_table(lang: str = "en", op: str | None = None) -> str:
    """The same/different-signs rule table. By default shows both the
    multiply and divide columns side by side; pass `op="×"` or `op="÷"` to
    show only the rules for that one operation — e.g. a multiplication
    question has no business also showing the division rules."""
    navy, pink = "#1b3a5c", "#e0457b"
    only = {"×": 0, "÷": 1}.get(op)

    def block(border: str, label: str, rows: list[tuple[str, str]]) -> str:
        if only is None:
            row_html = "".join(f'<div style="display:flex;gap:16px;justify-content:center;">{m}{d}</div>' for m, d in rows)
        else:
            row_html = "".join(f'<div style="display:flex;justify-content:center;">{r[only]}</div>' for r in rows)
        return (
            f'<div style="border:3px solid {border};border-radius:10px;padding:6px 12px;box-sizing:border-box;">'
            f'<div style="text-align:center;font-weight:bold;color:{border};font-size:11px;'
            f'margin-bottom:5px;">{label}</div>{row_html}</div>'
        )

    same_rows = [
        (_sign_eq_row("+", "×", "+", "+"), _sign_eq_row("+", "÷", "+", "+")),
        (_sign_eq_row("−", "×", "−", "+"), _sign_eq_row("−", "÷", "−", "+")),
    ]
    diff_rows = [
        (_sign_eq_row("−", "×", "+", "−"), _sign_eq_row("−", "÷", "+", "−")),
        (_sign_eq_row("+", "×", "−", "−"), _sign_eq_row("+", "÷", "−", "−")),
    ]

    multiply_label, divide_label = ("IOMADAICH", "ROINN") if lang == "gd" else ("MULTIPLY", "DIVIDE")
    same_label = "COMHARRAN COIONANN = DEARBHACH" if lang == "gd" else "SAME SIGNS = POSITIVE"
    diff_label = "COMHARRAN EU-CHOSMHAIL = ÀICHEIL" if lang == "gd" else "DIFFERENT SIGNS = NEGATIVE"

    if only is None:
        header = (
            '<div style="display:flex;gap:20px;justify-content:center;font-weight:bold;'
            'font-size:11px;color:#555;margin-bottom:4px;">'
            f'<span>{multiply_label}</span><span>{divide_label}</span></div>'
        )
    else:
        label = multiply_label if only == 0 else divide_label
        header = (
            '<div style="text-align:center;font-weight:bold;font-size:11px;color:#555;'
            f'margin-bottom:4px;">{label}</div>'
        )

    # align-items:stretch (not center) so both rule boxes stretch to match
    # whichever is naturally wider — the "different signs" label is longer
    # than "same signs", which previously left the two boxes visibly
    # different widths.
    return (
        '<div style="display:flex;flex-direction:column;gap:7px;align-items:stretch;">'
        + header
        + block(navy, same_label, same_rows)
        + block(pink, diff_label, diff_rows)
        + "</div>"
    )


def negative_sign_scaffold(op: str, sign_x: int, sign_y: int, x_val: int, y_val: int, lang: str = "en") -> str:
    """Rule table (same/different signs) plus a worked example matching the
    question's operation and sign pattern, using fixed demo magnitudes so the
    actual question's answer is never shown."""
    x, y = x_val * sign_x, y_val * sign_y
    ans = x * y if op == "×" else x_val // y_val * (sign_x * sign_y)
    magnitude_ans = x_val * y_val if op == "×" else x_val // y_val
    x_str = f"({x})" if x < 0 else str(x)
    y_str = f"({y})" if y < 0 else str(y)
    ans_str = f"({ans})" if ans < 0 else str(ans)

    example = (
        '<div style="display:flex;flex-direction:column;gap:6px;align-items:center;">'
        f'<div style="font-size:19px;font-weight:bold;">{x_str} {op} {y_str} = {ans_str}</div>'
        f'<div style="font-size:13px;color:#555;">{x_val} {op} {y_val} = {magnitude_ans}</div>'
        "</div>"
    )

    inner = (
        '<div style="display:flex;align-items:center;gap:20px;flex-wrap:wrap;">'
        + sign_rules_table(lang, op=op)
        + '<div style="margin-left:6px;padding-left:20px;border-left:2px dashed #ccc;">'
        + example
        + "</div></div>"
    )
    return _wrap(inner)
