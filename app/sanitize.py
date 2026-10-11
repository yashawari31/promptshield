
import re

from app.detectors import detect
from app.normalize import normalize


VALID_SOURCES = {
    "user",
    "voice_transcript",
    "tool_output",
    "document",
}


def sanitize(
    text: str,
    signals: list[dict],
    source: str = "tool_output",
) -> str | None:
    """
    Remove sentences that contain detectable unsafe content.

    Detection is performed per sentence using the supplied source.
    Returns None if no legitimate content remains.
    """
    if not isinstance(text, str):
        raise TypeError("text must be a string")

    if source not in VALID_SOURCES:
        raise ValueError(f"Unsupported source: {source}")

    if not text.strip():
        return None

    if not signals:
        return text.strip()

    # Preserve sentence-ending punctuation while splitting.
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    kept = []

    for sentence in sentences:
        sentence = sentence.strip()

        if not sentence:
            continue

        sentence_signals = detect(normalize(sentence), source)

        if sentence_signals:
            continue

        kept.append(sentence)

    result = " ".join(kept).strip()
    return result or None
