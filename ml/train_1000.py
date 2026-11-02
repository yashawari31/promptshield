
import json
from pathlib import Path

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

ROOT = Path(__file__).resolve().parent.parent
TRAIN_FILE = ROOT / "data" / "train_1000.jsonl"
MODEL_FILE = ROOT / "ml" / "promptshield_model_1000.joblib"


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
                    f"Invalid JSON at line {line_number}"
                ) from exc

            if not isinstance(item.get("text"), str):
                raise ValueError(
                    f"Invalid text at line {line_number}"
                )

            if item.get("label") not in (0, 1):
                raise ValueError(
                    f"Invalid label at line {line_number}"
                )

            texts.append(item["text"])
            labels.append(item["label"])

    if len(texts) < 10 or len(set(labels)) != 2:
        raise ValueError(
            "Dataset must contain at least 10 examples and both labels."
        )

    if len({text.casefold() for text in texts}) != len(texts):
        raise ValueError("Duplicate texts detected in the dataset.")

    return texts, labels


def create_model():
    return Pipeline([
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


def main():
    texts, labels = load_dataset(TRAIN_FILE)

    X_train, X_test, y_train, y_test = train_test_split(
        texts,
        labels,
        test_size=0.20,
        random_state=42,
        stratify=labels,
    )

    # Train only on the training split so the test split remains unseen.
    model = create_model()
    model.fit(X_train, y_train)

    predictions = model.predict(X_test)

    print("\nPROMPTSHIELD 1000-DATASET EVALUATION")
    print(f"Total examples: {len(texts)}")
    print(f"Training examples: {len(X_train)}")
    print(f"Test examples: {len(X_test)}")
    print(f"Accuracy: {accuracy_score(y_test, predictions):.2%}")

    print("\nClassification report:")
    print(classification_report(
        y_test,
        predictions,
        labels=[0, 1],
        target_names=["Benign", "Malicious"],
        zero_division=0,
    ))

    print("Confusion matrix [rows=actual, columns=predicted]:")
    print(confusion_matrix(y_test, predictions, labels=[0, 1]))

    MODEL_FILE.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_FILE)

    print(f"\nSeparate model saved to: {MODEL_FILE}")
    print("The existing PromptShield model was not overwritten.")


if __name__ == "__main__":
    main()
