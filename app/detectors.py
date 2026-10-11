
import re
import unicodedata
from pathlib import Path

import yaml


PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROTECTED_FILE = PROJECT_ROOT / "config" / "protected.yaml"


RULES = [
    {
        "rule_id": "R-OVR-1",
        "category": "instruction_override",
        "pattern": re.compile(
            r"\b(ignore|disregard|override|forget)\b"
            r".{0,60}\b(previous|prior|all|system|developer)\b"
            r".{0,40}\b(instructions?|rules?|prompts?|directives?)\b",
            re.IGNORECASE,
        ),
        "signal": "override_phrase",
        "detail": "Possible attempt to override existing instructions",
        "weight": 0.95,
    },
    {
        "rule_id": "R-OVR-2",
        "category": "instruction_override",
        "pattern": re.compile(
            r"\b(you are now|act as|pretend to be)\b"
            r".{0,50}\b(unrestricted|unfiltered|jailbroken|without rules)\b",
            re.IGNORECASE,
        ),
        "signal": "role_override",
        "detail": "Possible attempt to change the assistant's role",
        "weight": 0.85,
    },
    {
        "rule_id": "R-SEC-1",
        "category": "secret_exfiltration",
        "pattern": re.compile(
            r"\b(reveal|disclose|print|show|expose|leak|repeat)\b"
            r".{0,60}\b(hidden|system|developer|secret|private|confidential)\b"
            r".{0,40}\b(prompt|instructions?|key|token|credentials?|data|message)?\b",
            re.IGNORECASE,
        ),
        "signal": "secret_reveal_phrase",
        "detail": "Possible attempt to reveal protected information",
        "weight": 0.95,
    },
    {
        "rule_id": "R-SEC-2",
        "category": "secret_exfiltration",
        "pattern": re.compile(
            r"\b(print|show|reveal|output|return|dump)\b"
            r".{0,40}\b(api[_ -]?key|password|access token|secret key)\b",
            re.IGNORECASE,
        ),
        "signal": "credential_reveal_phrase",
        "detail": "Possible attempt to expose credentials",
        "weight": 0.98,
    },
    {
        "rule_id": "R-DST-1",
        "category": "exfil_destination",
        "pattern": re.compile(
            r"\b(send|forward|upload|email|transmit|exfiltrate)\b"
            r".{0,100}\b(secret|credentials?|private data|hidden prompt|api[_ -]?key)\b",
            re.IGNORECASE,
        ),
        "signal": "data_transfer_phrase",
        "detail": "Possible attempt to send protected information elsewhere",
        "weight": 0.95,
    },
]


def load_protected_values() -> list[dict]:
    """Load configured protected values from config/protected.yaml."""
    if not PROTECTED_FILE.exists():
        return []

    with PROTECTED_FILE.open("r", encoding="utf-8") as file:
        config = yaml.safe_load(file) or {}

    values = config.get("protected_values", [])

    if not isinstance(values, list):
        raise ValueError("protected_values must be a list")

    return [
        item
        for item in values
        if isinstance(item, dict)
        and isinstance(item.get("id"), str)
        and isinstance(item.get("value"), str)
        and item["value"]
    ]


def compact_secret(value: str) -> str:
    """Normalize Unicode, case and whitespace for comparison."""
    value = unicodedata.normalize("NFKC", value).casefold()
    return "".join(char for char in value if not char.isspace())


def find_protected_values(text: str) -> list[dict]:
    """Detect configured protected values despite case or spacing changes."""
    compact_text = compact_secret(text)
    signals = []

    for item in load_protected_values():
        secret = compact_secret(item["value"])

        if secret in compact_text:
            signals.append({
                "rule_id": "R-SEC-3",
                "category": "secret_exfiltration",
                "signal": "protected_value_match",
                "detail": (
                    f"Configured protected value detected: {item['id']}"
                ),
                "span": None,
                "weight": 1.0,
            })

    return signals


def detect(norm: dict, source: str) -> list[dict]:
    """
    Inspect normalized views and return suspicious signals.

    Sources: user, voice_transcript, tool_output, document.
    Final allow/block/sanitize/escalate decisions belong to the policy engine.
    """
    valid_sources = {
        "user",
        "voice_transcript",
        "tool_output",
        "document",
    }

    if source not in valid_sources:
        raise ValueError(f"Unsupported source: {source}")

    views = norm.get("views", [])

    if not isinstance(views, list):
        raise TypeError("norm['views'] must be a list")

    original_text = views[0] if views else ""
    signals = find_protected_values(original_text)

    seen = {
        (signal["rule_id"], signal["category"], signal["signal"])
        for signal in signals
    }

    for view in views:
        if not isinstance(view, str):
            continue

        for rule in RULES:
            for match in rule["pattern"].finditer(view):
                key = (
                    rule["rule_id"],
                    rule["category"],
                    rule["signal"],
                )

                if key in seen:
                    continue

                seen.add(key)

                signals.append({
                    "rule_id": rule["rule_id"],
                    "category": rule["category"],
                    "signal": rule["signal"],
                    "detail": rule["detail"],
                    "span": [match.start(), match.end()],
                    "weight": rule["weight"],
                })

    return signals
