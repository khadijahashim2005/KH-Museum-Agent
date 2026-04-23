# ============================================================
# report.py
# Generates a readable evaluation report from
# data/evaluation_results.json produced by evaluation_script.py
#
# Usage: python evaluation_pipeline/report.py
# Output: data/evaluation_report.txt  (and prints to console)
# ============================================================

import json
import os
from typing import Dict, List

# ── Paths ───────────────────────────────────────────────────
BASE_DIR      = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_FILE  = os.path.join(BASE_DIR, "data", "evaluation_results.json")
REPORT_FILE   = os.path.join(BASE_DIR, "data", "evaluation_report.txt")


def load_results(path: str) -> dict:
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Results not found: {path}\n"
            "Run evaluation/evaluation_script.py first."
        )
    with open(path, "r") as f:
        return json.load(f)


def format_bar(score: float, width: int = 20) -> str:
    """Simple ASCII progress bar for a 0–1 score."""
    filled = int(score * width)
    return f"[{'█' * filled}{'░' * (width - filled)}] {score:.0%}"


def group_by_artifact(results: List[Dict]) -> Dict[str, List[Dict]]:
    groups: Dict[str, List[Dict]] = {}
    for r in results:
        title = r.get("artifact_title", "Unknown")
        groups.setdefault(title, []).append(r)
    return groups


def group_by_type(results: List[Dict]) -> Dict[str, List[Dict]]:
    groups: Dict[str, List[Dict]] = {}
    for r in results:
        qtype = r.get("question_type", "unknown")
        groups.setdefault(qtype, []).append(r)
    return groups


def generate_report(data: dict) -> str:
    lines = []

    summary = data.get("summary", {})
    results = data.get("results", [])

    # ── Header ──────────────────────────────────────────────
    lines.append("=" * 60)
    lines.append("  KH MUSEUM AGENT — EVALUATION REPORT")
    lines.append("=" * 60)
    lines.append("")

    # ── Overall summary ─────────────────────────────────────
    total    = summary.get("total_questions", len(results))
    correct  = summary.get("correct", sum(1 for r in results if r.get("is_correct")))
    accuracy = summary.get("accuracy", correct / total if total else 0)

    lines.append("OVERALL SUMMARY")
    lines.append("-" * 40)
    lines.append(f"Total questions : {total}")
    lines.append(f"Correct answers : {correct}")
    lines.append(f"Accuracy        : {format_bar(accuracy)}")
    lines.append("")

    # ── By question type ────────────────────────────────────
    by_type = group_by_type(results)
    if by_type:
        lines.append("BY QUESTION TYPE")
        lines.append("-" * 40)
        for qtype, items in sorted(by_type.items()):
            n       = len(items)
            n_corr  = sum(1 for r in items if r.get("is_correct"))
            acc     = n_corr / n if n else 0
            lines.append(f"  {qtype.upper():<10} {format_bar(acc)}  ({n_corr}/{n})")
        lines.append("")

    # ── By artefact ─────────────────────────────────────────
    by_artifact = group_by_artifact(results)
    if by_artifact:
        lines.append("BY ARTEFACT")
        lines.append("-" * 40)
        for title, items in sorted(by_artifact.items()):
            n      = len(items)
            n_corr = sum(1 for r in items if r.get("is_correct"))
            acc    = n_corr / n if n else 0
            lines.append(f"\n  {title}")
            lines.append(f"  {format_bar(acc)}  ({n_corr}/{n} correct)")

            # Break down by field
            by_field: Dict[str, List] = {}
            for r in items:
                field = r.get("source_field", "unknown")
                by_field.setdefault(field, []).append(r)

            for field, field_items in sorted(by_field.items()):
                fn = len(field_items)
                fc = sum(1 for r in field_items if r.get("is_correct"))
                lines.append(f"    {field:<25} {fc}/{fn}")
        lines.append("")

    # ── Wrong answers ────────────────────────────────────────
    wrong = [r for r in results if not r.get("is_correct")]
    if wrong:
        lines.append(f"INCORRECT ANSWERS ({len(wrong)} total)")
        lines.append("-" * 40)
        for r in wrong[:20]:   # cap at 20 for readability
            lines.append(f"\n  [{r.get('artifact_title', '?')}]")
            lines.append(f"  Q: {r['question']}")
            lines.append(f"  ✓  {r['correct_answer']}")
            lines.append(f"  ✗  {r.get('agent_response', '?')}")
        if len(wrong) > 20:
            lines.append(f"\n  ... and {len(wrong) - 20} more (see evaluation_results.json)")
        lines.append("")

    lines.append("=" * 60)
    lines.append("END OF REPORT")
    lines.append("=" * 60)

    return "\n".join(lines)


def main() -> None:
    print(f"Loading results from {RESULTS_FILE}...")
    data   = load_results(RESULTS_FILE)
    report = generate_report(data)

    print(report)

    os.makedirs(os.path.dirname(REPORT_FILE), exist_ok=True)
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\nReport saved → {REPORT_FILE}")


if __name__ == "__main__":
    main()