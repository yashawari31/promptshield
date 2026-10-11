
import json
from pathlib import Path

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

ROOT = Path(__file__).resolve().parent.parent
TRAIN_FILE = ROOT / "data" / "train.jsonl"
MODEL_FILE = ROOT / "ml" / "promptshield_model.joblib"


def load_dataset(path: Path):
    texts = []
    labels = []

    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                continue

            try:
                item = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Invalid JSON in {path}, line {line_number}"
                ) from exc

            if not isinstance(item.get("text"), str):
                raise ValueError(f"Missing or invalid text at line {line_number}")

            if item.get("label") not in (0, 1):
                raise ValueError(f"Label must be 0 or 1 at line {line_number}")

            texts.append(item["text"])
            labels.append(item["label"])

    if len(set(labels)) < 2:
        raise ValueError("Training data must contain both labels 0 and 1.")

    return texts, labels


def train():
    texts, labels = load_dataset(TRAIN_FILE)

    model = Pipeline([
        (
            "tfidf",
            TfidfVectorizer(
                lowercase=True,
                ngram_range=(1, 2),
                sublinear_tf=True,
            ),
        ),
        (
            "classifier",
            LogisticRegression(
                class_weight="balanced",
                max_iter=1000,
                random_state=42,
            ),
        ),
    ])

    model.fit(texts, labels)

    MODEL_FILE.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_FILE)

    print(f"Training examples: {len(texts)}")
    print(f"Model saved to: {MODEL_FILE}")


if __name__ == "__main__":
    train()
