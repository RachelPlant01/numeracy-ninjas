"""Curriculum links for each skill — CfE Experiences and Outcomes — plus the
four progress levels used by the tracker.

STATUS: DRAFT. The codes below were checked against the Education Scotland
lists (numeracy-across-learning-eo.pdf and numeracy-maths-eo.pdf), but which
skill links to which code is a first draft for the teacher to confirm.
Wording is shortened. Edit SKILL_EOS freely — the worksheets and trackers
read from here.
"""
from __future__ import annotations

EO_DRAFT = True  # set to False once the mapping has been checked

# code -> short wording
EOS: dict[str, str] = {
    "MNU 0-02a": "Explore numbers as quantities; count, create sequences and describe order.",
    "MNU 0-03a": "Use practical materials and 'count on and back' to understand addition and subtraction.",
    "MNU 1-01a": "Develop ways of estimating the answer to a calculation, then check against the estimate.",
    "MNU 1-02a": "How whole numbers are constructed; the link between a digit, its place and its value.",
    "MNU 1-03a": "Use +, −, ×, ÷ to solve problems, making best use of mental strategies and written skills.",
    "MNU 1-07b": "Find a fraction of an amount by applying knowledge of division.",
    "MNU 1-10a": "Tell the time using 12 hour clocks, realising the link with 24 hour notation.",
    "MNU 2-01a": "Use rounding to estimate the answer, then decide if the answer is reasonable.",
    "MNU 2-02a": "Extend the range of whole numbers; how decimal fractions are constructed; place and value.",
    "MNU 2-03a": "Solve problems involving whole numbers using a range of methods.",
    "MNU 2-03b": "Solve problems involving decimal fractions using a variety of methods.",
    "MNU 2-04a": "The number line extends to include numbers less than zero.",
    "MNU 2-07a": "Carry out calculations with simple fractions, percentages and decimal fractions in everyday contexts.",
    "MNU 2-07b": "Show equivalent forms of simple fractions, decimal fractions and percentages.",
    "MNU 2-10a": "Use and interpret timetables and schedules; make time calculations.",
    "MNU 3-01a": "Round a number using an appropriate degree of accuracy.",
    "MNU 3-03a": "Use a variety of methods to solve number problems, clearly communicating processes.",
    "MNU 3-03b": "Recall number facts quickly and use them accurately when making calculations.",
    "MNU 3-04a": "Use understanding of numbers less than zero to solve simple problems in context.",
    "MNU 3-07a": "Calculate with a wide range of fractions, decimal fractions and percentages.",
    "MTH 1-07c": "Show understanding of simple fractions which are equivalent (practical / pictorial).",
    "MTH 2-05a": "Investigate and identify the multiples and factors of numbers.",
    "MTH 2-07c": "Create sets of equivalent fractions; understand simplest form.",
    "MTH 3-06a": "Notation and vocabulary of whole number powers; evaluate powers.",
    "MTH 3-14a": "Collect like terms, simplify expressions and evaluate using substitution.",
    "MTH 4-06a": "The relationship between powers and roots.",
}

# skill id -> list of E&O codes (lowest level first)
SKILL_EOS: dict[str, list[str]] = {
    # ---- Mental strategies
    "MS1": ["MNU 0-03a"],
    "MS2": ["MNU 0-03a", "MNU 1-03a"],
    "MS30": ["MNU 0-03a", "MNU 1-03a"],
    "MS3": ["MNU 1-03a"],
    "MS4": ["MNU 1-03a", "MNU 2-03a"],
    "MS5": ["MNU 1-03a"],
    "MS6": ["MNU 1-03a", "MNU 2-03a"],
    "MS7": ["MNU 1-03a"],
    "MS8": ["MNU 1-03a", "MNU 2-03a"],
    "MS9": ["MNU 1-02a", "MNU 1-03a"],
    "MS10": ["MNU 1-02a", "MNU 1-03a"],
    "MS28": ["MNU 1-03a"],
    "MS29": ["MNU 1-03a"],
    "MS11": ["MNU 1-03a", "MNU 2-03a"],
    "MS12": ["MNU 1-03a", "MNU 2-03a"],
    "MS13": ["MNU 1-03a"],
    "MS14": ["MNU 1-03a", "MNU 2-03a"],
    "MS15": ["MNU 0-03a", "MNU 1-03a"],
    "MS16": ["MNU 1-02a", "MNU 1-03a"],
    "MS17": ["MNU 1-03a", "MNU 2-03a"],
    "MS18": ["MNU 1-03a", "MNU 2-03a"],
    "MS19": ["MNU 1-03a", "MNU 2-03a"],
    "MS20": ["MNU 1-03a"],
    "MS21": ["MNU 1-03a"],
    "MS22": ["MNU 1-03a"],
    "MS23": ["MNU 2-03a"],
    "MS25": ["MNU 1-10a", "MNU 2-10a"],
    "MS26": ["MNU 1-10a"],
    "MS27": ["MNU 2-10a"],
    # ---- Key skills
    "KS1": ["MNU 2-03a", "MNU 3-03a"],
    "KS2": ["MNU 2-03a", "MNU 3-03a"],
    "KS3": ["MNU 2-03a", "MNU 3-03a"],
    "KS4": ["MNU 2-03a", "MNU 3-03a"],
    "KS5": ["MNU 3-03a"],
    "KS6": ["MNU 3-03a"],
    "KS7": ["MNU 2-03b", "MNU 3-03a"],
    "KS8": ["MNU 2-03b", "MNU 3-03a"],
    "KS9": ["MNU 1-02a", "MNU 2-02a"],
    "KS10": ["MNU 2-07b", "MNU 3-07a"],
    "KS11": ["MNU 2-02a", "MNU 2-03b"],
    "KS12": ["MNU 2-02a", "MNU 2-03b"],
    "KS13": ["MNU 2-03b"],
    "KS14": ["MNU 2-03b"],
    "KS15": ["MNU 3-04a"],
    "KS16": ["MNU 3-04a"],
    "KS17": ["MTH 2-07c"],
    "KS18": ["MNU 2-01a", "MNU 3-01a"],
    "KS19": ["MTH 3-14a"],
    "KS20": ["MNU 2-04a", "MNU 3-04a"],
    "KS21": ["MNU 2-04a", "MNU 3-04a"],
    "KS22": ["MNU 3-04a"],
    "KS24": ["MNU 3-01a"],
    "KS25": ["MTH 2-05a"],
    "KS26": ["MTH 2-05a"],
    "KS28": ["MTH 3-06a", "MTH 4-06a"],
    "KS29": ["MTH 3-06a", "MTH 4-06a"],
    "KS30": ["MTH 1-07c", "MTH 2-07c"],
    "KS31": ["MNU 1-07b", "MNU 2-07a"],
    "KS32": ["MNU 2-07a", "MNU 3-07a"],
}

# Tracker levels, lowest to highest: (short code, label, fill colour)
LEVELS: list[tuple[str, str, str]] = [
    ("1", "With scaffolds and support", "#f8c9c4"),
    ("2", "Scaffolds, no support", "#fde3a7"),
    ("3", "No scaffolds", "#cfe8c4"),
    ("4", "No scaffolds — very fluent", "#8fd18a"),
]


def eo_codes(skill_id: str) -> list[str]:
    return SKILL_EOS.get(skill_id, [])


def eo_label(skill_id: str) -> str:
    codes = eo_codes(skill_id)
    return ", ".join(codes) if codes else "TBC"
