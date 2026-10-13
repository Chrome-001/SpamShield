"""Text preprocessing helpers.

Documented pipeline (used inside the scikit-learn Pipeline via TfidfVectorizer,
plus these helpers for analysis / display):

1. Normalize: lowercase text.
2. Strip surrounding whitespace.
3. Collapse repeated whitespace to single spaces.
4. (Vectorizer) tokenize on word boundaries (``(?u)\\b\\w\\w+\\b``),
   drop English stop words, extract word unigrams + bigrams.
5. (Vectorizer) compute TF-IDF weights with a capped vocabulary
   (``max_features``, default 5000 — safe for low-memory machines).

No heavy dependencies; everything else is handled by scikit-learn.
"""

from __future__ import annotations

import re

MAX_INPUT_CHARS = 5000  # shared input-size guard (also enforced in predictor.py)

_WHITESPACE_RE = re.compile(r"\s+")


def clean_text(text: str) -> str:
    """Normalize raw message text for display/analysis.

    Lowercases, strips, and collapses whitespace. Non-string input
    returns an empty string (callers validate separately).
    """
    if not isinstance(text, str):
        return ""
    text = text.lower().strip()
    return _WHITESPACE_RE.sub(" ", text)


def validate_input(text: str, max_chars: int = MAX_INPUT_CHARS) -> tuple[bool, str]:
    """Validate a user-supplied message.

    Returns ``(is_valid, error_message)``. Empty string means valid.
    """
    if not isinstance(text, str):
        return False, "Input must be text."
    if not text.strip():
        return False, "Please enter a message to analyze (input is empty)."
    if len(text) > max_chars:
        return (
            False,
            f"Message is too long ({len(text)} characters; limit is {max_chars}). "
            "Please shorten it and try again.",
        )
    return True, ""


def truncate_for_display(text: str, limit: int = 200) -> str:
    """Shorten text for safe display; never used for logging full contents."""
    if len(text) <= limit:
        return text
    return text[:limit] + "…"
