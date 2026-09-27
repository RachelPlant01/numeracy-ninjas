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


GD_ONES = ["", "aon", "dhà", "trì", "ceithir", "còig", "sia", "seachd", "ochd", "naoi",
           "deich", "aon-deug", "dà-dheug", "trì-deug", "ceithir-deug", "còig-deug",
           "sia-deug", "seachd-deug", "ochd-deug", "naoi-deug"]
GD_TENS = ["", "", "fichead", "trithead", "ceathrad", "caogad", "seasgad", "seachdad", "ochdad", "naochad"]
GD_HUNDRED_MULT = ["", "", "dà", "trì", "ceithir", "còig", "sia", "seachd", "ochd", "naoi"]


def _gd_three_digit_words(n: int) -> str:
    parts = []
    if n >= 100:
        h = n // 100
        parts.append("ceud" if h == 1 else f"{GD_HUNDRED_MULT[h]} cheud")
        n %= 100
        if n:
            parts.append("agus")
    if n >= 20:
        w = GD_TENS[n // 10]
        if n % 10:
            w += f" 's a {GD_ONES[n % 10]}"
        parts.append(w)
    elif n > 0:
        parts.append(GD_ONES[n])
    return " ".join(parts)


def gd_number_to_words(n: int) -> str:
    """Gaelic equivalent of number_to_words — a reasonable working version
    of the modern decimal counting system, not a definitive traditional
    rendering (lenition/plural noun forms after large multipliers are
    simplified)."""
    if n == 0:
        return "Neoni"
    groups = [("mhillean", 1_000_000), ("mìle", 1_000)]
    words = []
    remaining = n
    for name, size in groups:
        if remaining >= size:
            count = remaining // size
            if count == 1:
                words.append(f"aon {name}")
            elif count == 2:
                words.append(f"dà {name}")
            else:
                words.append(f"{_gd_three_digit_words(count)} {name}")
            remaining %= size
    if remaining:
        words.append(_gd_three_digit_words(remaining))
    return ", ".join(words).replace(" ,", ",")


def _fmt(n) -> str:
    if isinstance(n, float):
        if n == int(n):
            return str(int(n))
        return f"{n:g}"
    return str(n)


def _t(en: str, gd: str, lang: str) -> str:
    """Pick the English or Gàidhlig phrasing of a question/hint string."""
    return gd if lang == "gd" else en


# --------------------------------------------------------------------------
# KEY SKILLS
# --------------------------------------------------------------------------

def ks_multiply_whole_numbers(lang: str = "en") -> Question:
    a = random.randint(12, 950)
    b = random.randint(3, 90)
    ans = a * b
    demo_a, demo_b = (34, 56) if (a, b) != (34, 56) else (23, 14)
    scaffold = sc.lattice_multiplication(a, b, demo_a, demo_b)
    return Question(f"{a} × {b} =", str(ans), numeric_check(ans), scaffold)


def ks_divide_whole_numbers(lang: str = "en") -> Question:
    b = random.randint(3, 12)
    q = random.randint(20, 400)
    a = b * q
    demo_a, demo_b = (875, 7) if (a, b) != (875, 7) else (936, 8)
    scaffold = sc.division_bus_stop(a, b, demo_a, demo_b)
    return Question(f"{a} ÷ {b} =", str(q), numeric_check(q), scaffold)


def ks_add_whole_numbers(lang: str = "en") -> Question:
    a = random.randint(200, 9500)
    b = random.randint(200, 9500)
    ans = a + b
    demo_a, demo_b = (267, 485) if (a, b) != (267, 485) else (356, 476)
    scaffold = sc.column_addition(a, b, demo_a, demo_b)
    return Question(f"{a} + {b} =", str(ans), numeric_check(ans), scaffold)


def ks_subtract_whole_numbers(lang: str = "en") -> Question:
    a = random.randint(1000, 9800)
    b = random.randint(200, a - 100)
    ans = a - b
    demo_a, demo_b = (532, 178) if (a, b) != (532, 178) else (641, 275)
    scaffold = sc.column_subtraction(a, b, demo_a, demo_b)
    return Question(f"{a} - {b} =", str(ans), numeric_check(ans), scaffold)


def _rand_op_val(lo=2, hi=12):
    return random.randint(lo, hi)


def ks_order_of_operations_easy(lang: str = "en") -> Question:
    template = random.choice(["div_sub", "mul_add", "sub_mul"])
    if template == "div_sub":
        b = _rand_op_val(2, 9)
        q = _rand_op_val(2, 9)
        a = b * q
        c = _rand_op_val(1, 9)
        expr = f"{a} ÷ {b} - {c}"
        ans = a / b - c
        steps = [
            _t(f"Divide first: {a} ÷ {b} = {a // b}", f"Roinn an toiseach: {a} ÷ {b} = {a // b}", lang),
            _t(f"Then subtract: {a // b} - {c}", f"An uairsin thoir air falbh: {a // b} - {c}", lang),
        ]
    elif template == "mul_add":
        a = _rand_op_val(2, 9)
        b = _rand_op_val(2, 9)
        c = _rand_op_val(1, 20)
        expr = f"{a} × {b} + {c}"
        ans = a * b + c
        steps = [
            _t(f"Multiply first: {a} × {b} = {a*b}", f"Iomadaich an toiseach: {a} × {b} = {a*b}", lang),
            _t(f"Then add: {a*b} + {c}", f"An uairsin cuir ris: {a*b} + {c}", lang),
        ]
    else:
        a = _rand_op_val(10, 30)
        b = _rand_op_val(2, 9)
        c = _rand_op_val(2, 9)
        expr = f"{a} - {b} × {c}"
        ans = a - b * c
        steps = [
            _t(f"Multiply first: {b} × {c} = {b*c}", f"Iomadaich an toiseach: {b} × {c} = {b*c}", lang),
            _t(f"Then subtract: {a} - {b*c}", f"An uairsin thoir air falbh: {a} - {b*c}", lang),
        ]
    scaffold = sc.hint_list([_t("Remember: multiply/divide before you add/subtract.",
                                "Cuimhnich: iomadaich/roinn mus cuir thu ris no mus toir thu air falbh.", lang)] + steps)
    return Question(expr, _fmt(ans), numeric_check(ans), scaffold)


def ks_order_of_operations_harder(lang: str = "en") -> Question:
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
            _t("Brackets first.", "Camagan an toiseach.", lang),
            f"({a} - {b}) = {inner}",
            _t(f"Square it: {inner}² = {inner**2}", f"Ceàrnagaich e: {inner}² = {inner**2}", lang),
            _t(f"Multiply: {c} × {d} = {c*d}", f"Iomadaich: {c} × {d} = {c*d}", lang),
            _t(f"Add: {inner**2} + {c*d}", f"Cuir ris: {inner**2} + {c*d}", lang),
        ]
    else:
        expr = f"{a}² - {b} × {c}"
        ans = a ** 2 - b * c
        steps = [
            _t("Powers first.", "Cumhachdan an toiseach.", lang),
            f"{a}² = {a**2}",
            _t(f"Multiply: {b} × {c} = {b*c}", f"Iomadaich: {b} × {c} = {b*c}", lang),
            _t(f"Subtract: {a**2} - {b*c}", f"Thoir air falbh: {a**2} - {b*c}", lang),
        ]
    scaffold = sc.hint_list([_t("Order: Brackets, then Powers, then × ÷, then + −.",
                                "Òrdugh: Camagan, an uairsin Cumhachdan, an uairsin × ÷, an uairsin + −.", lang)] + steps)
    return Question(expr, _fmt(ans), numeric_check(ans), scaffold)


