
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sklearn.metrics import (
    confusion_matrix,
    precision_score,
    recall_score,
)

from app.classifier import score
TEST_FILE = ROOT / "data" / "test.jsonl"
REPORT_FILE = ROOT / "reports" / "latest.json"

THRESHOLD = 0.5


def load_test_data():
    texts = []
    labels = []

    with TEST_FILE.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                continue

            try:
                item = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Invalid JSON in test data, line {line_number}"
                ) from exc

            if not isinstance(item.get("text"), str):
                raise ValueError(f"Invalid text at line {line_number}")

            if item.get("label") not in (0, 1):
                raise ValueError(f"Invalid label at line {line_number}")

            texts.append(item["text"])
            labels.append(item["label"])

    if not texts:
        raise ValueError("Test dataset is empty.")

    if len(set(labels)) < 2:
        raise ValueError("Test dataset must contain both labels 0 and 1.")

    return texts, labels


def run_evaluation():
    texts, actual = load_test_data()
    scores = [score(text) for text in texts]
    predicted = [int(value >= THRESHOLD) for value in scores]

    tn, fp, fn, tp = confusion_matrix(
        actual, predicted, labels=[0, 1]
    ).ravel()

    report = {
        "model": "TF-IDF + Logistic Regression",
        "threshold": THRESHOLD,
        "test_examples": len(texts),
        "class_distribution": {
            "legitimate": actual.count(0),
            "malicious": actual.count(1),
        },
        "metrics": {
            "precision": float(precision_score(
                actual, predicted, zero_division=0
            )),
            "recall": float(recall_score(
                actual, predicted, zero_division=0
            )),
            "false_positive_rate": float(
                fp / (fp + tn) if fp + tn else 0.0
            ),
            "confusion_matrix": {
                "true_negative": int(tn),
                "false_positive": int(fp),
                "false_negative": int(fn),
                "true_positive": int(tp),
            },
        },
        "examples": [
            {
                "text": text,
                "actual_label": int(label),
                "score": round(float(value), 4),
                "predicted_label": int(prediction),
            }
            for text, label, value, prediction
            in zip(texts, actual, scores, predicted)
        ],
        "limitations": [
            "The test dataset is very small.",
            "Scores and metrics are preliminary and not evidence of real-world reliability.",
            "The threshold is a prototype setting, not a production security policy.",
        ],
    }

    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    REPORT_FILE.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"Test examples: {len(texts)}")
    print(f"Precision: {report['metrics']['precision']:.3f}")
    print(f"Recall: {report['metrics']['recall']:.3f}")
    print(
        "False-positive rate: "
        f"{report['metrics']['false_positive_rate']:.3f}"
    )
    print(f"Report saved to: {REPORT_FILE}")


if __name__ == "__main__":
    run_evaluation()
