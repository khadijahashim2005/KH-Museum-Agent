# ============================================================
# report.py
# Generates a readable evaluation report from
# data/evaluation_results.json produced by run_evaluation.py
#
# Usage: python evaluation_pipeline/report.py
# Output: printed to console + saved to data/evaluation_report.txt
# ============================================================

import json
import os
from typing import Dict, List

BASE_DIR     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_FILE = os.path.join(BASE_DIR, "data", "evaluation_results.json")
REPORT_FILE  = os.path.join(BASE_DIR, "data", "evaluation_report.txt")


def load_results(path: str) -> dict:
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Results not found: {path}\n"
            "Run scripts/test_evaluation.py or click Run Evaluation in the UI first."
        )
    with open(path, "r") as f:
        data = json.load(f)

    if isinstance(data, list):
        if not data:
            raise ValueError("No evaluation runs found in results file.")

        # Prefer latest entry that has averaged results
        averaged_entries = [e for e in data if "averaged" in e]
        if averaged_entries:
            latest   = averaged_entries[-1]
            avg      = latest["averaged"]
            last_run = latest["runs"][-1]
            print(f"Found {len(averaged_entries)} averaged run(s) — reporting on: {latest.get('artefact')}\n")
            return {
                "artifact":      latest.get("artefact", "Unknown"),
                "timestamp":     last_run.get("timestamp", ""),
                "overall_score": avg["overall_avg"],
                "hard_knowledge": {
                    **last_run["hard_knowledge"],
                    "accuracy": avg["hard_knowledge_avg"],
                },
                "soft_knowledge": {
                    **last_run["soft_knowledge"],
                    "avg_score": avg["soft_knowledge_avg"],
                },
                "safety": {
                    **last_run["safety"],
                    "safety_score": avg["safety_avg"],
                },
                "consistency": {
                    **last_run["consistency"],
                    "consistency_score": avg["consistency_avg"],
                },
            }

        # Fallback to latest single run
        print(f"Found {len(data)} run(s) — reporting on the latest.\n")
        return data[-1]

    return data


def bar(score: float, width: int = 20) -> str:
    """ASCII progress bar for a 0-1 score."""
    filled = int(score * width)
    return f"[{'█' * filled}{'░' * (width - filled)}] {score:.0%}"


def generate_report(run: dict) -> str:
    lines = []
    w = 60

    # ── Header ──────────────────────────────────────────────
    lines.append("=" * w)
    lines.append("  KH MUSEUM AGENT — EVALUATION REPORT")
    lines.append("=" * w)
    lines.append(f"  Artefact  : {run.get('artifact', 'Unknown')}")
    if run.get("timestamp"):
        lines.append(f"  Timestamp : {run['timestamp']}")
    lines.append("")

    # ── Overall score ────────────────────────────────────────
    overall = run.get("overall_score", 0)
    lines.append("OVERALL SCORE")
    lines.append("-" * w)
    lines.append(f"  {bar(overall, 30)}  ({overall:.0%})")
    lines.append("")

    # ── Dimension summary ────────────────────────────────────
    hard  = run.get("hard_knowledge", {})
    soft  = run.get("soft_knowledge", {})
    safe  = run.get("safety", {})
    cons  = run.get("consistency", {})

    lines.append("DIMENSION SUMMARY  (weights: hard 30% · soft 30% · safety 20% · consistency 20%)")
    lines.append("-" * w)

    hard_acc  = hard.get("accuracy", 0)
    soft_avg  = soft.get("avg_score", 0)
    safe_sc   = safe.get("safety_score", 0)
    cons_sc   = cons.get("consistency_score", 0)

    lines.append(f"  Hard Knowledge   {bar(hard_acc)}  "
                 f"({hard.get('correct', 0)}/{hard.get('total_questions', 0)} correct)")
    lines.append(f"  Soft Knowledge   {bar(soft_avg)}  "
                 f"(avg judge score)")
    lines.append(f"  Safety           {bar(safe_sc)}  "
                 f"({safe.get('correctly_refused', 0)}/{safe.get('total_tests', 0)} refused)")
    lines.append(f"  Consistency      {bar(cons_sc)}  "
                 f"({cons.get('consistent_count', 0)}/{cons.get('total_tests', 0)} consistent)")
    lines.append("")

    # ── Hard knowledge detail ────────────────────────────────
    lines.append("HARD KNOWLEDGE — Question Breakdown")
    lines.append("-" * w)
    for r in hard.get("results", []):
        status = "✅" if r.get("is_correct") else "❌"
        lines.append(f"  {status} [{r.get('source_field', '?')}]")
        lines.append(f"     Q: {r.get('question', '')}")
        lines.append(f"     ✓  {r.get('correct_answer', '')}")
        if not r.get("is_correct"):
            lines.append(f"     ✗  {r.get('agent_answer', '')[:80]}")
        lines.append("")

    # ── Soft knowledge detail ────────────────────────────────
    lines.append("SOFT KNOWLEDGE — Judge Results")
    lines.append("-" * w)
    for r in soft.get("results", []):
        score   = r.get("score", 0)
        verdict = r.get("verdict", "?")
        lines.append(f"  [{verdict.upper()}]  score: {score:.2f}")
        lines.append(f"     Q: {r.get('question', '')}")
        lines.append(f"     Agent: {r.get('agent_answer', '')[:100]}")
        lines.append("")

    # ── Safety detail ────────────────────────────────────────
    lines.append("SAFETY — Refusal Testing")
    lines.append("-" * w)
    for r in safe.get("results", []):
        status = "✅ Refused" if r.get("correctly_refused") else "❌ Did not refuse"
        lines.append(f"  {status}  [{r.get('category', '?')}]")
        lines.append(f"     Q: {r.get('question', '')}")
        if not r.get("correctly_refused"):
            lines.append(f"     Agent: {r.get('agent_answer', '')[:100]}")
        lines.append("")

    # ── Consistency detail ───────────────────────────────────
    lines.append("CONSISTENCY — Character Consistency")
    lines.append("-" * w)
    for r in cons.get("results", []):
        status = "✅" if r.get("is_consistent") else "❌"
        lines.append(f"  {status} Q: {r.get('question', '')}")
        lines.append(f"     Agent: {r.get('agent_answer', '')[:100]}")
        lines.append("")

    lines.append("=" * w)
    lines.append("END OF REPORT")
    lines.append("=" * w)

    return "\n".join(lines)


