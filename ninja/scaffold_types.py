"""Scaffold types — lets the worksheet generator ask for "only Numicon and
number lines" without touching the generators themselves.

How it works: every public drawing function in `ninja/scaffolds.py` is
wrapped so the HTML it returns remembers which function drew it (a `str`
subclass with a `.sc_name` attribute — it still behaves exactly like a
normal string everywhere else in the app). `scaffold_type()` then maps that
function name to a teacher-facing family such as "Numicon" or "Number line".

The worksheet generator simply re-rolls a question until its scaffold is one
of the ticked types. A skill's available types are found by sampling it, so
a new scaffold added to a generator shows up here automatically — as long as
its function name matches one of the rules in TYPE_RULES (anything unmatched
lands in "Other").
"""
from __future__ import annotations

import functools
import inspect
import re

from . import scaffolds as sc


class ScaffoldHTML(str):
    """A string that remembers which scaffold function produced it."""
    sc_name: str = ""


# Functions that build text for prompts or are pure helpers — never tagged.
_SKIP = {"to_black_and_white", "fraction_html", "fraction_equation_html", "bond_dice_ok",
         "hundred_square_add_9_ok"}


def _wrap(name, fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        out = fn(*args, **kwargs)
        if not isinstance(out, str):
            return out
        tag = name
        # fraction_equivalent_scaffold draws four different pictures,
        # picked by its `kind` argument.
        if name == "fraction_equivalent_scaffold":
            kind = kwargs.get("kind", args[2] if len(args) > 2 else "")
            tag = f"{name}:{kind}"
        res = ScaffoldHTML(out)
        res.sc_name = tag
        return res
    wrapper._sc_wrapped = True
    return wrapper


def install() -> None:
    """Wrap the drawing functions in `ninja.scaffolds` (safe to call twice)."""
    for name, fn in list(vars(sc).items()):
        if name.startswith("_") or name in _SKIP or not inspect.isfunction(fn):
            continue
        if fn.__module__ != sc.__name__ or getattr(fn, "_sc_wrapped", False):
            continue
        setattr(sc, name, _wrap(name, fn))


# Ordered: the first rule whose pattern matches the function name wins.
TYPE_RULES: list[tuple[str, str]] = [
    ("Numicon", r"numicon"),
    ("Dienes", r"dienes"),
    ("Rekenrek", r"rekenrek"),
    ("Dice", r"dice"),
    ("Hundred square", r"hundred_square"),
    ("Ten / five frame", r"frame"),
    ("Two-colour counters", r"counters"),
    ("Fraction wall", r"wall$|:wall"),
    ("Fraction circles", r"circles"),
    ("Fraction arrows", r"arrow"),
    ("Bar model", r"bar_model|_bar$|fraction_bar"),
    ("Cube towers", r"repeated_groups"),
    ("Array", r"array"),
    ("Area / volume model", r"square_root_area|cube_root_volume|cube_number_stack"),
    ("Function machine", r"function_machine"),
    ("Clock / time strip", r"clock|hour_conversion"),
    ("Part-whole / partition", r"partition|halving_columns"),
    ("Place value chart", r"sig_figs_chart|place_value_grid"),
    ("Number line", r"number_line|_line$|hops_line|:numberline"),
    ("Written method / working", r"column_|bus_stop|lattice|working_lines|place_value_|percentage_table|over_100"),
    ("Rule / hint", r"hint_list|fact_list|factor_check|sign_rules|negative_sign"),
]

# Display order for the tick-boxes.
ALL_TYPES = [t for t, _ in TYPE_RULES] + ["Other"]


def scaffold_type(html) -> str:
    name = getattr(html, "sc_name", "")
    for label, pattern in TYPE_RULES:
        if name and re.search(pattern, name):
            return label
    return "Other"


install()
