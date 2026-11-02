
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient
from app.main import app


DATA_FILE = ROOT / "data" / "expanded_eval_unique.jsonl"
REPORT_FILE = ROOT / "reports" / "pipeline_latest.json"

client = TestClient(app)


def main():
    examples = []

    with DATA_FILE.open("r", encoding="utf-8") as file:
        for line in file:
            if line.strip():
                examples.append(json.loads(line))

    counts = Counter()
    category_counts = {}
    errors = []
    true_positive = 0

    for index, example in enumerate(examples, start=1):
        text = example["text"]
        label = int(example["label"])
        category = example.get("category", "unknown")

        source = "document" if category == "indirect_injection" else "user"

        response = client.post(
            "/screen",
            json={"text": text, "source": source},
        )
        response.raise_for_status()
        result = response.json()

        decision = result["decision"]
        flagged = decision in {"block", "sanitize"}
        correct = flagged == bool(label)

        counts["total"] += 1
        counts["correct"] += int(correct)
        counts["false_positive"] += int(label == 0 and flagged)
        counts["false_negative"] += int(label == 1 and not flagged)
        counts["true_positive"] += int(label == 1 and flagged)

        if decision == "allow":
            counts["allowed"] += 1
        elif decision == "block":
            counts["blocked"] += 1
        elif decision == "sanitize":
            counts["sanitized"] += 1

        group = category_counts.setdefault(
            category,
            {
                "total": 0,
                "correct": 0,
                "false_positive": 0,
                "false_negative": 0,
            },
        )

        group["total"] += 1
        group["correct"] += int(correct)
        group["false_positive"] += int(label == 0 and flagged)
        group["false_negative"] += int(label == 1 and not flagged)

        if not correct:
            errors.append({
                "index": index,
                "category": category,
                "label": label,
                "decision": decision,
                "risk_score": result["risk_score"],
                "signals": result["signals"],
                "text": text,
            })

    total = counts["total"]
    tp = counts["true_positive"]
    fp = counts["false_positive"]
    fn = counts["false_negative"]

    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall else 0.0
    )
    accuracy = counts["correct"] / total if total else 0.0

    report = {
        "total": total,
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "false_positive": fp,
        "false_negative": fn,
        "decision_counts": {
            "allow": counts["allowed"],
            "block": counts["blocked"],
            "sanitize": counts["sanitized"],
        },
        "category_counts": category_counts,
        "errors": errors,
    }

    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    REPORT_FILE.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"Examples evaluated: {total}")
    print(f"Accuracy:           {accuracy:.3f}")
    print(f"Precision:          {precision:.3f}")
    print(f"Recall:             {recall:.3f}")
    print(f"F1-score:           {f1:.3f}")
    print(f"False positives:    {fp}")
    print(f"False negatives:    {fn}")

    print("\nDecision counts:")
    print(f"ALLOW:              {counts['allowed']}")
    print(f"BLOCK:              {counts['blocked']}")
    print(f"SANITIZE:           {counts['sanitized']}")

    print("\nCategory accuracy:")
    for name, group in category_counts.items():
        accuracy_for_category = group["correct"] / group["total"]
        print(
            f"{name}: {group['correct']}/{group['total']} "
            f"({accuracy_for_category:.3f})"
        )

    print(f"\nReport saved to: {REPORT_FILE}")


if __name__ == "__main__":
    main()
