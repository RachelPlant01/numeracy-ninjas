"""Understanding ("concept") questions for the assessment — one bank per skill.

The fluency half of the assessment reuses the practice generators as they
are. These questions check whether a pupil *understands* the skill rather
than just carrying it out. Each skill has a few kinds of item:

- Spot the mistake — someone's answer, usually showing a common
  misconception. The pupil decides if they're right, and if not, picks the
  right answer.
- Use what you know — a derived fact ("23 × 4 = 92, so what is 23 × 5?"),
  an inverse, or a pattern that pupils who understand can use without
  starting again.
- Reasoning / estimate / represent — choose a strategy, an estimate, or
  what a calculation means.

Wrong multiple-choice options carry a note naming the misconception they
suggest, which goes on the teacher's report. English only for now.
Edit or add items freely — each skill just needs a list of item functions.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Callable

from .checking import numeric_check

SPOT = "Spot the mistake"
DERIVED = "Use what you know"
REASON = "Reasoning"
ESTIMATE = "Estimate"
REPRESENT = "Represent it"

NAMES = ["Sam", "Alex", "Jamie", "Morgan", "Isla", "Ruaridh", "Kai", "Eilidh", "Finn", "Ava"]


@dataclass
class ConceptItem:
    prompt: str
    answer_display: str
    checker: Callable[[str], bool]
    kind: str
    options: list[str] | None = None  # multiple choice when set
    notes: dict[str, str] = field(default_factory=dict)  # wrong option -> misconception


def _fmt(n) -> str:
    if isinstance(n, float):
        n = round(n, 6)
        return str(int(n)) if n == int(n) else f"{n:g}"
    return str(n)


def _n(n) -> str:
    """Bracket negatives inside a calculation, as the practice questions do."""
    return f"({_fmt(n)})" if n < 0 else _fmt(n)


def _typed(prompt: str, ans, kind: str = DERIVED) -> ConceptItem:
    return ConceptItem(prompt, _fmt(ans), numeric_check(ans), kind)


def _mc(prompt: str, correct, wrong: dict, kind: str = REASON) -> ConceptItem:
    correct = _fmt(correct) if not isinstance(correct, str) else correct
    opts: dict[str, str] = {correct: ""}
    for w, note in wrong.items():
        w = _fmt(w) if not isinstance(w, str) else w
        if w not in opts:
            opts[w] = note
    options = list(opts)
    random.shuffle(options)
    return ConceptItem(prompt, correct, lambda u, c=correct: u == c, kind, options,
                       {o: n for o, n in opts.items() if o != correct})


def _spot(calc: str, correct, wrong, note: str, alt=None, alt_note: str = "") -> ConceptItem:
    """`Name says calc = (wrong or correct)`. Usually the claim is the
    misconception; sometimes it's right, so "they're wrong" isn't a safe guess."""
    who = random.choice(NAMES)
    c, w = _fmt(correct) if not isinstance(correct, str) else correct, _fmt(wrong) if not isinstance(wrong, str) else wrong
    agree = f"{who} is right"
    claim_is_wrong = random.random() < 0.75
    prompt = f"{who} says {calc} = {w if claim_is_wrong else c}. Is {who} right?"
    extra = {}
    if alt is not None and _fmt(alt) not in (c, w):
        extra[f"No, it should be {_fmt(alt)}"] = alt_note or "Calculation slip"
    if claim_is_wrong:
        return _mc(prompt, f"No, it should be {c}", {agree: note, **extra}, SPOT)
    return _mc(prompt, agree, {f"No, it should be {w}": note, **extra}, SPOT)


def _estimate(calc: str, exact: float, rough: float) -> ConceptItem:
    """Closest-estimate question; distractors are a power of ten out."""
    return _mc(f"Without working it out exactly: which is the best estimate for {calc}?",
               _fmt(rough),
               {_fmt(rough * 10): "Place value — estimate is 10 times too big",
                _fmt(rough / 10): "Place value — estimate is 10 times too small",
                _fmt(rough * 100): "Place value — estimate is 100 times too big"},
               ESTIMATE)


def _round_sig1(x: float) -> float:
    if x == 0:
        return 0
    p = 10 ** math.floor(math.log10(abs(x)))
    return round(x / p) * p