def ks_multiply_decimal_numbers(lang: str = "en") -> Question:
    a = round(random.uniform(1.1, 9.9), 1)
    b = random.randint(2, 12)
    ans = round(a * b, 2)
    scaffold = sc.hint_list([
        _t(f"Ignore the decimal point: work out {round(a*10)} × {b}.",
           f"Leig seachad am puing deicheach: obraich a-mach {round(a*10)} × {b}.", lang),
        _t("Now put the decimal point back — count 1 digit in from the right.",
           "A-nis cuir am puing deicheach air ais — cunnt 1 àireamh a-steach bhon taobh dheas.", lang),
    ])
    return Question(f"{a} × {b} =", _fmt(ans), numeric_check(ans), scaffold)


def ks_divide_decimal_numbers(lang: str = "en") -> Question:
    b = random.randint(2, 9)
    q = round(random.uniform(1.0, 20.0), 1)
    a = round(q * b, 2)
    scaffold = sc.hint_list([
        _t("Divide as if there were no decimal point, then place it in the answer directly above.",
           "Roinn mar nach robh puing deicheach ann, agus cuir e san fhreagairt dìreach os a chionn.", lang),
        f"{a} ÷ {b}",
    ])
    return Question(f"{a} ÷ {b} =", _fmt(round(a / b, 2)), numeric_check(a / b, 0.05), scaffold)


def ks_place_value(lang: str = "en") -> Question:
    n = random.randint(100000, 9_876_543)
    words = gd_number_to_words(n) if lang == "gd" else number_to_words(n)
    scaffold = sc.hint_list([
        _t("Break the words into groups: millions, thousands, then hundreds/tens/units.",
           "Roinn na faclan ann am buidhnean: milleanan, mìltean, an uairsin ceudan/deicheadan/aonadan.", lang),
        _t("Write each group's digits in order.", "Sgrìobh àireamhan gach buidheann san òrdugh cheart.", lang),
    ])
    return Question(_t(f"Write “{words}” in digits", f"Sgrìobh “{words}” ann an àireamhan", lang), str(n), numeric_check(n), scaffold)


def ks_convert_fdp(lang: str = "en") -> Question:
    template = random.choice(["pct_to_dec", "pct_to_frac", "dec_to_pct", "frac_to_pct"])
    if template == "pct_to_dec":
        p = random.randint(1, 99)
        ans = p / 100
        scaffold = sc.hint_list([
            _t(f"Divide {p} by 100.", f"Roinn {p} le 100.", lang),
            _t("Move the decimal point 2 places left.", "Gluais am puing deicheach 2 àite chun na clì.", lang),
        ])
        return Question(_t(f"{p}% as a decimal", f"{p}% mar dheicheach", lang), _fmt(ans), numeric_check(ans, 0.001), scaffold)
    if template == "pct_to_frac":
        p = random.choice([10, 20, 25, 40, 50, 60, 75, 80, 90])
        frac = Fraction(p, 100)
        scaffold = sc.hint_list([_t(f"Write {p}/100, then simplify by dividing top and bottom by the same number.",
                                     f"Sgrìobh {p}/100, an uairsin sìmplich le bhith a' roinn a' bhàrr 's a' bhun leis an aon àireamh.", lang)])
        return Question(_t(f"{p}% as a fraction in its simplest form", f"{p}% mar bhloigh san riochd as sìmplidh", lang),
                         f"{frac.numerator}/{frac.denominator}", fraction_check(frac), scaffold)
    if template == "dec_to_pct":
        d = round(random.uniform(0.02, 0.98), 2)
        ans = round(d * 100, 2)
        scaffold = sc.hint_list([
            _t(f"Multiply {d} by 100.", f"Iomadaich {d} le 100.", lang),
            _t("Move the decimal point 2 places right.", "Gluais am puing deicheach 2 àite chun na deis.", lang),
        ])
        return Question(f"{d} = ☐%", _fmt(ans), numeric_check(ans, 0.5), scaffold)
    num = random.randint(1, 4)
    den = random.choice([4, 5, 10, 20, 25])
    while num >= den:
        num = random.randint(1, den - 1)
    ans = round(100 * num / den, 1)
    scaffold = sc.hint_list([_t(f"Turn {num}/{den} into a fraction out of 100 first, or divide {num} by {den} and ×100.",
                                 f"Dèan {num}/{den} na bhloigh a-mach à 100 an toiseach, no roinn {num} le {den} agus ×100.", lang)])
    return Question(_t(f"{num}/{den} as a percentage", f"{num}/{den} mar cheudad", lang), _fmt(ans), numeric_check(ans, 0.5), scaffold)


def ks_multiply_by_10_100_1000(lang: str = "en") -> Question:
    mult = random.choice([10, 100, 1000])
    shift = {10: 1, 100: 2, 1000: 3}[mult]
    int_digits = random.randint(1, 5 - shift)
    dec_digits = random.randint(0, 2)
    int_part = [random.randint(1, 9)] + [random.randint(0, 9) for _ in range(int_digits - 1)]
    dec_part = [random.randint(0, 9) for _ in range(dec_digits)]
    n_str = "".join(map(str, int_part)) + ("." + "".join(map(str, dec_part)) if dec_part else "")
    n = float(n_str)
    ans = round(n * mult, 3)
    scaffold = sc.place_value_shift(int_part, dec_part, shift, direction="left")
    return Question(f"{_fmt(n)} × {mult} =", _fmt(ans), numeric_check(ans, 0.001), scaffold)


