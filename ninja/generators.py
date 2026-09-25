"""One question-generator function per BGE Numeracy skill.

Each generator takes no arguments and returns a `Question`, with fresh
random numbers every call and a scaffold appropriate to that skill.
"""
from __future__ import annotations

import math
import random
from fractions import Fraction

from . import scaffolds as sc
from .checking import (
    any_of_check,
    exact_text_check,
    fraction_check,
    list_check,
    numeric_check,
    yes_no_check,
)
from .question import Question

# --------------------------------------------------------------------------
# small helpers
# --------------------------------------------------------------------------

ONES = ["", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine",
        "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen",
        "seventeen", "eighteen", "nineteen"]
TENS = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]


def _three_digit_words(n: int) -> str:
    parts = []
    if n >= 100:
        parts.append(f"{ONES[n // 100]} Hundred")
        n %= 100
        if n:
            parts.append("and")
    if n >= 20:
        w = TENS[n // 10]
        if n % 10:
            w += f"-{ONES[n % 10].lower()}"
        parts.append(w)
    elif n > 0:
        parts.append(ONES[n])
    return " ".join(parts)


def number_to_words(n: int) -> str:
    if n == 0:
        return "Zero"
    groups = [("Million", 1_000_000), ("Thousand", 1_000)]
    words = []
    remaining = n
    for name, size in groups:
        if remaining >= size:
            count = remaining // size
            words.append(f"{_three_digit_words(count)} {name}")
            remaining %= size
    if remaining:
        words.append(_three_digit_words(remaining))
    return ", ".join(words).replace(" ,", ",")


def _fmt(n) -> str:
    if isinstance(n, float):
        if n == int(n):
            return str(int(n))
        return f"{n:g}"
    return str(n)


# --------------------------------------------------------------------------
# KEY SKILLS
# --------------------------------------------------------------------------

def ks_multiply_whole_numbers() -> Question:
    a = random.randint(12, 950)
    b = random.randint(3, 90)
    ans = a * b
    scaffold = sc.hint_list([
        f"Split {a} into friendlier parts, e.g. tens and ones.",
        f"Multiply {b} by each part separately.",
        "Add the partial answers back together.",
    ], note="Grid / partial-products method.")
    return Question(f"{a} × {b} =", str(ans), numeric_check(ans), scaffold)


def ks_divide_whole_numbers() -> Question:
    b = random.randint(3, 12)
    q = random.randint(20, 400)
    a = a_val = b * q
    scaffold = sc.hint_list([
        f"How many groups of {b} fit into {a}?",
        f"Try multiplying {b} by 10, 20, 30… to get close first.",
        "Subtract that chunk, then finish the remainder.",
    ], note="Chunking method.")
    return Question(f"{a} ÷ {b} =", str(q), numeric_check(q), scaffold)


def ks_add_whole_numbers() -> Question:
    a = random.randint(200, 9500)
    b = random.randint(200, 9500)
    ans = a + b
    scaffold = sc.place_value_grid(
        _fmt(max(a, b)).rjust(4, " "), ["Th", "H", "T", "U"],
        note="Line up the place-value columns, then add starting from the units.",
    )
    return Question(f"{a} + {b} =", str(ans), numeric_check(ans), scaffold)


def ks_subtract_whole_numbers() -> Question:
    a = random.randint(1000, 9800)
    b = random.randint(200, a - 100)
    ans = a - b
    scaffold = sc.hint_list([
        f"Line up {a} and {b} by place value (units under units).",
        "Subtract column by column, starting with the units.",
        "Exchange (borrow) from the next column if you need to.",
    ])
    return Question(f"{a} - {b} =", str(ans), numeric_check(ans), scaffold)


def _rand_op_val(lo=2, hi=12):
    return random.randint(lo, hi)


def ks_order_of_operations_easy() -> Question:
    template = random.choice(["div_sub", "mul_add", "sub_mul"])
    if template == "div_sub":
        b = _rand_op_val(2, 9)
        q = _rand_op_val(2, 9)
        a = b * q
        c = _rand_op_val(1, 9)
        expr = f"{a} ÷ {b} - {c}"
        ans = a / b - c
        steps = [f"Divide first: {a} ÷ {b} = {a // b}", f"Then subtract: {a // b} - {c}"]
    elif template == "mul_add":
        a = _rand_op_val(2, 9)
        b = _rand_op_val(2, 9)
        c = _rand_op_val(1, 20)
        expr = f"{a} × {b} + {c}"
        ans = a * b + c
        steps = [f"Multiply first: {a} × {b} = {a*b}", f"Then add: {a*b} + {c}"]
    else:
        a = _rand_op_val(10, 30)
        b = _rand_op_val(2, 9)
        c = _rand_op_val(2, 9)
        expr = f"{a} - {b} × {c}"
        ans = a - b * c
        steps = [f"Multiply first: {b} × {c} = {b*c}", f"Then subtract: {a} - {b*c}"]
    scaffold = sc.hint_list(["Remember: multiply/divide before you add/subtract."] + steps)
    return Question(expr, _fmt(ans), numeric_check(ans), scaffold)


def ks_order_of_operations_harder() -> Question:
    a = _rand_op_val(2, 9)
    b = _rand_op_val(2, 9)
    c = _rand_op_val(2, 9)
    d = _rand_op_val(2, 9)
    template = random.choice(["bracket_sq", "sq_mul"])
    if template == "bracket_sq":
        expr = f"({a} - {b})² + {c} × {d}"
        inner = a - b
        ans = inner ** 2 + c * d
        steps = [
            "Brackets first.",
            f"({a} - {b}) = {inner}",
            f"Square it: {inner}² = {inner**2}",
            f"Multiply: {c} × {d} = {c*d}",
            f"Add: {inner**2} + {c*d}",
        ]
    else:
        expr = f"{a}² - {b} × {c}"
        ans = a ** 2 - b * c
        steps = [
            "Powers first.",
            f"{a}² = {a**2}",
            f"Multiply: {b} × {c} = {b*c}",
            f"Subtract: {a**2} - {b*c}",
        ]
    scaffold = sc.hint_list(["Order: Brackets, then Powers, then × ÷, then + −."] + steps)
    return Question(expr, _fmt(ans), numeric_check(ans), scaffold)


def ks_multiply_decimal_numbers() -> Question:
    a = round(random.uniform(1.1, 9.9), 1)
    b = random.randint(2, 12)
    ans = round(a * b, 2)
    scaffold = sc.hint_list([
        f"Ignore the decimal point: work out {round(a*10)} × {b}.",
        "Now put the decimal point back — count 1 digit in from the right.",
    ])
    return Question(f"{a} × {b} =", _fmt(ans), numeric_check(ans), scaffold)


def ks_divide_decimal_numbers() -> Question:
    b = random.randint(2, 9)
    q = round(random.uniform(1.0, 20.0), 1)
    a = round(q * b, 2)
    scaffold = sc.hint_list([
        f"Divide as if there were no decimal point, then place it in the answer directly above.",
        f"{a} ÷ {b}",
    ])
    return Question(f"{a} ÷ {b} =", _fmt(round(a / b, 2)), numeric_check(a / b, 0.05), scaffold)


def ks_place_value() -> Question:
    n = random.randint(100000, 9_876_543)
    words = number_to_words(n)
    scaffold = sc.hint_list([
        "Break the words into groups: millions, thousands, then hundreds/tens/units.",
        "Write each group's digits in order.",
    ])
    return Question(f"Write “{words}” in digits", str(n), numeric_check(n), scaffold)


def ks_convert_fdp() -> Question:
    template = random.choice(["pct_to_dec", "pct_to_frac", "dec_to_pct", "frac_to_pct"])
    if template == "pct_to_dec":
        p = random.randint(1, 99)
        ans = p / 100
        scaffold = sc.hint_list([f"Divide {p} by 100.", "Move the decimal point 2 places left."])
        return Question(f"{p}% as a decimal", _fmt(ans), numeric_check(ans, 0.001), scaffold)
    if template == "pct_to_frac":
        p = random.choice([10, 20, 25, 40, 50, 60, 75, 80, 90])
        frac = Fraction(p, 100)
        scaffold = sc.hint_list([f"Write {p}/100, then simplify by dividing top and bottom by the same number."])
        return Question(f"{p}% as a fraction in its simplest form", f"{frac.numerator}/{frac.denominator}", fraction_check(frac), scaffold)
    if template == "dec_to_pct":
        d = round(random.uniform(0.02, 0.98), 2)
        ans = round(d * 100, 2)
        scaffold = sc.hint_list([f"Multiply {d} by 100.", "Move the decimal point 2 places right."])
        return Question(f"{d} = ☐%", _fmt(ans), numeric_check(ans, 0.5), scaffold)
    num = random.randint(1, 4)
    den = random.choice([4, 5, 10, 20, 25])
    while num >= den:
        num = random.randint(1, den - 1)
    ans = round(100 * num / den, 1)
    scaffold = sc.hint_list([f"Turn {num}/{den} into a fraction out of 100 first, or divide {num} by {den} and ×100."])
    return Question(f"{num}/{den} as a percentage", _fmt(ans), numeric_check(ans, 0.5), scaffold)


def ks_multiply_by_10_100_1000() -> Question:
    n = round(random.uniform(0.01, 99.9), 3)
    mult = random.choice([10, 100, 1000])
    ans = n * mult
    scaffold = sc.hint_list([f"Multiplying by {mult} moves every digit {len(str(mult))-1} place(s) to the left."])
    return Question(f"{n} × {mult} =", _fmt(round(ans, 3)), numeric_check(ans, 0.001), scaffold)


def ks_divide_by_10_100_1000() -> Question:
    n = round(random.uniform(1, 9999), 3)
    div = random.choice([10, 100, 1000])
    ans = n / div
    scaffold = sc.hint_list([f"Dividing by {div} moves every digit {len(str(div))-1} place(s) to the right."])
    return Question(f"{n} ÷ {div} =", _fmt(round(ans, 3)), numeric_check(ans, 0.001), scaffold)


def ks_add_decimal_numbers() -> Question:
    a = round(random.uniform(1, 90), 2)
    b = round(random.uniform(1, 90), 2)
    ans = round(a + b, 2)
    scaffold = sc.hint_list([f"Line up the decimal points under each other before adding {a} and {b}."])
    return Question(f"{a} + {b}", _fmt(ans), numeric_check(ans, 0.01), scaffold)


def ks_subtract_decimal_numbers() -> Question:
    a = round(random.uniform(10, 99), 2)
    b = round(random.uniform(1, a - 1), 2)
    ans = round(a - b, 2)
    scaffold = sc.hint_list([f"Line up the decimal points under each other before subtracting {b} from {a}."])
    return Question(f"{a} - {b}", _fmt(ans), numeric_check(ans, 0.01), scaffold)


def ks_multiply_negative_numbers() -> Question:
    a = random.randint(2, 12)
    b = random.randint(2, 12)
    signs = random.choice([(1, -1), (-1, 1), (-1, -1)])
    x, y = a * signs[0], b * signs[1]
    ans = x * y
    rule = "Same signs → positive answer." if signs[0] == signs[1] else "Different signs → negative answer."
    scaffold = sc.hint_list([rule, f"Multiply the sizes: {a} × {b} = {a*b}"])
    return Question(f"{x} × ({y})" if y < 0 else f"{x} × {y}", str(ans), numeric_check(ans), scaffold)


def ks_divide_negative_numbers() -> Question:
    b = random.randint(2, 12)
    q = random.randint(2, 12)
    signs = random.choice([(1, -1), (-1, 1), (-1, -1)])
    a = (b * q) * signs[0]
    d = b * signs[1]
    ans = a / d
    rule = "Same signs → positive answer." if signs[0] == signs[1] else "Different signs → negative answer."
    scaffold = sc.hint_list([rule, f"Divide the sizes: {abs(a)} ÷ {abs(d)} = {q}"])
    a_str = f"({a})" if a < 0 else f"{a}"
    d_str = f"({d})" if d < 0 else f"{d}"
    return Question(f"{a_str} ÷ {d_str}", str(int(ans)), numeric_check(ans), scaffold)


def ks_simplify_fractions() -> Question:
    g = random.randint(2, 9)
    num = random.randint(1, 9)
    den = random.randint(num + 1, 12)
    while math.gcd(num, den) != 1:
        num = random.randint(1, 9)
        den = random.randint(num + 1, 12)
    n2, d2 = num * g, den * g
    simplest = Fraction(n2, d2)
    scaffold = sc.hint_list([f"Find a common factor of {n2} and {d2}.", "Divide top and bottom by it, repeat until you can't simplify further."])
    return Question(f"Write {n2}/{d2} in its simplest form", f"{simplest.numerator}/{simplest.denominator}", fraction_check(simplest), scaffold)


def ks_round_to_decimal_places() -> Question:
    dp_source = round(random.uniform(1, 99), 4)
    dp = random.randint(1, 3)
    ans = round(dp_source, dp)
    scaffold = sc.hint_list([
        f"Look at the digit after the {dp} decimal place you're rounding to.",
        "5 or more → round up. Less than 5 → stays the same.",
    ])
    return Question(f"Round {dp_source} to {dp} decimal place{'s' if dp > 1 else ''}", _fmt(ans), numeric_check(ans, 10 ** (-dp) / 2), scaffold)


def ks_substitution() -> Question:
    a_v = random.randint(1, 9)
    b_v = random.randint(1, 9)
    c_v = random.randint(1, 9)
    template = random.choice(["3a-b2", "2a+bc", "ab-c"])
    if template == "3a-b2":
        expr = "3a - b²"
        ans = 3 * a_v - b_v ** 2
        steps = [f"a = {a_v}, b = {b_v}", f"3 × {a_v} = {3*a_v}", f"{b_v}² = {b_v**2}", f"{3*a_v} - {b_v**2}"]
    elif template == "2a+bc":
        expr = "2a + bc"
        ans = 2 * a_v + b_v * c_v
        steps = [f"a = {a_v}, b = {b_v}, c = {c_v}", f"2 × {a_v} = {2*a_v}", f"{b_v} × {c_v} = {b_v*c_v}", f"{2*a_v} + {b_v*c_v}"]
    else:
        expr = "ab - c"
        ans = a_v * b_v - c_v
        steps = [f"a = {a_v}, b = {b_v}, c = {c_v}", f"{a_v} × {b_v} = {a_v*b_v}", f"{a_v*b_v} - {c_v}"]
    scaffold = sc.hint_list(steps)
    return Question(f"If a = {a_v}, b = {b_v}, c = {c_v}, what is the value of {expr}?", str(ans), numeric_check(ans), scaffold)


def ks_simple_directed_number() -> Question:
    a = random.randint(-12, 12)
    b = random.randint(1, 12)
    op = random.choice(["+", "-"])
    ans = a + b if op == "+" else a - b
    a_str = f"({a})" if a < 0 else str(a)
    scaffold = sc.number_line(-15, 15, jumps=[(a, ans, ("+" if op == "+" else "-") + str(b), True)], circle=a, hide_value=ans)
    return Question(f"{a_str} {op} {b}", str(ans), numeric_check(ans), scaffold)


def ks_add_negative_number() -> Question:
    a = random.randint(-15, 15)
    b = random.randint(1, 15)
    ans = a + (-b)
    scaffold = sc.number_line(-20, 20, jumps=[(a, ans, f"-{b}", True)], circle=a, hide_value=ans)
    return Question(f"{a} + ({-b})", str(ans), numeric_check(ans), scaffold)


def ks_subtract_negative_number() -> Question:
    a = random.randint(-15, 15)
    b = random.randint(1, 15)
    ans = a - (-b)
    scaffold = sc.number_line(-20, 20, jumps=[(a, ans, f"+{b}", True)], circle=a, hide_value=ans)
    return Question(f"{a} - ({-b})", str(ans), numeric_check(ans), scaffold)


def ks_round_to_significant_figures() -> Question:
    n = round(random.uniform(0.0001, 98765), 6)
    sf = random.randint(1, 3)

    def round_sig(x, sig):
        if x == 0:
            return 0
        d = math.ceil(math.log10(abs(x)))
        power = sig - d
        factor = 10 ** power
        return round(x * factor) / factor

    ans = round_sig(n, sf)
    scaffold = sc.hint_list([
        "Count significant figures from the first non-zero digit.",
        f"Keep the first {sf}, then round the next digit.",
    ])
    return Question(f"Round {n} to {sf} significant figure{'s' if sf > 1 else ''}", _fmt(ans), numeric_check(ans, abs(ans) * 0.02 + 1e-9), scaffold)


def ks_factors() -> Question:
    n = random.choice([12, 18, 20, 24, 30, 36, 40, 45, 48, 60])
    candidate = random.randint(2, n // 2 + 1)
    is_factor = n % candidate == 0
    scaffold = sc.hint_list([f"Does {candidate} divide exactly into {n} with no remainder?"])
    return Question(f"Is {candidate} a factor of {n}?", "Yes" if is_factor else "No", yes_no_check(is_factor), scaffold)


def ks_multiples() -> Question:
    n = random.randint(3, 12)
    count = 4
    ans_list = [n * i for i in range(1, count + 1)]
    scaffold = sc.hint_list([f"Multiples of {n}: keep adding {n} each time.", f"{n}, {n*2}, …"])
    return Question(f"List the first {count} multiples of {n}", ", ".join(map(str, ans_list)), list_check(ans_list), scaffold)


def ks_square_numbers_and_roots() -> Question:
    n = random.randint(2, 15)
    if random.random() < 0.5:
        ans = n * n
        scaffold = sc.hint_list([f"{n}² means {n} × {n}."])
        return Question(f"What is {n}²?", str(ans), numeric_check(ans), scaffold)
    ans = n
    scaffold = sc.hint_list([f"Which number multiplied by itself gives {n*n}?"])
    return Question(f"What is the positive value of √{n*n}?", str(ans), numeric_check(ans), scaffold)


def ks_cube_numbers_and_roots() -> Question:
    n = random.randint(2, 10)
    if random.random() < 0.5:
        ans = n ** 3
        scaffold = sc.hint_list([f"{n}³ means {n} × {n} × {n}."])
        return Question(f"What is {n}³?", str(ans), numeric_check(ans), scaffold)
    ans = n
    scaffold = sc.hint_list([f"Which number, cubed, gives {n**3}?"])
    return Question(f"What is the value of ∛{n**3}?", str(ans), numeric_check(ans), scaffold)


def ks_equivalent_fractions() -> Question:
    num = random.randint(1, 6)
    den = random.randint(num + 1, 9)
    while math.gcd(num, den) != 1:
        num = random.randint(1, 6)
        den = random.randint(num + 1, 9)
    scale = random.randint(2, 6)
    missing_side = random.choice(["den", "num"])
    scaffold = sc.bar_model(f"{num}/{den}", [("", 1)] * den, note=f"Whatever you multiply the bottom by, multiply the top by the same number (×{scale}).")
    if missing_side == "den":
        prompt = f"{num}/{den} = {num*scale}/☐"
        ans = den * scale
    else:
        prompt = f"{num}/{den} = ☐/{den*scale}"
        ans = num * scale
    return Question(prompt, str(ans), numeric_check(ans), scaffold)


def ks_fraction_of_amount() -> Question:
    den = random.randint(2, 10)
    num = random.randint(1, den - 1)
    unit = random.randint(2, 20)
    total = unit * den
    ans = unit * num
    scaffold = sc.bar_model(str(total), [(str(unit), 1)] * den, note=f"Divide {total} into {den} equal parts, then take {num} of them.")
    return Question(f"What is {num}/{den} of {total}?", str(ans), numeric_check(ans), scaffold)


def ks_percentage_of_amount() -> Question:
    amount = random.choice([20, 40, 50, 60, 80, 100, 120, 150, 200, 240, 300])
    pct = random.choice([5, 10, 15, 20, 25, 30, 40, 50, 75, 10])
    ans = round(amount * pct / 100, 2)
    ten_pct = amount / 10
    scaffold = sc.hint_list([
        f"Find 10% of {amount} first: {amount} ÷ 10 = {ten_pct:g}",
        f"Scale that up (or halve it) to get {pct}%.",
    ])
    return Question(f"What is {pct}% of £{amount}?", f"£{_fmt(ans)}", numeric_check(ans, 0.5), scaffold)


KEY_SKILLS: dict[str, tuple[str, callable]] = {
    "KS1": ("Multiply whole numbers", ks_multiply_whole_numbers),
    "KS2": ("Divide whole numbers", ks_divide_whole_numbers),
    "KS3": ("Add whole numbers", ks_add_whole_numbers),
    "KS4": ("Subtract whole numbers", ks_subtract_whole_numbers),
    "KS5": ("Order of operations (easy)", ks_order_of_operations_easy),
    "KS6": ("Order of operations (harder)", ks_order_of_operations_harder),
    "KS7": ("Multiply decimal numbers", ks_multiply_decimal_numbers),
    "KS8": ("Divide decimal numbers", ks_divide_decimal_numbers),
    "KS9": ("Place value", ks_place_value),
    "KS10": ("Convert fractions, decimals and percentages", ks_convert_fdp),
    "KS11": ("Multiply by 10, 100 and 1000", ks_multiply_by_10_100_1000),
    "KS12": ("Divide by 10, 100 and 1000", ks_divide_by_10_100_1000),
    "KS13": ("Add decimal numbers", ks_add_decimal_numbers),
    "KS14": ("Subtract decimal numbers", ks_subtract_decimal_numbers),
    "KS15": ("Multiply negative numbers", ks_multiply_negative_numbers),
    "KS16": ("Divide negative numbers", ks_divide_negative_numbers),
    "KS17": ("Simplify fractions", ks_simplify_fractions),
    "KS18": ("Round to decimal places", ks_round_to_decimal_places),
    "KS19": ("Substitution", ks_substitution),
    "KS20": ("Simple directed number", ks_simple_directed_number),
    "KS21": ("Add a negative number", ks_add_negative_number),
    "KS22": ("Subtract a negative number", ks_subtract_negative_number),
    "KS24": ("Round to significant figures", ks_round_to_significant_figures),
    "KS25": ("Factors", ks_factors),
    "KS26": ("Multiples", ks_multiples),
    "KS28": ("Square numbers and square roots", ks_square_numbers_and_roots),
    "KS29": ("Cube numbers and cube roots", ks_cube_numbers_and_roots),
    "KS30": ("Equivalent fractions", ks_equivalent_fractions),
    "KS31": ("Fraction of an amount", ks_fraction_of_amount),
    "KS32": ("Percentage of an amount", ks_percentage_of_amount),
}


# --------------------------------------------------------------------------
# MENTAL STRATEGIES
# --------------------------------------------------------------------------

def _bond_question(target: int) -> Question:
    known = random.randint(0, target)
    other = target - known
    style = random.choice(["blank_result", "blank_first", "blank_second"])
    if style == "blank_result":
        prompt = f"{known} + {other} = ☐"
        ans = target
    elif style == "blank_first":
        prompt = f"☐ + {other} = {target}"
        ans = known
    else:
        prompt = f"{known} + ☐ = {target}"
        ans = other
    scaffold = sc.ten_frame_pair(known, target, note=f"Solid dots = the number you already have. Dashed dots = what's needed to reach {target}.")
    return Question(prompt, str(ans), numeric_check(ans), scaffold)


def ms_number_bonds_to_5() -> Question:
    return _bond_question(5)


def ms_number_bonds_to_10() -> Question:
    return _bond_question(10)


def ms_number_bonds_to_20() -> Question:
    known = random.randint(1, 19)
    other = 20 - known
    ans = other
    scaffold = sc.number_line(0, 20, jumps=[(known, 20, "+?", True)], circle=known)
    return Question(f"☐ + {known} = 20", str(ans), numeric_check(ans), scaffold)


def ms_number_bonds_to_100() -> Question:
    known = random.choice(range(1, 100, 1))
    ans = 100 - known
    scaffold = sc.number_line(0, 100, jumps=[(known, 100, "+?", True)], circle=known)
    return Question(f"{known} + ☐ = 100", str(ans), numeric_check(ans), scaffold)


def ms_double_single_digit() -> Question:
    n = random.randint(1, 5)
    ans = n * 2
    scaffold = sc.double_frame(n, note=f"Double means {n} + {n}.")
    style = random.choice(["double", "plus"])
    if style == "double":
        return Question(f"Double {n}", str(ans), numeric_check(ans), scaffold)
    return Question(f"{n} + {n} =", str(ans), numeric_check(ans), scaffold)


def ms_double_two_digit() -> Question:
    n = random.randint(11, 49)
    ans = n * 2
    scaffold = sc.double_dienes(n)
    style = random.choice(["double", "plus"])
    if style == "double":
        return Question(f"Double {n}", str(ans), numeric_check(ans), scaffold)
    return Question(f"{n} + {n} =", str(ans), numeric_check(ans), scaffold)


def ms_halve_single_digit() -> Question:
    n = random.choice([2, 4, 6, 8]) if random.random() < 0.7 else random.randint(1, 9)
    ans = n / 2
    scaffold = sc.halving_columns(n)
    style = random.choice(["halve", "div"])
    if style == "halve":
        return Question(f"Halve {n}", _fmt(ans), numeric_check(ans, 0.01), scaffold)
    return Question(f"{n} ÷ 2 =", _fmt(ans), numeric_check(ans, 0.01), scaffold)


def ms_halve_two_digit() -> Question:
    n = random.choice([n for n in range(20, 99) if n % 2 == 0]) if random.random() < 0.6 else random.randint(20, 99)
    ans = n / 2
    scaffold = sc.halving_dienes(n)
    style = random.choice(["halve", "div", "half_of"])
    if style == "halve":
        return Question(f"Halve {n}", _fmt(ans), numeric_check(ans, 0.01), scaffold)
    if style == "half_of":
        return Question(f"What is half of {n}?", _fmt(ans), numeric_check(ans, 0.01), scaffold)
    return Question(f"{n} ÷ 2", _fmt(ans), numeric_check(ans, 0.01), scaffold)


def ms_add_10() -> Question:
    n = random.randint(1, 90)
    ans = n + 10
    order = random.choice([f"10 + {n}", f"{n} + 10"])
    scaffold = sc.hundred_square(n, ans)
    return Question(order, str(ans), numeric_check(ans), scaffold)


def ms_subtract_10() -> Question:
    n = random.randint(20, 999)
    ans = n - 10
    scaffold = sc.hint_list(["Subtracting 10 only changes the tens digit — the units digit stays the same."])
    return Question(f"{n} − 10", str(ans), numeric_check(ans), scaffold)


def ms_add_multiples_of_10() -> Question:
    n = random.randint(1, 800)
    m = random.choice([10, 20, 30, 40, 50, 60, 70, 80, 90, 100]) * random.randint(1, 5)
    ans = n + m
    scaffold = sc.hint_list([f"Only the tens (and hundreds) change — add {m} to the tens part of {n}."])
    return Question(f"{n} + {m}", str(ans), numeric_check(ans), scaffold)


def ms_subtract_multiples_of_10() -> Question:
    m = random.choice([10, 20, 30, 40, 50, 60, 70, 80, 90]) * random.randint(1, 3)
    n = random.randint(m + 1, m + 500)
    ans = n - m
    scaffold = sc.hint_list([f"Only the tens (and hundreds) change — subtract {m} from the tens part of {n}."])
    return Question(f"{n} − {m}", str(ans), numeric_check(ans), scaffold)


def ms_how_many_to_multiple_of_10() -> Question:
    n = random.randint(1, 99)
    target = math.ceil((n + 1) / 10) * 10
    if target == n:
        target += 10
    ans = target - n
    scaffold = sc.number_line(max(0, n - 15), target + 5, jumps=[(n, target, "+?", True)], circle=target)
    return Question(f"{n} + ☐ = {target}", str(ans), numeric_check(ans), scaffold)


def ms_add_near_doubles() -> Question:
    a = random.randint(3, 49)
    diff = random.choice([-2, -1, 1, 2])
    b = a + diff
    ans = a + b
    near = a * 2
    scaffold = sc.hint_list([f"This is close to double {a} ({a} + {a} = {near}).", f"Adjust by {diff:+d} to compensate."])
    return Question(f"{a} + {b}", str(ans), numeric_check(ans), scaffold)


def ms_partition_single_digit() -> Question:
    total = random.randint(4, 9)
    part = random.randint(1, total - 1)
    ans = total - part
    scaffold = sc.ten_frame_pair(part, total, note=f"Solid dots show {part}; the dashed dots show what's needed to make {total}.")
    return Question(f"{total} = {part} + ☐", str(ans), numeric_check(ans), scaffold)


def ms_partition_two_digit() -> Question:
    style = random.choice(["tens", "near"])
    if style == "tens":
        tens = random.choice([20, 30, 40, 50, 60, 70, 80, 90])
        ones = random.randint(1, 9)
        total = tens + ones
        scaffold = sc.place_value_grid(f"{tens+ones}", ["T", "U"], highlight=1, note="Split into tens and units.")
        return Question(f"{total} = {tens} + ☐", str(ones), numeric_check(ones), scaffold)
    total = random.randint(11, 99)
    part = total - random.randint(1, 3)
    ans = total - part
    scaffold = sc.ten_frame_pair(min(part, 10), min(total, 10), note="Think about how close the part is to the whole.")
    return Question(f"{total} = {part} + ☐", str(ans), numeric_check(ans), scaffold)


def ms_add_bridge_10() -> Question:
    a = random.randint(4, 98)
    bridge = 10 - (a % 10)
    if bridge == 10:
        bridge = random.randint(1, 5)
    b = bridge + random.randint(1, 8)
    remainder = b - bridge
    landmark = a + bridge
    ans = remainder
    scaffold = sc.number_line(a - 5, landmark + b, jumps=[(a, landmark, f"+{bridge}", False), (landmark, landmark + remainder, "+?", True)], circle=landmark)
    return Question(f"{a} + {b} = {a} + {bridge} + ☐", str(ans), numeric_check(ans), scaffold)


def ms_subtract_bridge_10() -> Question:
    a = random.randint(20, 99)
    to_ten = a % 10
    if to_ten == 0:
        to_ten = random.randint(1, 9)
    b = to_ten + random.randint(1, 8)
    remainder = b - to_ten
    landmark = a - to_ten
    ans = remainder
    scaffold = sc.number_line(max(0, landmark - b), a + 5, jumps=[(a, landmark, f"-{to_ten}", False), (landmark, landmark - remainder, "-?", True)], circle=landmark)
    return Question(f"{a} − {b} = {a} − {to_ten} − ☐", str(ans), numeric_check(ans), scaffold)


def ms_count_smallest_to_largest() -> Question:
    small = random.randint(50, 990)
    diff = random.randint(1, 6)
    large = small + diff
    scaffold = sc.number_line(small - 2, large + 2, jumps=[(small, large, "+?", True)], circle=large)
    return Question(f"{large} − {small}", str(diff), numeric_check(diff), scaffold)


def ms_reorder_addition() -> Question:
    small = random.randint(2, 9)
    large = random.randint(100, 900)
    ans = small + large
    scaffold = sc.hint_list([f"It's easier to start with the bigger number: {large} + {small} instead of {small} + {large}."])
    return Question(f"{small} + {large}", str(ans), numeric_check(ans), scaffold)


def ms_multiplication_repeated_addition() -> Question:
    n = random.randint(2, 12)
    times = random.randint(2, 6)
    style = random.choice(["find_multiplier", "sum_form"])
    if style == "find_multiplier":
        total = n * times
        scaffold = sc.fact_list([f"{n} × {times} = {total}"], note="How many lots of the number make the total?")
        return Question(f"{total} = ☐ × {n}", str(times), numeric_check(times), scaffold)
    addition = " + ".join([str(n)] * times)
    ans = times
    scaffold = sc.hint_list([f"Count how many {n}s are being added."])
    return Question(f"{addition} = ☐ × {n}", str(ans), numeric_check(ans), scaffold)


def ms_division_inverse_multiplication() -> Question:
    a = random.randint(2, 12)
    b = random.randint(2, 12)
    product = a * b
    ans = b
    scaffold = sc.fact_list([f"{a} × {b} = {product}", f"So {product} ÷ {a} = ☐"], note="Division undoes multiplication.")
    return Question(f"{a} × {b} = {product}, so {product} ÷ {a} = ☐", str(ans), numeric_check(ans), scaffold)


def ms_equivalent_calc_addition() -> Question:
    a = random.randint(11, 89)
    b = random.randint(11, 89)
    a_round = (a // 10) * 10
    b_round = (b // 10) * 10
    a_rem = a - a_round
    b_rem = b - b_round
    ans = a_rem + b_rem
    scaffold = sc.hint_list([f"Round each number down to its tens: {a}→{a_round}, {b}→{b_round}.", "Add the leftover units back on at the end."])
    return Question(f"{a} + {b} = {a_round} + {b_round} + ☐", str(ans), numeric_check(ans), scaffold)


def ms_24_hour_clock() -> Question:
    h = random.randint(0, 23)
    m = random.choice([0, 5, 10, 15, 20, 30, 40, 45, 50])
    direction = random.choice(["to12", "to24"])
    if direction == "to12":
        suffix = "am" if h < 12 else "pm"
        h12 = h % 12
        if h12 == 0:
            h12 = 12
        ans = f"{h12}:{m:02d} {suffix}"
        scaffold = sc.clock_face(h, m, note="Subtract 12 from the hour if it's 13 or more, and use am/pm.")
        return Question(f"Write {h:02d}:{m:02d} in 12-hour clock format", ans, any_of_check([ans, ans.replace(" ", "")]), scaffold)
    h12 = random.randint(1, 12)
    suffix = random.choice(["am", "pm"])
    if suffix == "am":
        h24 = 0 if h12 == 12 else h12
    else:
        h24 = 12 if h12 == 12 else h12 + 12
    m2 = random.choice([0, 5, 10, 15, 20, 30, 40, 45, 50])
    ans = f"{h24:02d}:{m2:02d}"
    scaffold = sc.clock_face(h24, m2, note="Add 12 to the hour for pm times (except 12 pm itself).")
    return Question(f"Write {h12}:{m2:02d} {suffix} in 24-hour clock format", ans, any_of_check([ans]), scaffold)


def ms_minutes_to_past() -> Question:
    h1 = random.randint(0, 23)
    m1 = random.randint(0, 59)
    diff = random.randint(3, 45)
    total = h1 * 60 + m1 + diff
    h2 = (total // 60) % 24
    m2 = total % 60
    direction = random.choice(["after", "before"])
    if direction == "after":
        prompt = f"{h2:02d}:{m2:02d} is how many minutes after {h1:02d}:{m1:02d}?"
    else:
        prompt = f"{h1:02d}:{m1:02d} is how many minutes before {h2:02d}:{m2:02d}?"
    scaffold = sc.clock_face(h1, m1, note=f"Count on from {h1:02d}:{m1:02d} to {h2:02d}:{m2:02d}.")
    return Question(prompt, str(diff), numeric_check(diff), scaffold)


MENTAL_STRATEGIES: dict[str, tuple[str, callable]] = {
    "MS1": ("Number bonds to 5", ms_number_bonds_to_5),
    "MS2": ("Number bonds to 10", ms_number_bonds_to_10),
    "MS3": ("Number bonds to 20", ms_number_bonds_to_20),
    "MS4": ("Number bonds to 100", ms_number_bonds_to_100),
    "MS5": ("Doubling a single digit number", ms_double_single_digit),
    "MS6": ("Doubling a two digit number", ms_double_two_digit),
    "MS7": ("Halving a single digit number", ms_halve_single_digit),
    "MS8": ("Halving a two digit number", ms_halve_two_digit),
    "MS9": ("Adding 10 to a number", ms_add_10),
    "MS10": ("Subtracting 10 from a number", ms_subtract_10),
    "MS11": ("Adding multiples of 10 to a number", ms_add_multiples_of_10),
    "MS12": ("Subtracting multiples of 10 from a number", ms_subtract_multiples_of_10),
    "MS13": ("How many to a multiple of 10?", ms_how_many_to_multiple_of_10),
    "MS14": ("Add near doubles and compensate", ms_add_near_doubles),
    "MS15": ("Partitioning single digit numbers", ms_partition_single_digit),
    "MS16": ("Partitioning two digit numbers", ms_partition_two_digit),
    "MS17": ("Add using number bonds to bridge a multiple of 10", ms_add_bridge_10),
    "MS18": ("Subtract using number bonds to bridge a multiple of 10", ms_subtract_bridge_10),
    "MS19": ("Count from smallest to largest in a subtraction", ms_count_smallest_to_largest),
    "MS20": ("Reorder an addition", ms_reorder_addition),
    "MS21": ("Understand multiplication as repeated addition", ms_multiplication_repeated_addition),
    "MS22": ("Understand division as the inverse of multiplication", ms_division_inverse_multiplication),
    "MS23": ("Equivalent calculations to make an addition easier", ms_equivalent_calc_addition),
    "MS25": ("24 hour clock", ms_24_hour_clock),
    "MS26": ("How many minutes to/past a time?", ms_minutes_to_past),
}
