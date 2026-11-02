
import json
from pathlib import Path

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
)

ROOT = Path(__file__).resolve().parent.parent
REPORT_FILE = ROOT / "reports" / "expanded_latest.json"


def main():
    with REPORT_FILE.open("r", encoding="utf-8") as file:
        report = json.load(file)

    examples = report["examples"]
    actual = [item["actual_label"] for item in examples]
    scores = [item["score"] for item in examples]

    print("\nThreshold comparison")
    print("-" * 86)
    print(
        f"{'Threshold':<12}{'Accuracy':<12}{'Precision':<12}"
        f"{'Recall':<12}{'F1':<12}{'FPR':<12}{'Missed':<8}"
    )
    print("-" * 86)

    for threshold in [0.40, 0.42, 0.44, 0.46, 0.48, 0.49, 0.50]:
        predicted = [
            int(score >= threshold) for score in scores
        ]

        tn, fp, fn, tp = confusion_matrix(
            actual, predicted, labels=[0, 1]
        ).ravel()

        fpr = fp / (fp + tn) if (fp + tn) else 0.0

        print(
            f"{threshold:<12.2f}"
            f"{accuracy_score(actual, predicted):<12.3f}"
            f"{precision_score(actual, predicted, zero_division=0):<12.3f}"
            f"{recall_score(actual, predicted, zero_division=0):<12.3f}"
            f"{f1_score(actual, predicted, zero_division=0):<12.3f}"
            f"{fpr:<12.3f}"
            f"{fn:<8}"
        )


if __name__ == "__main__":
    main()
