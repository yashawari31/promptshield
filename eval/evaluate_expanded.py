
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)

from app.classifier import score

TEST_FILE = ROOT / "data" / "expanded_eval_unique.jsonl"
REPORT_FILE = ROOT / "reports" / "expanded_latest.json"
ERROR_FILE = ROOT / "reports" / "expanded_errors.csv"
THRESHOLD = 0.5


def load_data():
    texts, labels, categories = [], [], []

    with TEST_FILE.open("r", encoding="utf-8") as file:
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
                raise ValueError(f"Invalid text at line {line_number}")

            if item.get("label") not in (0, 1):
                raise ValueError(f"Invalid label at line {line_number}")

            texts.append(item["text"])
            labels.append(item["label"])
            categories.append(item.get("category", "uncategorized"))

    if not texts:
        raise ValueError("Expanded dataset is empty.")

    if len(set(labels)) != 2:
        raise ValueError("Dataset must contain both labels 0 and 1.")

    return texts, labels, categories


def calculate_metrics(actual, predicted):
    tn, fp, fn, tp = confusion_matrix(
        actual, predicted, labels=[0, 1]
    ).ravel()

    return {
        "accuracy": float(accuracy_score(actual, predicted)),
        "precision": float(
            precision_score(actual, predicted, zero_division=0)
        ),
        "recall": float(
            recall_score(actual, predicted, zero_division=0)
        ),
        "f1_score": float(
            f1_score(actual, predicted, zero_division=0)
        ),
        "false_positive_rate": float(
            fp / (fp + tn) if (fp + tn) else 0.0
        ),
        "confusion_matrix": {
            "true_negative": int(tn),
            "false_positive": int(fp),
            "false_negative": int(fn),
            "true_positive": int(tp),
        },
    }


def run_evaluation():
    texts, actual, categories = load_data()

    scores = [float(score(text)) for text in texts]
    predicted = [int(value >= THRESHOLD) for value in scores]

    category_indices = defaultdict(list)
    for index, category in enumerate(categories):
        category_indices[category].append(index)

    category_results = {}

    for category, indices in sorted(category_indices.items()):
        category_actual = [actual[i] for i in indices]
        category_predicted = [predicted[i] for i in indices]

        category_results[category] = {
            "examples": len(indices),
            "legitimate": category_actual.count(0),
            "malicious": category_actual.count(1),
            "metrics": calculate_metrics(
                category_actual, category_predicted
            ),
        }

    report = {
        "model": "TF-IDF + Logistic Regression",
        "threshold": THRESHOLD,
        "test_file": str(TEST_FILE.relative_to(ROOT)),
        "test_examples": len(texts),
        "class_distribution": {
            "legitimate": actual.count(0),
            "malicious": actual.count(1),
        },
        "metrics": calculate_metrics(actual, predicted),
        "category_results": category_results,
        "examples": [
            {
                "text": text,
                "actual_label": int(label),
                "score": round(value, 4),
                "predicted_label": int(prediction),
                "category": category,
            }
            for text, label, value, prediction, category
            in zip(texts, actual, scores, predicted, categories)
        ],
        "limitations": [
            "The dataset is synthetic and combination-generated.",
            "Results are preliminary and do not establish real-world reliability.",
            "Mixed-content examples are evaluated as binary malicious/legitimate labels; this does not measure SANITIZE behavior.",
            "Threshold 0.5 is a prototype setting.",
        ],
    }

    # Save the complete evaluation report.
    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    REPORT_FILE.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    # Select only misclassified examples.
    errors = [
        item
        for item in report["examples"]
        if item["actual_label"] != item["predicted_label"]
    ]

    # Save errors to a CSV file that can be opened in Excel or VS Code.
    with ERROR_FILE.open(
        "w", newline="", encoding="utf-8-sig"
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "category",
                "text",
                "actual_label",
                "predicted_label",
                "score",
            ],
        )
        writer.writeheader()
        writer.writerows(errors)

    # Count missed attacks and incorrectly flagged legitimate prompts.
    false_negatives = sum(
        item["actual_label"] == 1
        and item["predicted_label"] == 0
        for item in errors
    )

    false_positives = sum(
        item["actual_label"] == 0
        and item["predicted_label"] == 1
        for item in errors
    )

    # Print overall evaluation metrics.
    print(f"\nExamples evaluated: {len(texts)}")
    print(f"Accuracy:           {report['metrics']['accuracy']:.3f}")
    print(f"Precision:          {report['metrics']['precision']:.3f}")
    print(f"Recall:             {report['metrics']['recall']:.3f}")
    print(f"F1-score:           {report['metrics']['f1_score']:.3f}")
    print(
        "False-positive rate: "
        f"{report['metrics']['false_positive_rate']:.3f}"
    )

    print("\nCategory-wise results:")
    for category, result in category_results.items():
        metrics = result["metrics"]
        print(
            f"{category}: n={result['examples']}, "
            f"accuracy={metrics['accuracy']:.3f}, "
            f"precision={metrics['precision']:.3f}, "
            f"recall={metrics['recall']:.3f}, "
            f"F1={metrics['f1_score']:.3f}"
        )

    print("\nError analysis:")
    print(f"Misclassified examples: {len(errors)}")
    print(f"False negatives (missed attacks): {false_negatives}")
    print(f"False positives (legitimate flagged): {false_positives}")
    print(f"\nReport saved to: {REPORT_FILE}")
    print(f"Error report saved to: {ERROR_FILE}")


if __name__ == "__main__":
    run_evaluation()
