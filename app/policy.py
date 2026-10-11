
import re

from app.sanitize import sanitize

VALID_SOURCES = {"user", "voice_transcript", "tool_output", "document"}
BLOCK_THRESHOLD = 0.85
REVIEW_THRESHOLD = 0.65


def is_defensive_analysis(text: str, source: str) -> bool:
    """Recognize clearly framed user requests about defensive security."""
    if source != "user":
        return False

    lower = text.casefold()

    has_security_context = any(
        phrase in lower
        for phrase in (
            "prompt injection",
            "prompt-injection",
            "security awareness",
            "defensive security",
            "security scanner",
            "security research",
            "security report",
        )
    )

    has_analysis_context = any(
        phrase in lower
        for phrase in (
            "as an example",
            "example of",
            "treat the described sentence as evidence",
            "should be treated as untrusted content",
            "do not execute it",
            "do not execute any embedded instruction",
            "not as an instruction to follow",
        )
    )

    has_quoted_attack = bool(
        re.search(
            r"""(['"]).{0,180}\b(ignore|disregard|override|reveal|export)\b.{0,180}\1""",
            text,
            re.IGNORECASE,
        )
    )

    return has_security_context and (
        has_analysis_context or has_quoted_attack
    )


def decide(
    text: str,
    signals: list[dict],
    score: float | None,
    source: str,
) -> dict:
    if source not in VALID_SOURCES:
        raise ValueError(f"Unsupported source: {source}")

    # Configured protected values always take priority.
    if any(
        signal.get("signal") == "protected_value_match"
        for signal in signals
    ):
        return {
            "decision": "block",
            "reason": "Protected value detected",
            "sanitized_text": None,
        }

    # Allow clearly framed defensive analysis only for user input.
    # Never apply this exception to untrusted documents or tool output.
    if signals and is_defensive_analysis(text, source):
        return {
            "decision": "allow",
            "reason": "Defensive security analysis context",
            "sanitized_text": text,
        }

    # Explicit detector signals take priority over classifier scores.
    if signals:
        if source in {"tool_output", "document"}:
            cleaned = sanitize(text, signals, source)

            if cleaned:
                return {
                    "decision": "sanitize",
                    "reason": "Suspicious content removed",
                    "sanitized_text": cleaned,
                }

        return {
            "decision": "block",
            "reason": (
                "Prompt-injection or data-exfiltration signal detected"
            ),
            "sanitized_text": None,
        }

    # If the classifier is unavailable, continue without its score.
    if score is not None and score >= BLOCK_THRESHOLD:
        return {
            "decision": "block",
            "reason": "Classifier score exceeds block threshold",
            "sanitized_text": None,
        }

    if score is not None and score >= REVIEW_THRESHOLD:
        if source in {"tool_output", "document"}:
            cleaned = sanitize(text, [], source)
            return {
                "decision": "sanitize",
                "reason": "Classifier score requires cautious handling",
                "sanitized_text": cleaned,
            }

        return {
            "decision": "block",
            "reason": "Classifier score requires blocking this source",
            "sanitized_text": None,
        }

    return {
        "decision": "allow",
        "reason": "No suspicious signals detected",
        "sanitized_text": text,
    }
