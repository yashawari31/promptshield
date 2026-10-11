
import json

from eval.run_eval import run_evaluation, REPORT_FILE


def test_evaluation_generates_valid_report():
    run_evaluation()

    assert REPORT_FILE.exists()

    report = json.loads(REPORT_FILE.read_text(encoding="utf-8"))

    assert report["test_examples"] == 26
    assert report["model"] == "TF-IDF + Logistic Regression"

    metrics = report["metrics"]
    assert 0.0 <= metrics["precision"] <= 1.0
    assert 0.0 <= metrics["recall"] <= 1.0
    assert 0.0 <= metrics["false_positive_rate"] <= 1.0

    matrix = metrics["confusion_matrix"]
    assert sum(matrix.values()) == report["test_examples"]
