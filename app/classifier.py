
import os
from pathlib import Path

import joblib

ROOT = Path(__file__).resolve().parent.parent
MODEL_DIR = ROOT / "ml"
DEFAULT_MODEL = "promptshield_model.joblib"

_model = None
_loaded_path = None


def get_model_path() -> Path:
    """Return the selected model path; use the original model by default."""
    filename = os.getenv("PROMPTSHIELD_MODEL", DEFAULT_MODEL).strip()

    # Accept a filename inside ml/, not an arbitrary filesystem path.
    if not filename or Path(filename).name != filename:
        raise ValueError(
            "PROMPTSHIELD_MODEL must be a model filename inside the ml folder."
        )

    return MODEL_DIR / filename


def load_model():
    """Load and cache the selected model."""
    global _model, _loaded_path

    model_path = get_model_path()

    if not model_path.exists():
        raise FileNotFoundError(
            f"Model not found at {model_path}. "
            "Check PROMPTSHIELD_MODEL and the ml folder."
        )

    if _model is None or _loaded_path != model_path:
        _model = joblib.load(model_path)
        _loaded_path = model_path

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

    if 1 not in classes:
        raise ValueError("The classifier does not contain malicious class label 1.")

    malicious_index = classes.index(1)
    return float(probabilities[malicious_index])