def ks_divide_by_10_100_1000(lang: str = "en") -> Question:
    div = random.choice([10, 100, 1000])
    shift = {10: 1, 100: 2, 1000: 3}[div]
    dec_digits = random.randint(0, 3 - shift)
    int_digits = random.randint(1, 3)
    int_part = [random.randint(1, 9)] + [random.randint(0, 9) for _ in range(int_digits - 1)]
    dec_part = [random.randint(0, 9) for _ in range(dec_digits)]
    n_str = "".join(map(str, int_part)) + ("." + "".join(map(str, dec_part)) if dec_part else "")
    n = float(n_str)
    ans = round(n / div, 3)
    scaffold = sc.place_value_shift(int_part, dec_part, shift, direction="right")
    return Question(f"{_fmt(n)} ÷ {div} =", _fmt(ans), numeric_check(ans, 0.001), scaffold)


def ks_add_decimal_numbers(lang: str = "en") -> Question:
    a = round(random.uniform(1, 90), 2)
    b = round(random.uniform(1, 90), 2)
    ans = round(a + b, 2)
    demo_a, demo_b = (4.65, 3.78) if (a, b) != (4.65, 3.78) else (5.46, 2.87)
    scaffold = sc.column_addition(round(a * 100), round(b * 100), round(demo_a * 100), round(demo_b * 100), decimals=2)
    return Question(f"{_fmt(a)} + {_fmt(b)}", _fmt(ans), numeric_check(ans, 0.01), scaffold)


def ks_subtract_decimal_numbers(lang: str = "en") -> Question:
    a = round(random.uniform(10, 99), 2)
    b = round(random.uniform(1, a - 1), 2)
    ans = round(a - b, 2)
    demo_a, demo_b = (5.32, 1.78) if (a, b) != (5.32, 1.78) else (6.41, 2.75)
    scaffold = sc.column_subtraction(round(a * 100), round(b * 100), round(demo_a * 100), round(demo_b * 100), decimals=2)
    return Question(f"{_fmt(a)} - {_fmt(b)}", _fmt(ans), numeric_check(ans, 0.01), scaffold)


def ks_multiply_negative_numbers(lang: str = "en") -> Question:
    a = random.randint(2, 12)
    b = random.randint(2, 12)
    signs = random.choice([(1, -1), (-1, 1), (-1, -1)])
    x, y = a * signs[0], b * signs[1]
    ans = x * y
    demo_a, demo_b = (4, 5) if (a, b) != (4, 5) else (6, 7)
    scaffold = sc.negative_sign_scaffold("×", signs[0], signs[1], demo_a, demo_b, lang=lang)
    return Question(f"{x} × ({y})" if y < 0 else f"{x} × {y}", str(ans), numeric_check(ans), scaffold)


def ks_divide_negative_numbers(lang: str = "en") -> Question:
    b = random.randint(2, 12)
    q = random.randint(2, 12)
    signs = random.choice([(1, -1), (-1, 1), (-1, -1)])
    a = (b * q) * signs[0]
    d = b * signs[1]
    ans = a / d
    demo_b, demo_q = (4, 3) if (b, q) != (4, 3) else (6, 5)
    scaffold = sc.negative_sign_scaffold("÷", signs[0], signs[1], demo_b * demo_q, demo_b, lang=lang)
    a_str = f"({a})" if a < 0 else f"{a}"
    d_str = f"({d})" if d < 0 else f"{d}"
    return Question(f"{a_str} ÷ {d_str}", str(int(ans)), numeric_check(ans), scaffold)


def ks_simplify_fractions(lang: str = "en") -> Question:
    g = random.randint(2, 9)
    num = random.randint(1, 9)
    den = random.randint(num + 1, 12)
    while math.gcd(num, den) != 1:
        num = random.randint(1, 9)
        den = random.randint(num + 1, 12)
    n2, d2 = num * g, den * g
    simplest = Fraction(n2, d2)

    # The scaffold works the actual question through to its simplified
    # form. A wall/circle pair of "before" and "after" only stays readable
    # up to about a dozen segments, so above that we switch to the
    # single ÷HCF arrow instead of a finely-sliced wall or pie.
    if d2 > 12:
        scaffold = sc.fraction_simplify_single_arrow(n2, d2)
    else:
        kind = random.choice(["wall", "circles"])
        if kind == "wall":
            scaffold = sc.fraction_wall_two_rows(n2, d2, simplest.numerator, simplest.denominator)
        else:
            scaffold = sc.fraction_circles_pair(n2, d2, simplest.numerator, simplest.denominator)

    prompt = _t(f"Write {sc.fraction_html(n2, d2)} in its simplest form",
                f"Sgrìobh {sc.fraction_html(n2, d2)} san riochd as sìmplidh", lang)
    return Question(prompt, f"{simplest.numerator}/{simplest.denominator}", fraction_check(simplest), scaffold)


def ks_round_to_decimal_places(lang: str = "en") -> Question:
    dp_source = round(random.uniform(1, 99), 4)
    dp = random.randint(1, 3)
    ans = round(dp_source, dp)
    scaffold = sc.hint_list([
        _t(f"Look at the digit after the {dp} decimal place you're rounding to.",
           f"Seall air an fhigear às dèidh an {dp} àite dheicheach a tha thu a' cuairteachadh gu ruige.", lang),
        _t("5 or more → round up. Less than 5 → stays the same.",
           "5 no barrachd → cuairtich suas. Nas lugha na 5 → fuirich mar a tha e.", lang),
    ])
    prompt = _t(f"Round {dp_source} to {dp} decimal place{'s' if dp > 1 else ''}",
                f"Cuairtich {dp_source} gu {dp} àite dheicheach", lang)
    return Question(prompt, _fmt(ans), numeric_check(ans, 10 ** (-dp) / 2), scaffold)


def ks_substitution(lang: str = "en") -> Question:
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
    prompt = _t(f"If a = {a_v}, b = {b_v}, c = {c_v}, what is the value of {expr}?",
                f"Ma tha a = {a_v}, b = {b_v}, c = {c_v}, dè an luach a th' aig {expr}?", lang)
    return Question(prompt, str(ans), numeric_check(ans), scaffold)


def ks_simple_directed_number(lang: str = "en") -> Question:
    a = random.randint(-12, 12)
    b = random.randint(1, 12)
    op = random.choice(["+", "-"])
    ans = a + b if op == "+" else a - b
    a_str = f"({a})" if a < 0 else str(a)
    scaffold = sc.number_line(-15, 15, jumps=[(a, ans, ("+" if op == "+" else "-") + str(b), True)], circle=a, hide_value=ans)
    return Question(f"{a_str} {op} {b}", str(ans), numeric_check(ans), scaffold)