def generate_summary_table(path: str) -> str:
    """Generate a summary table across all evaluated artefacts."""
    with open(path, "r") as f:
        data = json.load(f)

    averaged = [e for e in data if isinstance(e, dict) and "averaged" in e]
    single_runs = [e for e in data if isinstance(e, dict) and "averaged" not in e and "artifact" in e]

    if not averaged and single_runs:
        averaged = [{
            "artefact": e.get("artifact", "Unknown"),
            "averaged": {
                "hard_knowledge_avg": e.get("hard_knowledge", {}).get("accuracy", 0),
                "soft_knowledge_avg": e.get("soft_knowledge", {}).get("avg_score", 0),
                "safety_avg": e.get("safety", {}).get("safety_score", 0),
                "consistency_avg": e.get("consistency", {}).get("consistency_score", 0),
                "overall_avg": e.get("overall_score", 0),
            },
            "runs": [e]
        } for e in single_runs]
    w = 60
    lines = []
    lines.append("\n" + "=" * w)
    lines.append("  SUMMARY — ALL ARTEFACTS")
    lines.append("=" * w)
    lines.append(f"  {'Artefact':<32} {'Hard':>5} {'Soft':>5} {'Safe':>5} {'Cons':>5} {'Avg':>5}")
    lines.append(f"  {'─'*32} {'─'*5} {'─'*5} {'─'*5} {'─'*5} {'─'*5}")

    overall_scores = []
    for entry in averaged:
        avg   = entry["averaged"]
        title = entry.get("artefact", "Unknown")[:32]
        lines.append(
            f"  {title:<32} "
            f"{avg['hard_knowledge_avg']:>5.2f} "
            f"{avg['soft_knowledge_avg']:>5.2f} "
            f"{avg['safety_avg']:>5.2f} "
            f"{avg['consistency_avg']:>5.2f} "
            f"{avg['overall_avg']:>5.2f}"
        )
        overall_scores.append(avg["overall_avg"])

    if overall_scores:
        mean = round(sum(overall_scores) / len(overall_scores), 2)
        lines.append(f"  {'─'*32} {'─'*5} {'─'*5} {'─'*5} {'─'*5} {'─'*5}")
        lines.append(f"  {'MEAN':<32} {'':>5} {'':>5} {'':>5} {'':>5} {mean:>5.2f}")

    lines.append("=" * w)
    return "\n".join(lines)


def main():
    print(f"Loading results from {RESULTS_FILE}...")
    with open(RESULTS_FILE, "r") as f:
        data = json.load(f)
    
    averaged = [e for e in data if isinstance(e, dict) and "averaged" in e]
    
    if not averaged:
        print("No averaged results found.")
        return
    
    # Summary Table
    summary = generate_summary_table(RESULTS_FILE)

    #Find best and worst 

    scores_with_entries = [
        (e.get("artefact", "Unknown"), e["averaged"]["overall_avg"], e) 
        for e in averaged
    ]

    best_title,  best_score,  best_entry  = max(scores_with_entries, key=lambda x: (x[1], x[0]))
    worst_title, worst_score, worst_entry = min(scores_with_entries, key=lambda x: x[1])

    # Use last run for detailed breakdown
    best_run  = best_entry.get("runs", [{}])[-1]
    worst_run = worst_entry.get("runs", [{}])[-1]

    # Override scores with averaged values for accuracy
    best_run["overall_score"]  = best_score
    worst_run["overall_score"] = worst_score

    best_report  = generate_report(best_run)
    worst_report = generate_report(worst_run)

    # ── Combine output ───────────────────────────────────────
    w = 60
    full_output = summary
    full_output += f"\n\n{'='*w}"
    full_output += f"\n  BEST PERFORMING AGENT: {best_title} ({best_score:.2f})"
    full_output += f"\n{'='*w}\n"
    full_output += best_report
    full_output += f"\n\n{'='*w}"
    full_output += f"\n  WORST PERFORMING AGENT: {worst_title} ({worst_score:.2f})"
    full_output += f"\n{'='*w}\n"
    full_output += worst_report

    print(full_output)

    os.makedirs(os.path.dirname(REPORT_FILE), exist_ok=True)
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(full_output)

    print(f"\nReport saved → {REPORT_FILE}")


if __name__ == "__main__":
    main()