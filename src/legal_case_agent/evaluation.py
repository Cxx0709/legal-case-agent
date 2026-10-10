"""Offline evaluation for the versioned synthetic cases."""
import argparse
import json
from pathlib import Path
from .parsers import ParseError, parse_document

def markdown_report(report: dict) -> str:
    metrics = report["metrics"]
    lines = [f"# 合成数据评测报告（{report['dataset_version']}）", "", "本报告仅适用于固定版本的合成材料，不代表法律准确性或真实案件效果。", "", "## 汇总指标", "", "| 指标 | 分子 | 分母 |", "|---|---:|---:|"]
    for name, value in metrics.items():
        lines.append(f"| {name} | {value['numerator']} | {value['denominator']} |")
    lines += ["", "## 逐案例结果", ""]
    for case in report["cases"]:
        lines.append(f"### {case['id']}")
        for file in case["files"]:
            suffix = f"（{file['error']}）" if file["error"] else ""
            lines.append(f"- 文件：`{file['name']}` — **{file['status']}**{suffix}")
        lines.append(f"- 缺失来源：{'、'.join(case['missing_sources']) or '无'}")
        lines.append(f"- 待核实：{'、'.join(case['must_review']) or '无'}")
        lines.append("")
    return "\n".join(lines)

def evaluate_dataset(dataset_dir: Path, gold_path: Path) -> dict:
    gold = json.loads(gold_path.read_text(encoding="utf-8"))
    cases, parsed_total, parsed_ok, source_total, source_ok = [], 0, 0, 0, 0
    for expected in gold["cases"]:
        labels, files = set(), []
        for name in expected["expected_documents"]:
            status, error = "parsed", None
            try:
                result = parse_document(name, name, dataset_dir / expected["id"] / name)
                labels.update(chunk.source_label for chunk in result.chunks)
                if not result.chunks:
                    status, error = "needs_review", "未提取到文字"
            except (ParseError, OSError) as exc:
                status, error = "failed", str(exc)
            files.append({"name": name, "status": status, "error": error})
            parsed_total += 1
            parsed_ok += status == "parsed"
        missing = [s for s in expected["required_sources"] if s not in labels]
        source_total += len(expected["required_sources"])
        source_ok += len(expected["required_sources"]) - len(missing)
        cases.append({"id": expected["id"], "files": files, "required_sources": expected["required_sources"], "missing_sources": missing, "must_review": expected.get("must_review", [])})
    return {"dataset_version": gold["version"], "cases": cases, "metrics": {"file_parse_coverage": {"numerator": parsed_ok, "denominator": parsed_total}, "source_coverage": {"numerator": source_ok, "denominator": source_total}}}

def main() -> None:
    parser = argparse.ArgumentParser(description="评测合成案件材料的离线解析与来源覆盖")
    parser.add_argument("--dataset", type=Path, default=Path("data/synthetic"))
    parser.add_argument("--gold", type=Path, default=Path("data/synthetic/gold.json"))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--markdown", type=Path)
    args = parser.parse_args()
    text = json.dumps(evaluate_dataset(args.dataset, args.gold), ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    if args.markdown:
        args.markdown.parent.mkdir(parents=True, exist_ok=True)
        args.markdown.write_text(markdown_report(json.loads(text)) + "\n", encoding="utf-8")
    print(text)

if __name__ == "__main__":
    main()