# ======================================================== mental strategies
def _bond_items(target_fn: Callable[[], int]):
    def inverse():
        t = target_fn()
        a = random.randint(1, t - 1)
        return _typed(f"{a} + {t - a} = {t}. Use this to answer: {t} − {a} = ?", t - a)

    def scaled():
        t = target_fn()
        a = random.randint(1, t - 1)
        return _typed(f"{a} + {t - a} = {t}. Use this to answer: {a * 10} + {(t - a) * 10} = ?", t * 10)

    def which_pair():
        t = target_fn()
        a = random.randint(1, t - 1)
        wrong = {f"{a} and {t - a + 1}": "Off by one — counting error",
                 f"{a} and {max(t - a - 1, 0)}": "Off by one — counting error"}
        if t == 100 and a % 10:
            b = (10 - a // 10) * 10 + (10 - a % 10)  # e.g. 37 and 73 → 110
            wrong[f"{a} and {b}"] = "Made both the tens and the ones up to 10 (gives 110)"
        else:
            wrong[f"{a} and {a}"] = "Doesn't connect the pair to the total"
        return _mc(f"Which pair of numbers adds up to exactly {t}?", f"{a} and {t - a}", wrong, REPRESENT)

    def spot():
        t = target_fn()
        a = random.randint(1, t - 1)
        if t == 100 and a % 10:
            wrong = (10 - a // 10) * 10 + (10 - a % 10)
            note = "Made both the tens and the ones up to 10 — 110, not 100"
        else:
            wrong = t - a + 1
            note = "Off by one — may be counting on and including the start number"
        return _spot(f"{a} + ☐ = {t}, so ☐", t - a, wrong, note)

    return [inverse, scaled, which_pair, spot]


def _double_items(lo: int, hi: int):
    def meaning():
        n = random.randint(lo, hi)
        return _mc(f"Which of these is the same as double {n}?", f"{n} + {n}",
                   {f"{n} + 2": "Thinks doubling means adding 2",
                    f"{n} × {n}": "Confuses doubling with squaring",
                    f"{n} ÷ 2": "Confuses doubling with halving"})

    def inverse():
        n = random.randint(lo, hi)
        return _typed(f"Double a number is {2 * n}. What was the number?", n)

    def scaled():
        n = random.randint(lo, min(hi, 25))
        return _typed(f"Double {n} is {2 * n}. Use this to find double {n * 10}.", 20 * n)

    def spot():
        n = random.randint(max(lo, 15), max(hi, 49))
        while n % 10 < 5:  # need the ones to cross ten for the misconception
            n = random.randint(15, 49)
        t, o = n // 10, n % 10
        return _spot(f"double {n}", 2 * n, int(f"{2 * t}{2 * o}"),
                     "Doubled the tens and ones separately but didn't recombine them",
                     alt=2 * n - 10, alt_note="Forgot to carry the extra ten")

    return [meaning, inverse, scaled, spot] if hi > 9 else [meaning, inverse, scaled]


def _halve_items(lo: int, hi: int):
    def meaning():
        n = random.randrange(lo + lo % 2, hi + 1, 2)
        return _mc(f"Which of these is the same as halving {n}?", f"{n} ÷ 2",
                   {f"{n} − 2": "Thinks halving means taking away 2",
                    f"{n} × 2": "Confuses halving with doubling",
                    f"{n} ÷ 10": "Unsure what halving means"})

    def inverse():
        h = random.randint(max(1, lo // 2), hi // 2)
        return _typed(f"Half of a number is {h}. What was the number?", 2 * h)

    def spot():
        if hi <= 9:
            n = random.choice([3, 5, 7, 9])
            return _spot(f"half of {n}", n / 2, n // 2, "Ignored the remainder — half of an odd number isn't whole")
        n = random.choice([n for n in range(30, 99) if (n // 10) % 2 == 1 and n % 2 == 0])
        return _spot(f"half of {n}", n // 2, int(f"{(n // 10) // 2}{(n % 10) // 2}"),
                     "Halved each digit separately and lost the leftover ten")

    return [meaning, inverse, spot]


def _plus_ten_items(sign: int):
    word = "add" if sign > 0 else "subtract"

    def digit():
        n = random.choice([n for n in range(12, 89) if n % 10 and 1 <= n // 10 <= 8])
        return _mc(f"When you {word} 10 {'to' if sign > 0 else 'from'} {n}, which digit changes?", "The tens digit",
                   {"The ones digit": "Confuses tens and ones",
                    "Both digits": "Unsure what adding/subtracting 10 does to place value",
                    "Neither digit": "Unsure what adding/subtracting 10 does to place value"})

    def square():
        n = random.randint(23, 77)
        return _mc(f"On a hundred square, where is {n} {'+' if sign > 0 else '−'} 10 compared to {n}?",
                   "Directly below" if sign > 0 else "Directly above",
                   {"One square to the right": "Thinks of 10 as one step (ones)",
                    "One square to the left": "Thinks of 10 as one step (ones)",
                    "Directly above" if sign > 0 else "Directly below": "Direction of tens on the square"},
                   REPRESENT)

    def spot():
        n = random.randint(21, 89)
        return _spot(f"{n} {'+' if sign > 0 else '−'} 10", n + 10 * sign, n + sign,
                     "Added/subtracted 1 instead of 10 (changed the ones)",
                     alt=int(f"{n}0") if sign > 0 else None,
                     alt_note="Thinks adding 10 means putting a 0 on the end")

    return [digit, square, spot]


def _plus_mult10_items(sign: int):
    op = "+" if sign > 0 else "−"

    def derived():
        n, m = random.randint(25, 140), random.choice(range(20, 90, 10))
        if sign < 0:
            n = max(n, m + 15)
        return _typed(f"{n} {op} {m} = {n + sign * m}. Use this to answer: {n} {op} {m + 10} = ?",
                      n + sign * (m + 10))

    def spot():
        n, m = random.randint(25, 140), random.choice(range(20, 90, 10))
        if sign < 0:
            n = max(n, m + 15)
        return _spot(f"{n} {op} {m}", n + sign * m, n + sign * (m // 10),
                     f"Treated {m} as {m // 10} — {op} to the ones instead of the tens")

    def digit():
        n = random.choice([n for n in range(31, 69) if n % 10])
        m = random.choice([20, 30])
        return _mc(f"Which digit of {n} changes when you work out {n} {op} {m}?", "Only the tens digit",
                   {"Only the ones digit": "Confuses tens and ones",
                    "Both digits": "Not sure that adding tens leaves the ones alone"})

    return [derived, spot, digit]


def _add9_items():
    def strategy():
        n = random.randint(14, 85)
        return _mc(f"Which is a quick way to work out {n} + 9?", "Add 10, then take away 1",
                   {"Add 10, then add 1": "Compensates the wrong way",
                    "Take away 10, then add 1": "Mixes up the operation",
                    "Add 9 to the tens digit": "Place value — 9 is ones, not tens"})

    def derived():
        n = random.randint(14, 85)
        return _typed(f"{n} + 10 = {n + 10}. Use this to answer: {n} + 9 = ?", n + 9)

    def spot():
        n = random.randint(14, 85)
        return _spot(f"{n} + 9", n + 9, n + 11, "Added 10 then added 1 — compensated the wrong way")

    return [strategy, derived, spot]


def _bridge20_items():
    def split():
        a = random.randint(6, 9)
        b = random.randint(11 - a, 9)
        return _typed(f"To work out {a} + {b}, you can make 10 first: {a} + {10 - a} + ☐. What goes in the box?",
                      b - (10 - a))

    def spot():
        a = random.randint(6, 9)
        b = random.randint(11 - a, 9)
        return _spot(f"{a} + {b}", a + b, a + b - 1,
                     "Counted on and included the starting number (one too few)")

    def which():
        a = random.randint(6, 9)
        b = random.randint(11 - a, 9)
        r = b - (10 - a)
        return _mc(f"Which shows a good way to work out {a} + {b}?", f"{a} + {10 - a} + {r}",
                   {f"{a} + {10 - a} + {r + 1}": "Split the second number wrongly",
                    f"{a} + {b} + 10": "Unsure how bridging through 10 works",
                    f"10 + {b}": "Rounded but didn't adjust"})

    return [split, spot, which]


def _to_mult10_items():
    def next10():
        n = random.choice([n for n in range(12, 98) if n % 10])
        t = (n // 10 + 1) * 10
        return _mc(f"What is the next multiple of 10 after {n}?", t,
                   {t - 10: "Went back to the previous ten", n + 10: "Added 10 instead of finding the next ten",
                    t + 10: "Skipped a ten"})

    def spot():
        n = random.choice([n for n in range(12, 98) if n % 10 and n % 10 != 5])
        t = (n // 10 + 1) * 10
        return _spot(f"{n} + ☐ = {t}, so ☐", t - n, n % 10, "Gave the ones digit instead of its bond to 10")

    def derived():
        n = random.choice([n for n in range(12, 88) if n % 10])
        t = (n // 10 + 1) * 10
        return _typed(f"{n} + {t - n} = {t}. Use this to answer: {n} + {t - n + 10} = ?", t + 10)

    return [next10, spot, derived]


def _near_double_items():
    def which():
        a = random.randint(6, 45)
        return _mc(f"Which is a quick way to work out {a} + {a + 1}?", f"Double {a}, then add 1",
                   {f"Double {a}, then take away 1": "Adjusts the wrong way",
                    f"Double {a + 1}, then add 1": "Adjusts the wrong way",
                    f"Double {a}, then add 2": "Not sure how far apart the numbers are"})

    def derived():
        a = random.randint(6, 45)
        d = random.choice([-1, 1])
        return _typed(f"Double {a} is {2 * a}. Use this to answer: {a} + {a + d} = ?", 2 * a + d)

    def spot():
        a = random.randint(6, 45)
        return _spot(f"{a} + {a + 2}", 2 * a + 2, 2 * a + 1,
                     "Treated every near double as 'double and add 1'")

    return [which, derived, spot]


def _partition1_items():
    def count_pairs():
        t = random.randint(4, 9)
        return _typed(f"How many different pairs of whole numbers add up to {t}? Include 0 + {t}, and count "
                      f"pairs like 1 + {t - 1} and {t - 1} + 1 as the same.", t // 2 + 1, REASON)

    def inverse():
        t = random.randint(4, 9)
        p = random.randint(1, t - 1)
        return _typed(f"{t} = {p} + {t - p}. Use this to answer: {t} − {t - p} = ?", p)

    def which():
        t = random.randint(4, 9)
        p = random.randint(1, t - 1)
        return _mc(f"Which of these is another way to make {t}?", f"{t - p} + {p}",
                   {f"{p} + {t - p + 1}": "Off by one", f"{t} + {p}": "Confuses the parts and the whole",
                    f"{t - p} − {p}": "Mixes up adding and subtracting"}, REPRESENT)

    return [count_pairs, inverse, which]


def _partition2_items():
    def value():
        n = random.choice([n for n in range(21, 99) if n % 10 and n // 10 != n % 10])
        return _mc(f"In {n}, what is the digit {n // 10} worth?", (n // 10) * 10,
                   {n // 10: "Reads the tens digit as ones", n: "Gives the whole number",
                    (n // 10) * 100: "Place value — thinks it's hundreds"})

    def same():
        n = random.choice([n for n in range(21, 99) if n % 10 and n // 10 != n % 10])
        t, o = n // 10, n % 10
        return _mc(f"Which of these is the same as {n}?", f"{t * 10} + {o}",
                   {f"{t} + {o}": "Treats the tens digit as ones", f"{o * 10} + {t}": "Swapped tens and ones",
                    f"{t * 10} + {o * 10}": "Treats both digits as tens"}, REPRESENT)

    def regroup():
        n = random.randint(31, 98)
        return _typed(f"{n} = {n - 10} + ☐. What goes in the box?", 10, REASON)

    return [value, same, regroup]


def _bridge_mult10_items(sign: int):
    op = "+" if sign > 0 else "−"

    def pick():
        while True:
            a = random.randint(23, 97)
            step = (10 - a % 10) if sign > 0 else a % 10
            if 1 <= step <= 7 and a % 10:
                return a, step, step + random.randint(1, 8 - step) + 1

    def why():
        a, step, b = pick()
        target = a + step if sign > 0 else a - step
        return _mc(f"To work out {a} {op} {b}, {random.choice(NAMES)} splits {b} into {step} and {b - step}. "
                   f"Why {step}?", f"{op}{step} takes {a} to {target}, a multiple of 10",
                   {f"{step} is about half of {b}": "Doesn't see the purpose of bridging",
                    f"{step} is the ones digit of {a}" if sign > 0 else f"{step} is the bond to 10":
                        "Confuses the bond to 10 with the ones digit" if sign > 0 else "Confuses which bond is needed",
                    "Any split works just as well": "Doesn't see the purpose of bridging"})

    def spot():
        a, step, b = pick()
        ans = a + sign * b
        if sign > 0:
            return _spot(f"{a} + {b} = {a} + {step} + {b - step}", ans, ans - 1,
                         "Split the number wrongly — the parts must add up to the number")
        return _spot(f"{a} − {b} = {a} − {step} − {b - step}", ans, a - step + (b - step),
                     "Added the second part instead of subtracting it")

    def nearest():
        a, step, b = pick()
        t = a + step if sign > 0 else a - step
        return _mc(f"Working out {a} {op} {b}, which multiple of 10 do you bridge through?", t,
                   {t - 10 * sign: "Picked the wrong multiple of 10", t + 10 * sign: "Picked the wrong multiple of 10",
                    a + 10 * sign: "Added/subtracted 10 instead of finding the ten"})

    return [why, spot, nearest]


def _smaller_from_larger(a: int, b: int) -> int:
    """The 'take the smaller digit from the larger' misconception."""
    sa, sb = str(a), str(b).rjust(len(str(a)), "0")
    return int("".join(str(abs(int(x) - int(y))) for x, y in zip(sa, sb)))


def _count_up_items():
    def spot():
        h = random.randint(2, 9) * 100
        big, small = h + random.randint(1, 5), h - random.randint(2, 9)
        return _spot(f"{big} − {small}", big - small, _smaller_from_larger(big, small),
                     "Took the smaller digit from the larger in each column")

    def strategy():
        h = random.randint(2, 9) * 100
        big, small = h + random.randint(1, 5), h - random.randint(2, 9)
        return _mc(f"What is the quickest way to work out {big} − {small}?", f"Count up from {small} to {big}",
                   {f"Count back {small} from {big}, one at a time": "Doesn't see that the numbers are close",
                    f"Work out {small} − {big} instead": "Thinks subtraction can be done in either order",
                    f"Add {big} and {small}": "Mixes up the operation"})

    def meaning():
        return _mc("Is a − b always the same as b − a?", "Only when a and b are the same number",
                   {"Yes, always": "Thinks subtraction is commutative", "Never": "Hasn't considered equal numbers"})

    return [spot, strategy, meaning]


def _reorder_items():
    def strategy():
        s, l = random.randint(3, 9), random.randint(120, 880)
        return _mc(f"What is the easiest way to work out {s} + {l}?", f"Start at {l} and count on {s}",
                   {f"Start at {s} and count on {l}": "Doesn't use reordering",
                    f"Work out {l} − {s}": "Thinks reordering changes the operation",
                    f"Start at {s} and count back {l}": "Unsure about the operation"})

    def always():
        a, b = random.randint(3, 9), random.randint(120, 880)
        return _mc(f"Is {a} + {b} always equal to {b} + {a}?", "Yes — adding in any order gives the same total",
                   {"No — the bigger number must go first": "Doesn't know addition is commutative",
                    "Only if both numbers are small": "Doesn't know addition is commutative"})

    def subtract():
        return _mc("Can you swap the order of a subtraction, like 9 − 4 and 4 − 9, and get the same answer?",
                   "No — only addition can be reordered",
                   {"Yes, any calculation can be reordered": "Over-applies commutativity to subtraction",
                    "Yes, if the answer is positive": "Over-applies commutativity to subtraction"})

    return [strategy, always, subtract]


def _repeated_add_items():
    def meaning():
        n, k = random.randint(3, 9), random.randint(3, 6)
        return _mc(f"Which of these is the same as {n} × {k}?", " + ".join([str(n)] * k),
                   {f"{n} + {k}": "Confuses × with +", " + ".join([str(n)] * (k + 1)): "One group too many",
                    f"{n}{k}": "Writes the digits together"}, REPRESENT)

    def one_more():
        n, k = random.randint(3, 9), random.randint(3, 8)
        return _typed(f"{k} × {n} = {k * n}. Use this to answer: {k + 1} × {n} = ?", (k + 1) * n)

    def array():
        r, c = random.randint(2, 6), random.randint(3, 9)
        return _mc(f"Some dots are laid out in {r} rows with {c} dots in each row. Which calculation finds "
                   f"how many dots there are?", f"{r} × {c}",
                   {f"{r} + {c}": "Adds rows and columns instead of multiplying",
                    f"{c} − {r}": "Unsure what the array shows", f"{r * c} × {r}": "Unsure what the array shows"},
                   REPRESENT)

    return [meaning, one_more, array]


def _inverse_div_items():
    def fact():
        a, b = random.randint(3, 9), random.randint(3, 9)
        while a == b:
            b = random.randint(3, 9)
        p = a * b
        return _mc(f"{a} × {b} = {p}. Which division fact is also true?", f"{p} ÷ {a} = {b}",
                   {f"{a} ÷ {p} = {b}": "Divides the wrong way round",
                    f"{p} ÷ {b} = {a + 1}": "Doesn't use the related fact",
                    f"{b} ÷ {a} = {p}": "Divides the wrong way round"})

    def scaled():
        a, b = random.randint(2, 9), random.randint(2, 9)
        return _typed(f"{a * b} ÷ {a} = {b}. Use this to answer: {a * b * 10} ÷ {a} = ?", 10 * b)

    def story():
        a, b = random.randint(3, 8), random.randint(3, 9)
        return _mc(f"{a * b} sweets are shared equally between {a} friends. Which calculation tells you how many "
                   f"each friend gets?", f"{a * b} ÷ {a}",
                   {f"{a * b} − {a}": "Sees sharing as taking away", f"{a * b} × {a}": "Mixes up the operation",
                    f"{a} ÷ {a * b}": "Divides the wrong way round"}, REPRESENT)

    return [fact, scaled, story]


def _equiv_calc_items():
    def same():
        a, b = random.randint(23, 79), random.randint(23, 79)
        return _mc(f"Which of these gives the same answer as {a} + {b}?", f"{a + 1} + {b - 1}",
                   {f"{a + 1} + {b + 1}": "Changed both numbers the same way",
                    f"{a - 1} + {b - 1}": "Changed both numbers the same way",
                    f"{a + 10} + {b - 1}": "Didn't balance the change"})

    def compensate():
        a = random.randint(23, 79)
        b = random.choice([19, 29, 39, 49, 59, 98, 99])
        r = (b + 1) if b % 10 == 9 else 100
        return _typed(f"{a} + {b} = {a} + {r} − ☐. What goes in the box?", r - b, REASON)

    def spot():
        a = random.randint(23, 79)
        return _spot(f"{a} + 99 = {a} + 100 + 1, so {a} + 99", a + 99, a + 101,
                     "Compensated the wrong way (should take 1 away)")

    return [same, compensate, spot]


def _clock24_items():
    def to24():
        h, m = random.randint(1, 11), random.choice([5, 15, 20, 30, 45])
        return _mc(f"Which 24-hour time is the same as {h}:{m:02d} pm?", f"{h + 12:02d}:{m:02d}",
                   {f"{h:02d}:{m:02d}": "Forgot to add 12 for pm", f"{h + 10:02d}:{m:02d}": "Added 10 instead of 12",
                    f"{h + 2:02d}:{m:02d}": "Unsure how pm converts"})

    def midnight():
        m = random.choice([10, 15, 30, 45])
        return _mc(f"Which 24-hour time is {m} minutes after midnight?", f"00:{m:02d}",
                   {f"12:{m:02d}": "Thinks the hour after midnight is 12", f"24:{m:02d}": "Thinks the day ends at 24:59",
                    f"01:{m:02d}": "Unsure about the first hour of the day"})

    def invalid():
        bad = random.choice(["25:10", "24:30", "13:75"])
        return _mc("Which of these is NOT a real 24-hour clock time?", bad,
                   {"00:45": "Unsure that 00:xx is a real time", "23:59": "Unsure where the day ends",
                    "12:05": "Unsure about 12-something"})

    return [to24, midnight, invalid]


def _time_items():
    def _times():
        h = random.randint(7, 15)
        m1 = random.randint(35, 55)
        d = random.randint(70 - m1, 50)
        t2 = h * 60 + m1 + d
        return h, m1, d, t2 // 60, t2 % 60

    def spot():
        h, m1, d, h2, m2 = _times()
        wrong = (h2 * 100 + m2) - (h * 100 + m1)
        return _spot(f"from {h:02d}:{m1:02d} to {h2:02d}:{m2:02d} is ☐ minutes, so ☐", d, wrong,
                     "Treated the times as ordinary numbers (100 minutes in an hour)")

    def derived():
        h, m1, d, h2, m2 = _times()
        return _typed(f"From {h:02d}:{m1:02d} to {h2:02d}:{m2:02d} is {d} minutes. How many minutes is it from "
                      f"{h:02d}:{m1:02d} to {h2 + 1:02d}:{m2:02d}?", d + 60)

    def jumps():
        h, m1, d, h2, m2 = _times()
        return _mc(f"Which jumps would get you from {h:02d}:{m1:02d} to {h2:02d}:{m2:02d}?",
                   f"{60 - m1} minutes to {h + 1:02d}:00, then {m2} more minutes",
                   {f"{100 - m1} minutes to {h + 1:02d}:00, then {m2} more minutes": "Thinks there are 100 minutes in an hour",
                    f"{m1} minutes to {h + 1:02d}:00, then {m2} more minutes": "Used the minutes instead of the gap to the hour",
                    f"{60 - m1} minutes to {h + 1:02d}:00, then {60 - m2} more minutes": "Unsure how to finish the count"},
                   REPRESENT)

    return [spot, derived, jumps]


# ================================================================ key skills
def _mult_whole_items():
    def estimate():
        a, b = random.randint(31, 890), random.randint(12, 89)
        return _estimate(f"{a} × {b}", a * b, _round_sig1(a) * _round_sig1(b))

    def derived():
        a, b = random.randint(13, 95), random.randint(3, 25)
        return _typed(f"{a} × {b} = {a * b}. Use this to answer: {a} × {b + 1} = ?", a * (b + 1))

    def spot():
        a = random.randint(13, 95)
        b = random.randint(2, 9) * 10 + random.randint(1, 9)
        t, u = b // 10, b % 10
        return _spot(f"{a} × {b}", a * b, a * u + a * t,
                     "Forgot the placeholder zero — treated the tens digit as ones")

    return [estimate, derived, spot]


def _div_whole_items():
    def inverse():
        b, q = random.randint(3, 12), random.randint(21, 300)
        return _typed(f"{b * q} ÷ {b} = {q}. Use this to answer: {q} × {b} = ?", b * q)

    def spot():
        b = random.randint(3, 9)
        q = random.randint(1, 9) * 100 + random.randint(1, 9)  # zero in the tens
        return _spot(f"{b * q} ÷ {b}", q, int(str(q).replace("0", "")),
                     "Missed a zero in the answer when a digit was smaller than the divisor")

    def estimate():
        b, q = random.randint(3, 9), random.randint(110, 900)
        return _estimate(f"{b * q} ÷ {b}", q, _round_sig1(q))

    return [inverse, spot, estimate]


def _carry_less_sum(a: int, b: int) -> int:
    sa, sb = str(a), str(b)
    w = max(len(sa), len(sb))
    sa, sb = sa.rjust(w, "0"), sb.rjust(w, "0")
    return int("".join(str((int(x) + int(y)) % 10) for x, y in zip(sa, sb)))


def _add_whole_items():
    def spot():
        while True:
            a, b = random.randint(1200, 6800), random.randint(1200, 2900)
            if _carry_less_sum(a, b) != a + b:
                break
        return _spot(f"{a} + {b}", a + b, _carry_less_sum(a, b), "Didn't carry when a column added to 10 or more")

    def inverse():
        a, b = random.randint(1200, 6800), random.randint(1200, 2900)
        return _typed(f"{a} + {b} = {a + b}. Use this to answer: {a + b} − {b} = ?", a)

    def estimate():
        a, b = random.randint(1200, 6800), random.randint(1200, 2900)
        return _mc(f"Without working it out exactly: which is the best estimate for {a} + {b}?",
                   _round_sig1(a) + _round_sig1(b),
                   {(_round_sig1(a) + _round_sig1(b)) * 10: "Place value — 10 times too big",
                    (_round_sig1(a) + _round_sig1(b)) // 10: "Place value — 10 times too small",
                    abs(_round_sig1(a) - _round_sig1(b)) or 100: "Mixes up the operation"}, ESTIMATE)

    return [spot, inverse, estimate]


def _sub_whole_items():
    def spot():
        while True:
            a, b = random.randint(3000, 9800), random.randint(1200, 2900)
            if _smaller_from_larger(a, b) != a - b:
                break
        return _spot(f"{a} − {b}", a - b, _smaller_from_larger(a, b),
                     "Took the smaller digit from the larger in each column")

    def inverse():
        a, b = random.randint(3000, 9800), random.randint(1200, 2900)
        return _typed(f"{a} − {b} = {a - b}. Use this to answer: {a - b} + {b} = ?", a)

    def derived():
        a, b = random.randint(3000, 9800), random.randint(1200, 2900)
        return _typed(f"{a} − {b} = {a - b}. Use this to answer: {a} − {b + 100} = ?", a - b - 100)

    return [spot, inverse, derived]


def _bidmas_easy_items():
    def spot():
        a, b, c = random.randint(15, 30), random.randint(2, 6), random.randint(2, 5)
        return _spot(f"{a} − {b} × {c}", a - b * c, (a - b) * c, "Worked left to right instead of multiplying first")

    def first():
        a, b, c = random.randint(2, 9), random.randint(2, 9), random.randint(2, 9)
        return _mc(f"In {a} + {b} × {c}, which part do you work out first?", f"{b} × {c}",
                   {f"{a} + {b}": "Works left to right", "It doesn't matter": "Doesn't know the order of operations"})

    def brackets():
        a, b, c = random.randint(2, 9), random.randint(2, 9), random.randint(2, 9)
        return _mc(f"Where do brackets go so that {a} + {b} × {c} = {(a + b) * c}?", f"({a} + {b}) × {c}",
                   {f"{a} + ({b} × {c})": "These brackets don't change the answer",
                    "No brackets needed": "Works left to right"})

    return [spot, first, brackets]


def _bidmas_hard_items():
    def spot_square():
        a, b, c = random.randint(3, 9), random.randint(2, 5), random.randint(2, 5)
        return _spot(f"{a}² − {b} × {c}", a * a - b * c, 2 * a - b * c, "Thinks squaring means multiplying by 2")

    def spot_neg():
        a = random.randint(2, 5)
        b = a + random.randint(1, 4)
        c, d = random.randint(2, 6), random.randint(2, 6)
        return _spot(f"({a} − {b})² + {c} × {d}", (a - b) ** 2 + c * d, -((a - b) ** 2) + c * d,
                     "Thinks a negative number squared is negative")

    def first():
        a, b, c, d = (random.randint(2, 9) for _ in range(4))
        return _mc(f"In {a} + ({b} − {c})² × {d}, which step comes first?", f"{b} − {c}",
                   {f"{a} + {b}": "Works left to right", f"{c}² × {d}": "Powers before brackets",
                    f"{c} × {d}": "Unsure of the order of operations"})

    return [spot_square, spot_neg, first]


def _mult_dec_items():
    def derived():
        A, b = random.randint(12, 99), random.randint(3, 9)
        return _typed(f"{A} × {b} = {A * b}. Use this to answer: {_fmt(A / 10)} × {b} = ?", A * b / 10)

    def spot():
        a, b = random.randint(2, 4), random.randint(2, 4)
        return _spot(f"0.{a} × 0.{b}", a * b / 100, a * b / 10, "Miscounted decimal places in the answer",
                     alt=a * b, alt_note="Ignored the decimal points")

    def estimate():
        a, b = round(random.uniform(2.1, 9.8), 1), random.randint(11, 48)
        return _estimate(f"{_fmt(a)} × {b}", a * b, round(a) * _round_sig1(b))

    return [derived, spot, estimate]


def _div_dec_items():
    def derived():
        b, q = random.randint(3, 9), random.randint(11, 49)
        return _typed(f"{b * q} ÷ {b} = {q}. Use this to answer: {_fmt(b * q / 10)} ÷ {b} = ?", q / 10)

    def half():
        a = random.randint(3, 12)
        return _mc(f"Is {a} ÷ 0.5 bigger or smaller than {a}?", f"Bigger — it's {2 * a}",
                   {f"Smaller — it's {_fmt(a / 2)}": "Thinks dividing always makes a number smaller",
                    f"The same — it's {a}": "Unsure what dividing by a decimal does"})

    def estimate():
        b, q = random.randint(3, 9), round(random.uniform(11, 49), 1)
        return _estimate(f"{_fmt(round(b * q, 1))} ÷ {b}", q, _round_sig1(q))

    return [derived, half, estimate]


def _place_value_items():
    def value():
        n = random.randint(1_200_000, 9_800_000)
        k = random.randint(3, 5)
        d = (n // 10 ** k) % 10
        while d == 0 or str(n).count(str(d)) > 1:
            n = random.randint(1_200_000, 9_800_000)
            d = (n // 10 ** k) % 10
        return _mc(f"In {n:,}, what is the digit {d} worth?", f"{d * 10 ** k:,}",
                   {f"{d * 10 ** (k - 1):,}": "Miscounted the place", f"{d * 10 ** (k + 1):,}": "Miscounted the place",
                    str(d): "Reads the digit as ones"})

    def more():
        n = random.randint(120_000, 980_000)
        return _mc(f"Which number is ten thousand more than {n:,}?", f"{n + 10_000:,}",
                   {f"{n + 1_000:,}": "Changed the thousands", f"{n + 100_000:,}": "Changed the hundred thousands",
                    f"{n * 10:,}": "Multiplied by 10 instead of adding ten thousand"})

    def spot():
        th, small = random.randint(2, 9), random.randint(3, 60)
        words = {2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine"}[th]
        return _spot(f'"{words} thousand and {small}" in digits', th * 1000 + small, int(f"{th}{small}"),
                     "Missing placeholder zeros")

    return [value, more, spot]


def _fdp_items():
    def spot():
        d = random.choice([1, 2, 3, 4, 6, 7, 8, 9])
        if random.random() < 0.5:
            return _spot(f"0.{d} as a percentage", f"{d * 10}%", f"{d}%", "Multiplied by 10, not 100")
        return _spot(f"0.0{d} as a percentage", f"{d}%", f"{d * 10}%", "Unsure about the place of the zero")

    def derived():
        n, d = random.choice([(1, 4), (1, 5), (1, 10), (1, 20)])
        k = random.randint(2, d - 1)
        return _typed(f"{n}/{d} = {_fmt(100 / d)}%. Use this to answer: {k}/{d} = ?%", 100 * k / d)

    def biggest():
        t = random.choice([3, 4, 6, 7])
        return _mc(f"Which is the biggest: 0.{t}, {t * 10 + 2}% or 0.{t - 1}99?", f"{t * 10 + 2}%",
                   {f"0.{t}": "Unsure how decimals compare with percentages",
                    f"0.{t - 1}99": "Thinks more decimal digits means bigger"})

    return [spot, derived, biggest]


def _times_pow10_items(div: bool):
    op = "÷" if div else "×"

    def spot():
        if div:
            n = round(random.uniform(1.1, 9.9), 1)
            return _spot(f"{_fmt(n)} ÷ 10", n / 10, float(f"{int(n)}.0{int(round(n * 10)) % 10}"),
                         "Put a zero after the decimal point instead of moving the digits")
        n = round(random.uniform(1.1, 9.9), 1)
        return _spot(f"{_fmt(n)} × 100", n * 100, f"{_fmt(n)}00", "Thinks multiplying by 100 means adding two zeros")

    def move():
        return _mc(f"When you {'divide' if div else 'multiply'} a number by 100, what happens to the digits?",
                   f"They move 2 places to the {'right' if div else 'left'}",
                   {f"They move 2 places to the {'left' if div else 'right'}": "Moves digits the wrong way",
                    "You add/remove two zeros": "Only works for whole numbers — not decimals",
                    "The decimal point moves 1 place": "Confuses 100 with 10"})

    def derived():
        n = round(random.uniform(1.1, 99.9), 1)
        ten = n / 10 if div else n * 10
        return _typed(f"{_fmt(n)} {op} 10 = {_fmt(ten)}. Use this to answer: {_fmt(n)} {op} 100 = ?",
                      n / 100 if div else n * 100)

    return [spot, move, derived]


def _add_dec_items():
    def spot():
        a = random.randint(2, 9) + random.randint(1, 9) / 10
        b = random.randint(1, 9) + random.randint(11, 99) / 100
        wrong = (round(a * 10) + round(b * 100)) / 100
        return _spot(f"{_fmt(a)} + {_fmt(b)}", round(a + b, 2), wrong,
                     "Lined up the right-hand digits instead of the decimal points")

    def derived():
        A, B = random.randint(120, 890), random.randint(120, 890)
        return _typed(f"{A} + {B} = {A + B}. Use this to answer: {_fmt(A / 100)} + {_fmt(B / 100)} = ?", (A + B) / 100)

    def estimate():
        a, b = round(random.uniform(11, 89), 2), round(random.uniform(11, 89), 2)
        return _mc(f"Without working it out exactly: which is the best estimate for {_fmt(a)} + {_fmt(b)}?",
                   round(a) + round(b),
                   {(round(a) + round(b)) * 10: "Place value — 10 times too big",
                    _fmt((round(a) + round(b)) / 10): "Place value — 10 times too small",
                    abs(round(a) - round(b)): "Mixes up the operation"}, ESTIMATE)

    return [spot, derived, estimate]


def _sub_dec_items():
    def spot():
        w, d = random.randint(5, 9), random.randint(1, 4) + random.randint(1, 9) / 10
        return _spot(f"{w} − {_fmt(d)}", round(w - d, 1), round(w - int(d) + (d - int(d)), 1),
                     "Subtracted the whole numbers and brought the decimal part down")

    def inverse():
        a, b = round(random.uniform(20, 90), 2), round(random.uniform(1, 19), 2)
        return _typed(f"{_fmt(a)} − {_fmt(b)} = {_fmt(round(a - b, 2))}. Use this to answer: "
                      f"{_fmt(round(a - b, 2))} + {_fmt(b)} = ?", a)

    def estimate():
        a, b = round(random.uniform(40, 98), 2), round(random.uniform(11, 39), 2)
        return _mc(f"Without working it out exactly: which is the best estimate for {_fmt(a)} − {_fmt(b)}?",
                   round(a) - round(b),
                   {(round(a) - round(b)) * 10: "Place value — 10 times too big",
                    round(a) + round(b): "Mixes up the operation",
                    _fmt((round(a) - round(b)) / 10): "Place value — 10 times too small"}, ESTIMATE)

    return [spot, inverse, estimate]


def _neg_mult_items(div: bool):
    op = "÷" if div else "×"

    def pattern():
        b = random.randint(2, 9)
        lines = ", ".join(f"{k} × {_n(-b)} = {-k * b}" for k in (3, 2, 1, 0))
        return _typed(f"Look at the pattern: {lines}. Continue it: (-1) × {_n(-b)} = ?", b, REASON)

    def sign():
        a, b = random.randint(2, 12), random.randint(2, 12)
        expr = f"{_n(-a * b)} {op} {_n(-b)}" if div else f"{_n(-a)} × {_n(-b)}"
        return _mc(f"Without working it out: is {expr} positive or negative?", "Positive",
                   {"Negative": "Thinks two negatives make a negative", "It could be either": "Unsure of the sign rules"})

    def spot():
        a, b = random.randint(2, 12), random.randint(2, 12)
        if div:
            return _spot(f"{_n(-a * b)} ÷ {_n(-b)}", a, -a, "Thinks two negatives make a negative")
        return _spot(f"{_n(-a)} × {_n(-b)}", a * b, -a * b, "Thinks two negatives make a negative")

    def inverse():
        a, b = random.randint(2, 12), random.randint(2, 12)
        return _typed(f"{_n(-a)} × {b} = {-a * b}. Use this to answer: {_n(-a * b)} ÷ {b} = ?", -a)

    return [pattern, sign, spot, inverse] if div else [pattern, sign, spot]


def _simplify_items():
    def which():
        n, d = random.choice([(2, 3), (3, 4), (2, 5), (3, 5), (4, 7), (5, 6)])
        g = random.randint(2, 5)
        k = random.randint(1, n * g - 1)
        return _mc(f"Which fraction is equal to {n * g}/{d * g}?", f"{n}/{d}",
                   {f"{n * g - k}/{d * g - k}": "Took the same number off the top and bottom",
                    f"{d}/{n}": "Turned the fraction upside down", f"{n}/{d * g}": "Divided only the top"})

    def fully():
        n, d = random.choice([(1, 3), (2, 3), (3, 4), (2, 5), (4, 5), (5, 6)])
        who = random.choice(NAMES)
        return _mc(f"{who} simplifies {n * 4}/{d * 4} to {n * 2}/{d * 2}. Is it in its simplest form?",
                   f"No — it simplifies to {n}/{d}",
                   {"Yes": "Stops before the fraction is fully simplified",
                    f"No — it simplifies to {n * 2 - 1}/{d * 2 - 1}": "Took the same number off the top and bottom"})

    def why():
        n, d = random.choice([(7, 11), (5, 9), (8, 15), (4, 9), (9, 14)])
        return _mc(f"How do you know {n}/{d} is in its simplest form?",
                   f"{n} and {d} have no common factor except 1",
                   {"The top number is smaller than the bottom": "Thinks proper means simplified",
                    "Both numbers are odd" if n % 2 and d % 2 else "One number is odd": "Uses odd/even instead of factors",
                    f"{d} is not in the {n} times table": "Only checks one number"})

    return [which, fully, why]


def _round_dp_items():
    def spot_nine():
        w = random.randint(1, 9)
        x = round(w + random.choice([0.95, 0.96, 0.97, 0.98]), 2)
        return _spot(f"{_fmt(x)} rounded to 1 decimal place", f"{w + 1}.0", f"{w}.10",
                     "Rounded the 9 up to 10 in the tenths column")

    def spot_chain():
        w, t = random.randint(1, 9), random.randint(1, 8)
        x = f"{w}.{t}4{random.randint(5, 9)}"
        return _spot(f"{x} rounded to 1 decimal place", f"{w}.{t}", f"{w}.{t + 1}",
                     "Rounded in steps (chain rounding) instead of looking at the next digit only")

    def which():
        w, t = random.randint(1, 9), random.randint(2, 8)
        ok = f"{w}.{t - 1}{random.randint(5, 9)}"
        return _mc(f"Which number rounds to {w}.{t} to 1 decimal place?", ok,
                   {f"{w}.{t}5": "Rounds 5 down", f"{w}.0{t}": "Looks at the wrong digit",
                    f"{w}.{t - 1}{random.randint(0, 4)}": "Rounds down digits under 5 the wrong way"})

    return [spot_nine, spot_chain, which]


def _substitution_items():
    def spot_concat():
        a, k = random.randint(2, 9), random.randint(2, 5)
        return _spot(f"if a = {a}, then {k}a", k * a, int(f"{k}{a}"), "Wrote the digits next to each other instead of multiplying")

    def spot_square():
        a = random.randint(3, 9)
        return _spot(f"if a = {a}, then a²", a * a, 2 * a, "Thinks squaring means multiplying by 2")

    def meaning():
        return _mc("What does 2ab mean?", "2 × a × b",
                   {"2 + a + b": "Thinks letters next to each other are added", "2a + b": "Applies the 2 to a only",
                    "2 × a + b": "Applies the multiplication to a only"})

    return [spot_concat, spot_square, meaning]


def _directed_items():
    def warmer():
        a, b = random.randint(5, 12), random.randint(1, 4)
        return _mc(f"Which temperature is warmer: -{a}°C or -{b}°C?", f"-{b}°C",
                   {f"-{a}°C": "Thinks −8 is bigger than −3 because 8 > 3", "They are the same": "Ignores the sign"})

    def context():
        a, b = random.randint(-9, -2), random.randint(3, 12)
        return _typed(f"The temperature is {a}°C. It rises by {b} degrees. What is the new temperature (°C)?", a + b, REPRESENT)

    def spot():
        a, b = random.randint(3, 9), random.randint(10, 15)
        return _spot(f"{_n(-a)} + {b}", b - a, -(a + b), "Ignored the direction — added the sizes and kept the sign")

    return [warmer, context, spot]


def _add_neg_items():
    def same():
        a, b = random.randint(3, 15), random.randint(1, 12)
        return _mc(f"Which is the same as {a} + {_n(-b)}?", f"{a} − {b}",
                   {f"{a} + {b}": "Ignores the negative sign", f"{b} − {a}": "Swaps the numbers round",
                    f"{_n(-a)} − {b}": "Unsure about the signs"})

    def pattern():
        a = random.randint(3, 9)
        return _typed(f"Look at the pattern: {a} + 2 = {a + 2}, {a} + 1 = {a + 1}, {a} + 0 = {a}. "
                      f"Continue it: {a} + (-1) = ?", a - 1, REASON)

    def spot():
        a, b = random.randint(3, 15), random.randint(1, 12)
        return _spot(f"{a} + {_n(-b)}", a - b, a + b, "Ignores the negative — adds the numbers")

    return [same, pattern, spot]


def _sub_neg_items():
    def same():
        a, b = random.randint(-9, 12), random.randint(1, 12)
        return _mc(f"Which is the same as {_n(a)} − {_n(-b)}?", f"{_n(a)} + {b}",
                   {f"{_n(a)} − {b}": "Thinks subtracting a negative makes it smaller",
                    f"{b} − {_n(a)}": "Swaps the numbers round", f"{_n(-a)} − {b}": "Unsure about the signs"})

    def pattern():
        a = random.randint(3, 9)
        return _typed(f"Look at the pattern: {a} − 2 = {a - 2}, {a} − 1 = {a - 1}, {a} − 0 = {a}. "
                      f"Continue it: {a} − (-1) = ?", a + 1, REASON)

    def context():
        hi, lo = random.randint(3, 15), random.randint(-12, -2)
        return _typed(f"It is {hi}°C in Glasgow and {lo}°C in Oslo. How many degrees warmer is Glasgow?",
                      hi - lo, REPRESENT)

    return [same, pattern, context]


def _sig_fig_items():
    def spot_zeros():
        n = random.randint(21_000, 98_000) + random.randint(1, 999)
        return _spot(f"{n:,} rounded to 1 significant figure", f"{_round_sig1(n):,.0f}",
                     str(int(_round_sig1(n)) // 10 ** (len(str(n)) - 1)), "Forgot the placeholder zeros")

    def count():
        n = random.choice(["0.0305", "0.405", "0.00307"])
        return _mc(f"How many significant figures does {n} have?", 3,
                   {len(n) - 1: "Counts the leading zeros as significant",
                    2: "Doesn't count a zero between other digits", 1: "Unsure what a significant figure is"})

    def spot_small():
        d1, d2, d3 = random.randint(1, 9), random.randint(1, 8), random.randint(5, 9)
        x = f"0.00{d1}{d2}{d3}"
        r = f"0.00{d1}{d2 + 1}"
        return _spot(f"{x} rounded to 2 significant figures", r, "0.0", "Counted the leading zeros as significant figures",
                     alt=f"0.00{d1}{d2}", alt_note="Cut the number off instead of rounding")

    return [spot_zeros, count, spot_small]


def _factor_items():
    def pair():
        n = random.choice([24, 36, 48, 60, 72])
        f = random.choice([d for d in range(2, 13) if n % d == 0])
        return _typed(f"{f} is a factor of {n}. Which other factor of {n} pairs with {f} (multiplies by {f} to make {n})?",
                      n // f, REASON)

    def all_factors():
        n = random.choice([12, 18, 20, 28, 30])
        fs = [d for d in range(1, n + 1) if n % d == 0]
        miss = random.choice(fs[1:-1])
        return _mc(f"Which list shows ALL the factors of {n}?", ", ".join(map(str, fs)),
                   {", ".join(str(d) for d in fs if d != miss): "Missed a factor pair",
                    ", ".join(str(n * k) for k in range(1, 5)): "Confuses factors and multiples",
                    ", ".join(str(d) for d in fs if d not in (1, n)): "Leaves out 1 and the number itself"})

    def spot():
        n = random.choice([6, 8, 9, 10, 12])
        return _spot(f"the three smallest factors of {n}",
                     ", ".join(map(str, [d for d in range(1, n + 1) if n % d == 0][:3])),
                     f"{n}, {2 * n}, {3 * n}", "Listed multiples instead of factors")

    return [pair, all_factors, spot]


def _multiple_items():
    def common():
        a, b = random.choice([(3, 4), (4, 6), (2, 5), (3, 5), (6, 8)])
        l = a * b // math.gcd(a, b)
        return _mc(f"Which number is a multiple of both {a} and {b}?", l,
                   {a + b: "Added the numbers", l + a: f"Only a multiple of {a}" if (l + a) % b else "Unsure",
                    l + b: f"Only a multiple of {b}" if (l + b) % a else "Unsure"})

    def tenth():
        n = random.randint(3, 15)
        return _typed(f"What is the 10th multiple of {n}?", 10 * n, REASON)

    def spot():
        n = random.choice([6, 8, 10, 12])
        facs = [d for d in range(1, n + 1) if n % d == 0][:4]
        return _spot(f"the first four multiples of {n}", f"{n}, {2 * n}, {3 * n}, {4 * n}",
                     ", ".join(map(str, facs)), "Listed factors instead of multiples")

    return [common, tenth, spot]


def _square_items():
    def spot():
        n = random.randint(3, 12)
        return _spot(f"{n}²", n * n, 2 * n, "Thinks squaring means multiplying by 2")

    def between():
        n = random.randint(4, 11)
        x = n * n + random.randint(2, 2 * n - 1)
        return _mc(f"√{x} is between which two whole numbers?", f"{n} and {n + 1}",
                   {f"{x // 2} and {x // 2 + 1}": "Halved instead of square-rooting",
                    f"{n - 1} and {n}": "Close — check the squares", f"{n + 1} and {n + 2}": "Close — check the squares"},
                   ESTIMATE)

    def derived():
        n = random.randint(2, 9)
        return _typed(f"{n}² = {n * n}. Use this to answer: {n * 10}² = ?", 100 * n * n)

    return [spot, between, derived]


def _cube_items():
    def spot():
        n = random.randint(2, 6)
        return _spot(f"{n}³", n ** 3, 3 * n, "Thinks cubing means multiplying by 3")

    def which():
        c = random.choice([8, 27, 64, 125])
        return _mc("Which of these is a cube number?", c,
                   {c + 1: "Unsure what a cube number is", round(c ** (1 / 3)) ** 2: "Confuses square and cube numbers",
                    3 * round(c ** (1 / 3)): "Thinks cubing means × 3"})

    def model():
        n = random.randint(2, 5)
        return _typed(f"A big cube is built from 1 cm cubes. Each edge is {n} cm long. How many small cubes are used?",
                      n ** 3, REPRESENT)

    return [spot, which, model]


def _equiv_frac_items():
    def which():
        n, d = random.choice([(1, 3), (2, 3), (3, 4), (2, 5), (3, 5)])
        k = random.randint(2, 4)
        return _mc(f"Which fraction is equivalent to {n}/{d}?", f"{n * k}/{d * k}",
                   {f"{n + k}/{d + k}": "Added the same number to top and bottom",
                    f"{d}/{n}": "Turned the fraction upside down", f"{n * k}/{d}": "Multiplied only the top"})

    def spot():
        n, d = random.choice([(1, 3), (2, 3), (3, 4), (2, 5), (3, 5)])
        k = random.randint(2, 3)
        return _spot(f"{n}/{d} = {n * k}/☐, so ☐", d * k, d + n * k - n,
                     "Added to the top and bottom instead of multiplying")

    def bigger():
        return _mc("Which is bigger: 3/4 or 5/8?", "3/4",
                   {"5/8": "Thinks bigger numbers on top/bottom mean a bigger fraction",
                    "They are the same": "Unsure how to compare fractions"})

    return [which, spot, bigger]


def _frac_amount_items():
    def method():
        n, d = random.choice([(2, 3), (3, 4), (2, 5), (3, 5), (5, 6)])
        return _mc(f"How do you find {n}/{d} of an amount?", f"Divide by {d}, then multiply by {n}",
                   {f"Divide by {n}, then multiply by {d}": "Swapped the numerator and denominator",
                    f"Divide by {d} only": "Found the unit fraction only",
                    f"Take {n} away, then divide by {d}": "Unsure what a fraction of an amount means"})

    def spot():
        n, d = random.choice([(2, 3), (3, 4), (2, 5), (3, 5)])
        u = random.randint(3, 12)
        return _spot(f"{n}/{d} of {d * u}", n * u, u, "Found the unit fraction only (didn't multiply by the numerator)",
                     alt=d * u - u if d * u - u != n * u else None, alt_note="Took one part away from the whole")

    def reverse():
        n, d = random.choice([(1, 4), (1, 5), (3, 4), (2, 3), (2, 5)])
        u = random.randint(3, 12)
        return _typed(f"{n}/{d} of a number is {n * u}. What is the number?", d * u, REASON)

    return [method, spot, reverse]


def _pct_amount_items():
    def derived():
        A = random.choice([40, 60, 80, 120, 150, 200, 240])
        p = random.choice([20, 30, 40, 60, 5])
        return _typed(f"10% of £{A} is £{_fmt(A / 10)}. Use this to find {p}% of £{A} (in £).", A * p / 100)

    def spot():
        A = random.choice([40, 60, 80, 120, 200])
        p = random.choice([20, 25, 30])
        return _spot(f"{p}% of £{A}", f"£{_fmt(A * p / 100)}", f"£{p}", "Gave the percentage itself as the answer",
                     alt=f"£{A - p}", alt_note="Took the percentage away as a number")

    def reverse():
        x = random.randint(3, 15)
        return _typed(f"10% of a number is {x}. What is the number?", 10 * x, REASON)

    def half():
        return _mc("Which of these is the same as 25%?", "1/4",
                   {"1/25": "Thinks a percent is 'one over' the number", "2/5": "Reads 25 as 2 and 5",
                    "0.025": "Divided by 1000 not 100"})

    return [derived, spot, reverse, half]


CONCEPT_ITEMS: dict[str, list[Callable[[], ConceptItem]]] = {
    "MS1": _bond_items(lambda: 5),
    "MS2": _bond_items(lambda: 10),
    "MS30": _bond_items(lambda: random.choice([6, 7, 8, 9])),
    "MS3": _bond_items(lambda: 20),
    "MS4": _bond_items(lambda: 100),
    "MS5": _double_items(1, 9),
    "MS6": _double_items(11, 49),
    "MS7": _halve_items(2, 9),
    "MS8": _halve_items(20, 98),
    "MS9": _plus_ten_items(1),
    "MS10": _plus_ten_items(-1),
    "MS28": _add9_items(),
    "MS29": _bridge20_items(),
    "MS11": _plus_mult10_items(1),
    "MS12": _plus_mult10_items(-1),
    "MS13": _to_mult10_items(),
    "MS14": _near_double_items(),
    "MS15": _partition1_items(),
    "MS16": _partition2_items(),
    "MS17": _bridge_mult10_items(1),
    "MS18": _bridge_mult10_items(-1),
    "MS19": _count_up_items(),
    "MS20": _reorder_items(),
    "MS21": _repeated_add_items(),
    "MS22": _inverse_div_items(),
    "MS23": _equiv_calc_items(),
    "MS25": _clock24_items(),
    "MS26": _time_items(),
    "MS27": _time_items(),
    "KS1": _mult_whole_items(),
    "KS2": _div_whole_items(),
    "KS3": _add_whole_items(),
    "KS4": _sub_whole_items(),
    "KS5": _bidmas_easy_items(),
    "KS6": _bidmas_hard_items(),
    "KS7": _mult_dec_items(),
    "KS8": _div_dec_items(),
    "KS9": _place_value_items(),
    "KS10": _fdp_items(),
    "KS11": _times_pow10_items(False),
    "KS12": _times_pow10_items(True),
    "KS13": _add_dec_items(),
    "KS14": _sub_dec_items(),
    "KS15": _neg_mult_items(False),
    "KS16": _neg_mult_items(True),
    "KS17": _simplify_items(),
    "KS18": _round_dp_items(),
    "KS19": _substitution_items(),
    "KS20": _directed_items(),
    "KS21": _add_neg_items(),
    "KS22": _sub_neg_items(),
    "KS24": _sig_fig_items(),
    "KS25": _factor_items(),
    "KS26": _multiple_items(),
    "KS28": _square_items(),
    "KS29": _cube_items(),
    "KS30": _equiv_frac_items(),
    "KS31": _frac_amount_items(),
    "KS32": _pct_amount_items(),
}


def concept_items(skill_id: str, n: int) -> list[ConceptItem]:
    """`n` items for a skill, using a different kind of item each time where
    the skill has enough kinds."""
    makers = list(CONCEPT_ITEMS[skill_id])
    random.shuffle(makers)
    return [makers[i % len(makers)]() for i in range(n)]
