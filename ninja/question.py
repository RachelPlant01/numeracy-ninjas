from dataclasses import dataclass
from typing import Callable


@dataclass
class Question:
    prompt: str
    answer_display: str
    checker: Callable[[str], bool]
    scaffold_html: str
    input_hint: str = ""
