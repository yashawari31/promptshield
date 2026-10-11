import json
from datetime import datetime, timezone
from pathlib import Path

AUDIT_FILE = Path(__file__).resolve().parent.parent / "logs" / "audit.jsonl"


def log_event(event: dict) -> None:
    AUDIT_FILE.parent.mkdir(parents=True, exist_ok=True)
    record = {
        **event,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    with AUDIT_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def get_event(request_id: str) -> dict | None:
    if not AUDIT_FILE.exists():
        return None
    with AUDIT_FILE.open("r", encoding="utf-8") as f:
        for line in reversed(f.readlines()):
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if event.get("request_id") == request_id:
                return event
    return None
