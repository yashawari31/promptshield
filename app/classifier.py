
from pathlib import Path

import joblib

ROOT = Path(__file__).resolve().parent.parent
MODEL_FILE = ROOT / "ml" / "promptshield_model.joblib"

_model = None


def load_model():
    """Load the trained classifier once and reuse it."""
    global _model

    if _model is None:
        if not MODEL_FILE.exists():
            raise FileNotFoundError(
                f"Model not found at {MODEL_FILE}. "
                "Run: python ml/train.py"
            )
        _model = joblib.load(MODEL_FILE)

    return _model


def score(text: str) -> float:
    """Return the model's estimated probability that text is malicious."""
    if not isinstance(text, str):
        raise TypeError("text must be a string")

    if not text.strip():
        return 0.0

    model = load_model()
    probabilities = model.predict_proba([text])[0]
    classes = list(model.classes_)

    malicious_index = classes.index(1)
    return float(probabilities[malicious_index])
