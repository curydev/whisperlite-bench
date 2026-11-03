"""Text normalization applied to both reference and hypothesis before CER.

Rules (see docs/measurement-rules.md):
1. Unicode NFKC, lowercase.
2. Drop punctuation and symbols.
3. Drop all whitespace, so spacing differences do not count as errors.

Digits are kept as-is. Whisper often writes "3시" where the reference says
"세 시"; converting digits to Korean readings is ambiguous (native vs.
Sino-Korean), so the team decides that rule separately and counts how often
it happens with has_digits().
"""

import re
import unicodedata

_PUNCT = re.compile(r"[^\w\s]|_", re.UNICODE)
_SPACE = re.compile(r"\s+", re.UNICODE)
_DIGIT = re.compile(r"\d")


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).lower()
    text = _PUNCT.sub("", text)
    return _SPACE.sub("", text)


def has_digits(text: str) -> bool:
    return bool(_DIGIT.search(text))