def ks_add_negative_number(lang: str = "en") -> Question:
    a = random.randint(-15, 15)
    b = random.randint(1, 15)
    ans = a + (-b)
    scaffold = sc.number_line(-20, 20, jumps=[(a, ans, f"-{b}", True)], circle=a, hide_value=ans)
    return Question(f"{a} + ({-b})", str(ans), numeric_check(ans), scaffold)


def ks_subtract_negative_number(lang: str = "en") -> Question:
    a = random.randint(-15, 15)
    b = random.randint(1, 15)
    ans = a - (-b)
    scaffold = sc.number_line(-20, 20, jumps=[(a, ans, f"+{b}", True)], circle=a, hide_value=ans)
    return Question(f"{a} - ({-b})", str(ans), numeric_check(ans), scaffold)


def ks_round_to_significant_figures(lang: str = "en") -> Question:
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
        _t("Count significant figures from the first non-zero digit.",
           "Cunnt na figearan brìoghmhor bhon chiad fhigear nach eil na neoni.", lang),
        _t(f"Keep the first {sf}, then round the next digit.",
           f"Cùm a' chiad {sf}, an uairsin cuairtich an ath fhigear.", lang),
    ])
    prompt = _t(f"Round {n} to {sf} significant figure{'s' if sf > 1 else ''}",
                f"Cuairtich {n} gu {sf} figear brìoghmhor", lang)
    return Question(prompt, _fmt(ans), numeric_check(ans, abs(ans) * 0.02 + 1e-9), scaffold)


