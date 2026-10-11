
import re

from app.detectors import detect
from app.normalize import normalize


def sanitize(text: str, signals: list[dict]) -> str | None:
    """
    Remove sentences containing detected unsafe spans.

    Returns None if no legitimate content remains.
    Signals' spans may refer to normalized views, so this function
    uses the original text and sentence-level detection instead.
    """
    if not isinstance(text, str):
        raise TypeError("text must be a string")

    if not signals:
        return text.strip() or None

    # Split while retaining sentence-ending punctuation.
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    kept = []

    for sentence in sentences:
        if not sentence.strip():
            continue

        sentence_signals = detect(normalize(sentence), "tool_output")

        if sentence_signals:
            continue

        kept.append(sentence.strip())

    result = " ".join(kept).strip()
    return result or None
