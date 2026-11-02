
import json
from pathlib import Path

import joblib
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
)

ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "data" / "expanded_eval_unique.jsonl"

MODELS = {
    "Original model": ROOT / "ml" / "promptshield_model.joblib",
    "1000-data model": ROOT / "ml" / "promptshield_model_1000.joblib",
}


def main():
    texts, labels = [], []

    with DATA_FILE.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                continue

            item = json.loads(line)
            texts.append(item["text"])
            labels.append(item["label"])

    print(f"Evaluation examples: {len(texts)}\n")

    for name, path in MODELS.items():
        model = joblib.load(path)
        predictions = model.predict(texts)

        tn, fp, fn, tp = confusion_matrix(
            labels, predictions, labels=[0, 1]
        ).ravel()

        print(f"--- {name} ---")
        print(f"Accuracy:  {accuracy_score(labels, predictions):.1%}")
        print(f"Precision: {precision_score(labels, predictions, zero_division=0):.1%}")
        print(f"Recall:    {recall_score(labels, predictions, zero_division=0):.1%}")
        print(f"F1:        {f1_score(labels, predictions, zero_division=0):.1%}")
        print(f"False positives: {fp}")
        print(f"False negatives: {fn}")
        print(f"TN={tn}, FP={fp}, FN={fn}, TP={tp}\n")


if __name__ == "__main__":
    main()