def ks_factors(lang: str = "en") -> Question:
    n = random.choice([12, 18, 20, 24, 30, 36, 40, 45, 48, 60])
    candidate = random.randint(2, n // 2 + 1)
    is_factor = n % candidate == 0
    scaffold = sc.hint_list([_t(f"Does {candidate} divide exactly into {n} with no remainder?",
                                 f"A bheil {candidate} a' roinn gu pongail a-steach do {n} gun fhuidheall?", lang)])
    prompt = _t(f"Is {candidate} a factor of {n}?", f"A bheil {candidate} na fhactar de {n}?", lang)
    ans_display = _t("Yes" if is_factor else "No", "Tha" if is_factor else "Chan eil", lang)
    return Question(prompt, ans_display, yes_no_check(is_factor), scaffold)


def ks_multiples(lang: str = "en") -> Question:
    n = random.randint(3, 12)
    count = 4
    ans_list = [n * i for i in range(1, count + 1)]
    scaffold = sc.hint_list([
        _t(f"Multiples of {n}: keep adding {n} each time.", f"Iomadan de {n}: cùm a' cur {n} ris gach turas.", lang),
        f"{n}, {n*2}, …",
    ])
    prompt = _t(f"List the first {count} multiples of {n}", f"Sgrìobh a' chiad {count} iomadan de {n}", lang)
    return Question(prompt, ", ".join(map(str, ans_list)), list_check(ans_list), scaffold)


def ks_square_numbers_and_roots(lang: str = "en") -> Question:
    n = random.randint(2, 15)
    if random.random() < 0.5:
        ans = n * n
        scaffold = sc.hint_list([_t(f"{n}² means {n} × {n}.", f"Tha {n}² a' ciallachadh {n} × {n}.", lang)])
        return Question(_t(f"What is {n}²?", f"Dè a th' ann an {n}²?", lang), str(ans), numeric_check(ans), scaffold)
    ans = n
    scaffold = sc.hint_list([_t(f"Which number multiplied by itself gives {n*n}?",
                                 f"Dè an àireamh a bheir {n*n}, ma dh'iomadaicheas tu i le fhèin?", lang)])
    prompt = _t(f"What is the positive value of √{n*n}?", f"Dè an luach dearbhach a th' aig √{n*n}?", lang)
    return Question(prompt, str(ans), numeric_check(ans), scaffold)


def ks_cube_numbers_and_roots(lang: str = "en") -> Question:
    n = random.randint(2, 10)
    if random.random() < 0.5:
        ans = n ** 3
        scaffold = sc.hint_list([_t(f"{n}³ means {n} × {n} × {n}.", f"Tha {n}³ a' ciallachadh {n} × {n} × {n}.", lang)])
        return Question(_t(f"What is {n}³?", f"Dè a th' ann an {n}³?", lang), str(ans), numeric_check(ans), scaffold)
    ans = n
    scaffold = sc.hint_list([_t(f"Which number, cubed, gives {n**3}?",
                                 f"Dè an àireamh, air a ciùbadh, a bheir {n**3}?", lang)])
    prompt = _t(f"What is the value of ∛{n**3}?", f"Dè an luach a th' aig ∛{n**3}?", lang)
    return Question(prompt, str(ans), numeric_check(ans), scaffold)


def ks_equivalent_fractions(lang: str = "en") -> Question:
    num = random.randint(1, 6)
    den = random.randint(num + 1, 9)
    while math.gcd(num, den) != 1:
        num = random.randint(1, 6)
        den = random.randint(num + 1, 9)
    scale = random.randint(2, 6)
    missing_side = random.choice(["den", "num"])

    # The question's own known fraction (num/den) is shown as a real bar,
    # paired with a worked example of the method using different numbers
    # — so the picture always relates to the actual question without ever
    # giving away the missing value.
    kind = random.choice(["wall", "circles", "arrows"])
    scaffold = sc.fraction_equivalent_scaffold(num, den, kind)

    if missing_side == "den":
        prompt = sc.fraction_equation_html(num, den, num * scale, "☐")
        ans = den * scale
    else:
        prompt = sc.fraction_equation_html(num, den, "☐", den * scale)
        ans = num * scale
    return Question(prompt, str(ans), numeric_check(ans), scaffold)


def ks_fraction_of_amount(lang: str = "en") -> Question:
    den = random.randint(2, 10)
    num = random.randint(1, den - 1)
    unit = random.randint(2, 20)
    total = unit * den
    ans = unit * num
    scaffold = sc.bar_model(str(total), [("", 1)] * den, single_color="#a3c9f9")
    prompt = _t(f"What is {num}/{den} of {total}?", f"Dè a th' ann an {num}/{den} de {total}?", lang)
    return Question(prompt, str(ans), numeric_check(ans), scaffold)


def ks_percentage_of_amount(lang: str = "en") -> Question:
    amount = random.choice([20, 40, 50, 60, 80, 100, 120, 150, 200, 240, 300])
    pct = random.choice([5, 10, 15, 20, 25, 30, 40, 50, 75, 10])
    ans = round(amount * pct / 100, 2)
    ten_pct = amount / 10
    scaffold = sc.hint_list([
        _t(f"Find 10% of {amount} first: {amount} ÷ 10 = {ten_pct:g}",
           f"Lorg 10% de {amount} an toiseach: {amount} ÷ 10 = {ten_pct:g}", lang),
        _t(f"Scale that up (or halve it) to get {pct}%.",
           f"Sgèilich sin suas (no gabh leth dheth) gus {pct}% fhaighinn.", lang),
    ])
    prompt = _t(f"What is {pct}% of £{amount}?", f"Dè a th' ann an {pct}% de £{amount}?", lang)
    return Question(prompt, f"£{_fmt(ans)}", numeric_check(ans, 0.5), scaffold)


KEY_SKILLS: dict[str, dict] = {
    "KS1": {"en": "Multiply whole numbers", "gd": "Iomadaich àireamhan slàna", "fn": ks_multiply_whole_numbers},
    "KS2": {"en": "Divide whole numbers", "gd": "Roinn àireamhan slàna", "fn": ks_divide_whole_numbers},
    "KS3": {"en": "Add whole numbers", "gd": "Cuir àireamhan slàna ris a chèile", "fn": ks_add_whole_numbers},
    "KS4": {"en": "Subtract whole numbers", "gd": "Thoir àireamhan slàna air falbh", "fn": ks_subtract_whole_numbers},
    "KS5": {"en": "Order of operations (easy)", "gd": "Òrdugh obrachaidh (furasta)", "fn": ks_order_of_operations_easy},
    "KS6": {"en": "Order of operations (harder)", "gd": "Òrdugh obrachaidh (nas duilghe)", "fn": ks_order_of_operations_harder},
    "KS7": {"en": "Multiply decimal numbers", "gd": "Iomadaich àireamhan deicheach", "fn": ks_multiply_decimal_numbers},
    "KS8": {"en": "Divide decimal numbers", "gd": "Roinn àireamhan deicheach", "fn": ks_divide_decimal_numbers},
    "KS9": {"en": "Place value", "gd": "Luach ionaid", "fn": ks_place_value},
    "KS10": {"en": "Convert fractions, decimals and percentages", "gd": "Iompaich bloighean, àireamhan deicheach agus ceudadan", "fn": ks_convert_fdp},
    "KS11": {"en": "Multiply by 10, 100 and 1000", "gd": "Iomadaich le 10, 100 agus 1000", "fn": ks_multiply_by_10_100_1000},
    "KS12": {"en": "Divide by 10, 100 and 1000", "gd": "Roinn le 10, 100 agus 1000", "fn": ks_divide_by_10_100_1000},
    "KS13": {"en": "Add decimal numbers", "gd": "Cuir àireamhan deicheach ris a chèile", "fn": ks_add_decimal_numbers},
    "KS14": {"en": "Subtract decimal numbers", "gd": "Thoir àireamhan deicheach air falbh", "fn": ks_subtract_decimal_numbers},
    "KS15": {"en": "Multiply negative numbers", "gd": "Iomadaich àireamhan àicheil", "fn": ks_multiply_negative_numbers},
    "KS16": {"en": "Divide negative numbers", "gd": "Roinn àireamhan àicheil", "fn": ks_divide_negative_numbers},
    "KS17": {"en": "Simplify fractions", "gd": "Sìmplich bloighean", "fn": ks_simplify_fractions},
    "KS18": {"en": "Round to decimal places", "gd": "Cuairtich gu àitean deicheach", "fn": ks_round_to_decimal_places},
    "KS19": {"en": "Substitution", "gd": "Cur an àite", "fn": ks_substitution},
    "KS20": {"en": "Simple directed number", "gd": "Àireamh stiùirichte shìmplidh", "fn": ks_simple_directed_number},
    "KS21": {"en": "Add a negative number", "gd": "Cuir àireamh àicheil ris", "fn": ks_add_negative_number},
    "KS22": {"en": "Subtract a negative number", "gd": "Thoir àireamh àicheil air falbh", "fn": ks_subtract_negative_number},
    "KS24": {"en": "Round to significant figures", "gd": "Cuairtich gu figearan brìoghmhor", "fn": ks_round_to_significant_figures},
    "KS25": {"en": "Factors", "gd": "Factaran", "fn": ks_factors},
    "KS26": {"en": "Multiples", "gd": "Iomadan", "fn": ks_multiples},
    "KS28": {"en": "Square numbers and square roots", "gd": "Àireamhan ceàrnagach agus freumhan ceàrnagach", "fn": ks_square_numbers_and_roots},
    "KS29": {"en": "Cube numbers and cube roots", "gd": "Àireamhan ciùbach agus freumhan ciùbach", "fn": ks_cube_numbers_and_roots},
    "KS30": {"en": "Equivalent fractions", "gd": "Bloighean co-ionann", "fn": ks_equivalent_fractions},
    "KS31": {"en": "Fraction of an amount", "gd": "Bloigh de dh'uiread", "fn": ks_fraction_of_amount},
    "KS32": {"en": "Percentage of an amount", "gd": "Ceudad de dh'uiread", "fn": ks_percentage_of_amount},
}


# --------------------------------------------------------------------------
# MENTAL STRATEGIES
# --------------------------------------------------------------------------

def _bond_question(target: int, lang: str = "en") -> Question:
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


def _bond_question_mixed(target: int, lang: str = "en") -> Question:
    a = random.randint(0, target)
    b = target - a
    style = random.choice(["sum", "first", "second"])
    if style == "sum":
        prompt = f"{a} + {b} = ☐"
        ans = target
        given, gap = a, b
    elif style == "first":
        prompt = f"☐ + {b} = {target}"
        ans = a
        given, gap = b, a
    else:
        prompt = f"{a} + ☐ = {target}"
        ans = b
        given, gap = a, b

    kind = random.choice(["numicon", "number_line", "ten_frame", "dienes"])
    if kind == "numicon":
        scaffold = sc.numicon_bond(given, gap)
    elif kind == "number_line":
        scaffold = sc.number_line(0, target + 2, jumps=[(given, target, "+?", True)], circle=given)
    elif kind == "ten_frame":
        scaffold = sc.ten_frame_pair(given, target)
    else:
        scaffold = sc.dienes_partition_near(given, gap)
    return Question(prompt, str(ans), numeric_check(ans), scaffold)


def ms_number_bonds_to_5(lang: str = "en") -> Question:
    return _bond_question(5, lang)


def ms_number_bonds_to_10(lang: str = "en") -> Question:
    return _bond_question(10, lang)


def ms_number_bonds_within_10(lang: str = "en") -> Question:
    return _bond_question_mixed(random.choice([6, 7, 8, 9]), lang)


def ms_number_bonds_to_20(lang: str = "en") -> Question:
    known = random.randint(1, 19)
    other = 20 - known
    ans = other
    scaffold = sc.number_line(0, 20, jumps=[(known, 20, "+?", True)], circle=known)
    return Question(f"☐ + {known} = 20", str(ans), numeric_check(ans), scaffold)


def ms_number_bonds_to_100(lang: str = "en") -> Question:
    known = random.choice(range(1, 100, 1))
    ans = 100 - known
    scaffold = sc.dienes_bonds_to_100(known)
    return Question(f"{known} + ☐ = 100", str(ans), numeric_check(ans), scaffold)


def ms_double_single_digit(lang: str = "en") -> Question:
    n = random.randint(1, 5)
    ans = n * 2
    scaffold = sc.double_frame(n, note=f"Double means {n} + {n}.")
    style = random.choice(["double", "plus"])
    if style == "double":
        return Question(_t(f"Double {n}", f"Dùblaich {n}", lang), str(ans), numeric_check(ans), scaffold)
    return Question(f"{n} + {n} =", str(ans), numeric_check(ans), scaffold)


def ms_double_two_digit(lang: str = "en") -> Question:
    n = random.randint(11, 49)
    ans = n * 2
    scaffold = sc.double_dienes(n)
    style = random.choice(["double", "plus"])
    if style == "double":
        return Question(_t(f"Double {n}", f"Dùblaich {n}", lang), str(ans), numeric_check(ans), scaffold)
    return Question(f"{n} + {n} =", str(ans), numeric_check(ans), scaffold)


def ms_halve_single_digit(lang: str = "en") -> Question:
    n = random.choice([2, 4, 6, 8]) if random.random() < 0.7 else random.randint(1, 9)
    ans = n / 2
    scaffold = sc.halving_columns(n)
    style = random.choice(["halve", "div"])
    if style == "halve":
        return Question(_t(f"Halve {n}", f"Gabh leth de {n}", lang), _fmt(ans), numeric_check(ans, 0.01), scaffold)
    return Question(f"{n} ÷ 2 =", _fmt(ans), numeric_check(ans, 0.01), scaffold)


def ms_halve_two_digit(lang: str = "en") -> Question:
    n = random.choice([n for n in range(20, 99) if n % 2 == 0]) if random.random() < 0.6 else random.randint(20, 99)
    ans = n / 2
    scaffold = sc.halving_dienes(n)
    style = random.choice(["halve", "div", "half_of"])
    if style == "halve":
        return Question(_t(f"Halve {n}", f"Gabh leth de {n}", lang), _fmt(ans), numeric_check(ans, 0.01), scaffold)
    if style == "half_of":
        return Question(_t(f"What is half of {n}?", f"Dè a th' ann an leth {n}?", lang), _fmt(ans), numeric_check(ans, 0.01), scaffold)
    return Question(f"{n} ÷ 2", _fmt(ans), numeric_check(ans, 0.01), scaffold)


def ms_add_10(lang: str = "en") -> Question:
    n = random.randint(1, 90)
    ans = n + 10
    order = random.choice([f"10 + {n}", f"{n} + 10"])
    scaffold = sc.hundred_square(n, ans)
    return Question(order, str(ans), numeric_check(ans), scaffold)


def ms_subtract_10(lang: str = "en") -> Question:
    n = random.randint(11, 100)
    ans = n - 10
    scaffold = sc.hundred_square(n, ans)
    return Question(f"{n} − 10", str(ans), numeric_check(ans), scaffold)


def ms_add_9(lang: str = "en") -> Question:
    n = random.randint(4, 95)
    ans = n + 9
    scaffold = sc.number_line(
        n - 2, n + 11,
        jumps=[(n, n + 10, "+10", False), (n + 10, ans, "-1", False)],
        circle=n, hide_value=ans,
    )
    order = random.choice([f"{n} + 9", f"9 + {n}"])
    return Question(order, str(ans), numeric_check(ans), scaffold)


def ms_add_within_20_bridge_10(lang: str = "en") -> Question:
    while True:
        a = random.randint(2, 9)
        b = random.randint(2, 9)
        if a + b > 10:
            break
    ans = a + b
    scaffold = sc.bridge_ten_frames(a, b)
    order = random.choice([f"{a} + {b}", f"{b} + {a}"])
    return Question(order, str(ans), numeric_check(ans), scaffold)


def ms_add_multiples_of_10(lang: str = "en") -> Question:
    n = random.randint(1, 150)
    m = random.choice([10, 20, 30, 40, 50, 60, 70, 80, 90])
    ans = n + m
    scaffold = sc.dienes_add_tens(n, m)
    return Question(f"{n} + {m}", str(ans), numeric_check(ans), scaffold)


def ms_subtract_multiples_of_10(lang: str = "en") -> Question:
    hundreds = random.choice([0, 0, 0, 1])
    tens_digit = random.randint(1, 9)
    ones = random.randint(0, 9)
    n = hundreds * 100 + tens_digit * 10 + ones
    m = random.randint(1, tens_digit) * 10
    ans = n - m
    scaffold = sc.dienes_subtract_tens(n, m)
    return Question(f"{n} − {m}", str(ans), numeric_check(ans), scaffold)


def ms_how_many_to_multiple_of_10(lang: str = "en") -> Question:
    n = random.randint(1, 99)
    target = math.ceil((n + 1) / 10) * 10
    if target == n:
        target += 10
    ans = target - n
    scaffold = sc.number_line(max(0, n - 15), target + 5, jumps=[(n, target, "+?", True)], circle=target)
    return Question(f"{n} + ☐ = {target}", str(ans), numeric_check(ans), scaffold)


def ms_add_near_doubles(lang: str = "en") -> Question:
    a = random.randint(3, 49)
    diff = random.choice([-2, -1, 1, 2])
    b = a + diff
    ans = a + b
    lo, hi = min(a, b), max(a, b)
    scaffold = sc.near_doubles_dienes(lo, hi - lo)
    return Question(f"{a} + {b}", str(ans), numeric_check(ans), scaffold)


def ms_partition_single_digit(lang: str = "en") -> Question:
    total = random.randint(4, 9)
    part = random.randint(1, total - 1)
    ans = total - part
    scaffold = sc.ten_frame_pair(part, total, note=f"Solid dots show {part}; the dashed dots show what's needed to make {total}.")
    return Question(f"{total} = {part} + ☐", str(ans), numeric_check(ans), scaffold)


def ms_partition_two_digit(lang: str = "en") -> Question:
    style = random.choice(["tens", "near"])
    if style == "tens":
        tens = random.choice([10, 20, 30, 40, 50, 60, 70, 80, 90])
        ones = random.randint(1, 9)
        total = tens + ones
        kinds = ["number_line", "dienes"]
        if total <= 50:
            kinds.append("ten_frames")
        kind = random.choice(kinds)
        if kind == "number_line":
            scaffold = sc.number_line(0, total + 5, jumps=[(tens, total, "+?", True)], circle=tens)
        elif kind == "dienes":
            scaffold = sc.dienes_partition_tens(tens, ones)
        else:
            scaffold = sc.ten_frames_multi(tens, total)
        return Question(f"{total} = {tens} + ☐", str(ones), numeric_check(ones), scaffold)

    total = random.randint(11, 99)
    part = total - random.randint(1, 3)
    ans = total - part
    kind = random.choice(["number_line", "dienes"])
    if kind == "number_line":
        scaffold = sc.number_line(max(0, part - 3), total + 3, jumps=[(part, total, "+?", True)], circle=total)
    else:
        scaffold = sc.dienes_partition_near(part, ans)
    return Question(f"{total} = {part} + ☐", str(ans), numeric_check(ans), scaffold)


def ms_add_bridge_10(lang: str = "en") -> Question:
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


def ms_subtract_bridge_10(lang: str = "en") -> Question:
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


def ms_count_smallest_to_largest(lang: str = "en") -> Question:
    small = random.randint(50, 990)
    diff = random.randint(1, 6)
    large = small + diff
    scaffold = sc.number_line(small - 2, large + 2, jumps=[(small, large, "+?", True)], circle=large)
    return Question(f"{large} − {small}", str(diff), numeric_check(diff), scaffold)


def ms_reorder_addition(lang: str = "en") -> Question:
    small = random.randint(2, 9)
    large = random.randint(100, 900)
    ans = small + large
    scaffold = sc.number_line(
        large - 2, large + small + 2,
        jumps=[(large, ans, f"+{small}", False)],
        circle=large, hide_value=ans,
    )
    return Question(f"{small} + {large}", str(ans), numeric_check(ans), scaffold)


def ms_multiplication_repeated_addition(lang: str = "en") -> Question:
    n = random.randint(2, 9)
    times = random.randint(2, 6)
    addition = " + ".join([str(n)] * times)
    ans = times
    scaffold = sc.repeated_groups(n, times)
    return Question(f"{addition} = ☐ × {n}", str(ans), numeric_check(ans), scaffold)


def ms_division_inverse_multiplication(lang: str = "en") -> Question:
    a = random.randint(2, 6)
    b = random.randint(2, 9)
    product = a * b
    ans = b
    scaffold = sc.repeated_groups(b, a)
    prompt = _t(f"{a} × {b} = {product}, so {product} ÷ {a} = ☐",
                f"{a} × {b} = {product}, mar sin {product} ÷ {a} = ☐", lang)
    return Question(prompt, str(ans), numeric_check(ans), scaffold)


def ms_equivalent_calc_addition(lang: str = "en") -> Question:
    a = random.randint(11, 89)
    b = random.randint(11, 89)
    a_round = (a // 10) * 10
    b_round = (b // 10) * 10
    a_rem = a - a_round
    b_rem = b - b_round
    total = a + b
    kind = random.choice(["dienes", "number_line", "bar_model"])
    if kind == "number_line":
        # Keep the first number whole here (rather than also rounding it
        # down) so the line starts on the same number the equation does.
        ans = b_rem
        scaffold = sc.number_line(
            a - 2, total + 3,
            jumps=[(a, a + b_round, f"+{b_round}", False), (a + b_round, total, "+?", True)],
            circle=a, hide_value=total,
        )
        return Question(f"{a} + {b} = {a} + {b_round} + ☐", str(ans), numeric_check(ans), scaffold)
    ans = a_rem + b_rem
    if kind == "dienes":
        scaffold = sc.dienes_partition_pair(a_round, a_rem, b_round, b_rem)
    else:
        scaffold = sc.bar_model(f"{a} + {b}", [(str(a_round), a_round), (str(b_round), b_round), ("?", max(ans, 1))])
    return Question(f"{a} + {b} = {a_round} + {b_round} + ☐", str(ans), numeric_check(ans), scaffold)


def ms_24_hour_clock(lang: str = "en") -> Question:
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
        prompt = _t(f"Write {h:02d}:{m:02d} in 12-hour clock format",
                    f"Sgrìobh {h:02d}:{m:02d} ann an cruth uaireadair 12-uair", lang)
        return Question(prompt, ans, any_of_check([ans, ans.replace(" ", "")]), scaffold)
    h12 = random.randint(1, 12)
    suffix = random.choice(["am", "pm"])
    if suffix == "am":
        h24 = 0 if h12 == 12 else h12
    else:
        h24 = 12 if h12 == 12 else h12 + 12
    m2 = random.choice([0, 5, 10, 15, 20, 30, 40, 45, 50])
    ans = f"{h24:02d}:{m2:02d}"
    scaffold = sc.clock_face(h24, m2, note="Add 12 to the hour for pm times (except 12 pm itself).")
    prompt = _t(f"Write {h12}:{m2:02d} {suffix} in 24-hour clock format",
                f"Sgrìobh {h12}:{m2:02d} {suffix} ann an cruth uaireadair 24-uair", lang)
    return Question(prompt, ans, any_of_check([ans]), scaffold)


def ms_minutes_to_past(lang: str = "en") -> Question:
    h1 = random.randint(0, 23)
    m1 = random.randint(0, 59)
    diff = random.randint(3, 45)
    total = h1 * 60 + m1 + diff
    h2 = (total // 60) % 24
    m2 = total % 60
    direction = random.choice(["after", "before"])
    if direction == "after":
        prompt = _t(f"{h2:02d}:{m2:02d} is how many minutes after {h1:02d}:{m1:02d}?",
                     f"Cia mheud mionaid an dèidh {h1:02d}:{m1:02d} a tha {h2:02d}:{m2:02d}?", lang)
    else:
        prompt = _t(f"{h1:02d}:{m1:02d} is how many minutes before {h2:02d}:{m2:02d}?",
                     f"Cia mheud mionaid ro {h2:02d}:{m2:02d} a tha {h1:02d}:{m1:02d}?", lang)
    scaffold = sc.clock_face(h1, m1, note=f"Count on from {h1:02d}:{m1:02d} to {h2:02d}:{m2:02d}.")
    return Question(prompt, str(diff), numeric_check(diff), scaffold)


def ms_elapsed_time(lang: str = "en") -> Question:
    h1 = random.randint(0, 22)
    m1 = random.randint(0, 59)
    diff = random.randint(12, 55)
    t1 = h1 * 60 + m1
    t2 = t1 + diff

    def as_time(t: int) -> tuple[int, int]:
        return (t // 60) % 24, t % 60

    cur = t1
    stops = [as_time(cur)]
    jump_labels: list[str] = []

    if cur % 10 != 0:
        nxt = min(((cur // 10) + 1) * 10, t2)
        if nxt > cur:
            jump_labels.append(f"+{nxt - cur} min")
            cur = nxt
            stops.append(as_time(cur))

    while t2 - cur >= 10:
        cur += 10
        jump_labels.append("+10 min")
        stops.append(as_time(cur))

    if t2 - cur > 0:
        jump_labels.append(f"+{t2 - cur} min")
        cur = t2
        stops.append(as_time(cur))

    h2, m2 = as_time(t2)
    prompt = _t(f"From {h1:02d}:{m1:02d} to {h2:02d}:{m2:02d} is ☐ minutes elapsed.",
                f"Bho {h1:02d}:{m1:02d} gu {h2:02d}:{m2:02d} tha ☐ mionaid air a dhol seachad.", lang)
    scaffold = sc.elapsed_time_line(stops, jump_labels)
    return Question(prompt, str(diff), numeric_check(diff), scaffold)


MENTAL_STRATEGIES: dict[str, dict] = {
    "MS1": {"en": "Number bonds to 5", "gd": "Bannan àireimh gu 5", "fn": ms_number_bonds_to_5},
    "MS2": {"en": "Number bonds to 10", "gd": "Bannan àireimh gu 10", "fn": ms_number_bonds_to_10},
    "MS3": {"en": "Number bonds to 20", "gd": "Bannan àireimh gu 20", "fn": ms_number_bonds_to_20},
    "MS4": {"en": "Number bonds to 100", "gd": "Bannan àireimh gu 100", "fn": ms_number_bonds_to_100},
    "MS5": {"en": "Doubling a single digit number", "gd": "A' dùblachadh àireamh aon-fhigear", "fn": ms_double_single_digit},
    "MS6": {"en": "Doubling a two digit number", "gd": "A' dùblachadh àireamh dà-fhigear", "fn": ms_double_two_digit},
    "MS7": {"en": "Halving a single digit number", "gd": "A' gabhail leth àireamh aon-fhigear", "fn": ms_halve_single_digit},
    "MS8": {"en": "Halving a two digit number", "gd": "A' gabhail leth àireamh dà-fhigear", "fn": ms_halve_two_digit},
    "MS9": {"en": "Adding 10 to a number", "gd": "A' cur 10 ri àireamh", "fn": ms_add_10},
    "MS10": {"en": "Subtracting 10 from a number", "gd": "A' toirt 10 air falbh o àireamh", "fn": ms_subtract_10},
    "MS28": {"en": "Adding 9 to a number", "gd": "A' cur 9 ri àireamh", "fn": ms_add_9},
    "MS29": {"en": "Adding within 20, bridging 10", "gd": "A' cur ri taobh a-staigh 20, a' drochaid 10", "fn": ms_add_within_20_bridge_10},
    "MS30": {"en": "Number bonds within 10", "gd": "Bannan àireimh taobh a-staigh 10", "fn": ms_number_bonds_within_10},
    "MS11": {"en": "Adding multiples of 10 to a number", "gd": "A' cur iomadan de 10 ri àireamh", "fn": ms_add_multiples_of_10},
    "MS12": {"en": "Subtracting multiples of 10 from a number", "gd": "A' toirt iomadan de 10 air falbh o àireamh", "fn": ms_subtract_multiples_of_10},
    "MS13": {"en": "How many to a multiple of 10?", "gd": "Cia mheud gu iomadach de 10?", "fn": ms_how_many_to_multiple_of_10},
    "MS14": {"en": "Add near doubles and compensate", "gd": "Cuir ris dlùth-dhùblaidhean agus dèan suas", "fn": ms_add_near_doubles},
    "MS15": {"en": "Partitioning single digit numbers", "gd": "A' roinn àireamhan aon-fhigear", "fn": ms_partition_single_digit},
    "MS16": {"en": "Partitioning two digit numbers", "gd": "A' roinn àireamhan dà-fhigear", "fn": ms_partition_two_digit},
    "MS17": {"en": "Add using number bonds to bridge a multiple of 10", "gd": "Cuir ris a' cleachdadh bannan àireimh gus iomadach de 10 a dhrochaid", "fn": ms_add_bridge_10},
    "MS18": {"en": "Subtract using number bonds to bridge a multiple of 10", "gd": "Thoir air falbh a' cleachdadh bannan àireimh gus iomadach de 10 a dhrochaid", "fn": ms_subtract_bridge_10},
    "MS19": {"en": "Count from smallest to largest in a subtraction", "gd": "Cunnt bhon fhear as lugha chun fhear as motha ann an toirt-air-falbh", "fn": ms_count_smallest_to_largest},
    "MS20": {"en": "Reorder an addition", "gd": "Ath-òrdaich cur-ris", "fn": ms_reorder_addition},
    "MS21": {"en": "Understand multiplication as repeated addition", "gd": "Tuig iomadachadh mar chur-ris a-rithist is a-rithist", "fn": ms_multiplication_repeated_addition},
    "MS22": {"en": "Understand division as the inverse of multiplication", "gd": "Tuig roinneadh mar chaochladh iomadachaidh", "fn": ms_division_inverse_multiplication},
    "MS23": {"en": "Equivalent calculations to make an addition easier", "gd": "Àireamhachadh co-ionann gus cur-ris a dhèanamh nas fhasa", "fn": ms_equivalent_calc_addition},
    "MS25": {"en": "24 hour clock", "gd": "Uaireadair 24-uair", "fn": ms_24_hour_clock},
    "MS26": {"en": "How many minutes to/past a time?", "gd": "Cia mheud mionaid gu/seach àm?", "fn": ms_minutes_to_past},
    "MS27": {"en": "Elapsed time", "gd": "Ùine air dol seachad", "fn": ms_elapsed_time},
}
