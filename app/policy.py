from app.sanitize import sanitize

VALID_SOURCES = {"user", "voice_transcript", "tool_output", "document"}
BLOCK_THRESHOLD = 0.85
REVIEW_THRESHOLD = 0.55


def decide(text: str, signals: list[dict], score: float | None, source: str) -> dict:
    if source not in VALID_SOURCES:
        raise ValueError(f"Unsupported source: {source}")

    # A direct match with configured protected data is a hard block.
    if any(s.get("signal") == "protected_value_match" for s in signals):
        return {"decision": "block", "reason": "Protected value detected", "sanitized_text": None}

    # Rule-based detection takes priority over a low model score.
    if signals:
        if source in {"tool_output", "document"}:
            cleaned = sanitize(text, signals, source)
            if cleaned:
                return {"decision": "sanitize", "reason": "Suspicious content removed", "sanitized_text": cleaned}
        return {"decision": "block", "reason": "Prompt-injection or data-exfiltration signal detected", "sanitized_text": None}

    # If the model is unavailable, continue using rule-based checks only.
    if score is not None and score >= BLOCK_THRESHOLD:
        return {"decision": "block", "reason": "Classifier score exceeds block threshold", "sanitized_text": None}

    if score is not None and score >= REVIEW_THRESHOLD:
        if source in {"tool_output", "document"}:
            cleaned = sanitize(text, [], source)
            return {"decision": "sanitize", "reason": "Classifier score requires cautious handling", "sanitized_text": cleaned}
        return {"decision": "block", "reason": "Classifier score requires blocking this source", "sanitized_text": None}

    return {"decision": "allow", "reason": "No suspicious signals detected", "sanitized_text": text}
