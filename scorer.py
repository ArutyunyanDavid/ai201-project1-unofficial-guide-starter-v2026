"""Deterministic scoring for the five Unit 2 evaluation questions.

The short ``expects`` phrases in questions.py were chosen before evaluation.
A run passes only when the answer contains that phrase, retrieval supplied a
chunk containing it, and the answer names that chunk's source. This combines
answer correctness with grounding instead of rewarding a lucky unsupported
answer or a citation to an unrelated retrieved file.
"""

import re
import unicodedata
from typing import Protocol


NUMBER_EQUIVALENTS = {
    "1": "one",
    "first": "one",
    "2": "two",
    "second": "two",
    "3": "three",
    "third": "three",
    "4": "four",
    "fourth": "four",
    "5": "five",
    "fifth": "five",
    "6": "six",
    "sixth": "six",
    "7": "seven",
    "seventh": "seven",
    "8": "eight",
    "eighth": "eight",
    "9": "nine",
    "ninth": "nine",
    "10": "ten",
    "tenth": "ten",
}


class SearchResult(Protocol):
    """The fields from ``store.Result`` used by the scorer."""

    text: str
    source: str


def _tokens(text: str) -> set[str]:
    """Return comparable tokens, treating cardinals and ordinals alike."""
    folded = unicodedata.normalize("NFKC", text).casefold()
    folded = re.sub(r"\b([ap])\s*\.\s*m\s*\.?", r"\1m", folded)
    raw = re.findall(r"[a-z]+|\d+(?:\.\d+)?", folded)
    return {NUMBER_EQUIVALENTS.get(token, token) for token in raw}


def _contains_expected(text: str, expects: str) -> bool:
    """Match equivalent tokens without unsafe numeric substring matches."""
    expected_tokens = _tokens(expects)
    return bool(expected_tokens) and expected_tokens <= _tokens(text)


def judge(
    question: str,
    expects: str,
    answer: str,
    results: list[SearchResult],
) -> bool:
    """Return whether an answer is correct, retrieved, and supportably cited."""
    del question  # Required by run_eval.py's scorer interface.

    if not expects.strip() or not _contains_expected(answer, expects):
        return False

    answer_lower = answer.casefold()
    return any(
        _contains_expected(result.text, expects)
        and result.source.casefold() in answer_lower
        for result in results
    )
