from pathlib import Path
from legal_case_agent.evaluation import evaluate_dataset, markdown_report

def test_synthetic_evaluation_reports_denominators():
    report = evaluate_dataset(Path("data/synthetic"), Path("data/synthetic/gold.json"))
    assert report["dataset_version"] == "v1"
    assert report["metrics"]["file_parse_coverage"] == {"numerator": 5, "denominator": 5}
    assert report["metrics"]["source_coverage"] == {"numerator": 5, "denominator": 5}
    assert report["cases"][1]["must_review"]
    assert "case-002" in markdown_report(report)
