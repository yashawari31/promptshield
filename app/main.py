from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, HTTPException

from app.audit import get_event, log_event
from app.classifier import score
from app.detectors import detect
from app.normalize import normalize
from app.policy import decide
from app.schemas import ScreenRequest, ScreenResponse

app = FastAPI(
    title="PromptShield API",
    description="Prompt injection and data exfiltration screening API",
    version="1.0.0",
)


@app.get("/health")
def health():
    root = Path(__file__).resolve().parent.parent
    return {
        "status": "ok",
        "classifier_model_available": (root / "ml" / "promptshield_model.joblib").exists(),
    }


@app.post("/screen", response_model=ScreenResponse)
def screen(request: ScreenRequest):
    request_id = str(uuid4())

    try:
        normalized = normalize(request.text)
        signals = detect(normalized, request.source)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    # Keep screening available if the trained model has not been installed.
    try:
        classifier_score = score(request.text)
    except FileNotFoundError:
        classifier_score = None

    result = decide(request.text, signals, classifier_score, request.source)

    response = {
        "request_id": request_id,
        "decision": result["decision"],
        "reason": result["reason"],
        "risk_score": classifier_score,
        "signals": signals,
        "sanitized_text": result["sanitized_text"],
    }

    log_event({
        "request_id": request_id,
        "source": request.source,
        "decision": result["decision"],
        "risk_score": classifier_score,
        "rule_ids": sorted({s.get("rule_id", "unknown") for s in signals}),
        "signal_count": len(signals),
    })

    return response


@app.get("/audit/{request_id}")
def audit(request_id: str):
    event = get_event(request_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Audit record not found")
    return event
