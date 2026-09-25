"""Answer-checking helpers used by generators."""
from __future__ import annotations

import re
from fractions import Fraction


def _clean(s: str) -> str:
    return (s or "").strip().lower().replace(" ", "").replace(",", "").replace("£", "")


def numeric_check(expected, tolerance: float = 0.01):
    expected = float(expected)

    def check(user: str) -> bool:
        try:
            val = float(_clean(user).replace("−", "-"))
        except ValueError:
            return False
        return abs(val - expected) <= tolerance

    return check


def exact_text_check(expected: str):
    exp = _clean(expected)

    def check(user: str) -> bool:
        return _clean(user) == exp

    return check


def any_of_check(expected_options: list[str]):
    exp = {_clean(e) for e in expected_options}

    def check(user: str) -> bool:
        return _clean(user) in exp

    return check


def fraction_check(expected: Fraction):
    def check(user: str) -> bool:
        u = _clean(user)
        m = re.match(r"^(-?\d+)/(\d+)$", u)
        if m:
            try:
                val = Fraction(int(m.group(1)), int(m.group(2)))
                return val == expected
            except ZeroDivisionError:
                return False
        try:
            return abs(float(u) - float(expected)) <= 0.001
        except ValueError:
            return False

    return check


def list_check(expected_numbers: list[int]):
    exp = [str(n) for n in expected_numbers]

    def check(user: str) -> bool:
        parts = re.split(r"[,\s]+", user.strip())
        parts = [p for p in parts if p]
        return parts == exp

    return check


def yes_no_check(expected_yes: bool):
    yes_words = {"yes", "y", "true"}
    no_words = {"no", "n", "false"}

    def check(user: str) -> bool:
        u = _clean(user)
        if expected_yes:
            return u in yes_words
        return u in no_words

    return check
