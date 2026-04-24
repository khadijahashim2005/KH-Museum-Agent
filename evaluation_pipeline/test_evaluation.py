# ============================================================
# test_evaluation.py
# Runs full evaluation across all 10 artefacts.
#
# Usage: python scripts/test_evaluation.py
# Requires: data/cached_agents.json
# Output:   data/evaluation_results.json
# ============================================================

import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, "api"))

from dotenv import load_dotenv
load_dotenv()

import json
from interactor import Interactor
from evaluation_pipeline.run_evaluation import run_full_evaluation

CACHE_FILE   = os.path.join(BASE_DIR, "data", "cached_agents.json")
RESULTS_FILE = os.path.join(BASE_DIR, "data", "evaluation_results.json")

# ── Config ───────────────────────────────────────────────────
ALL_INDICES = list(range(10))  # evaluate all 10 artefacts (0-9)
N_RUNS      = 3                # runs per artefact to average


def load_cache() -> dict:
    if not os.path.exists(CACHE_FILE):
        print(f"❌ Cache not found: {CACHE_FILE}")
        sys.exit(1)
    with open(CACHE_FILE, "r") as f:
        return json.load(f)


def run_once(artefact: dict, profile: str, run_num: int, total: int) -> dict:
    print(f"\n{'─'*60}")
    print(f"  RUN {run_num}/{total} — {artefact.get('title')}")
    print(f"{'─'*60}")
    interactor = Interactor(profile)
    interactor.start()
    return run_full_evaluation(interactor, artefact)


def average_results(all_runs: list) -> dict:
    n = len(all_runs)
    return {
        "hard_knowledge_avg": round(sum(r["hard_knowledge"]["accuracy"]       for r in all_runs) / n, 2),
        "soft_knowledge_avg": round(sum(r["soft_knowledge"]["avg_score"]      for r in all_runs) / n, 2),
        "safety_avg":         round(sum(r["safety"]["safety_score"]           for r in all_runs) / n, 2),
        "consistency_avg":    round(sum(r["consistency"]["consistency_score"] for r in all_runs) / n, 2),
        "overall_avg":        round(sum(r["overall_score"]                    for r in all_runs) / n, 2),
        "n_runs":             n,
        "individual_scores":  [r["overall_score"] for r in all_runs],
    }


def save_result(result: dict):
    existing = []
    if os.path.exists(RESULTS_FILE):
        try:
            with open(RESULTS_FILE, "r") as f:
                data = json.load(f)
            existing = data if isinstance(data, list) else [data]
        except Exception:
            existing = []
    existing.append(result)
    with open(RESULTS_FILE, "w") as f:
        json.dump(existing, f, indent=2, ensure_ascii=False)


def print_summary(avg: dict, title: str):
    w = 60
    print(f"\n{'='*w}")
    print(f"  {title}")
    print(f"  ({avg['n_runs']} runs averaged)")
    print(f"{'='*w}")
    print(f"  Hard Knowledge : {avg['hard_knowledge_avg']:.2f}")
    print(f"  Soft Knowledge : {avg['soft_knowledge_avg']:.2f}")
    print(f"  Safety         : {avg['safety_avg']:.2f}")
    print(f"  Consistency    : {avg['consistency_avg']:.2f}")
    print(f"  {'─'*38}")
    print(f"  Overall Avg    : {avg['overall_avg']:.2f}")
    print(f"  Individual     : {avg['individual_scores']}")
    print(f"{'='*w}")

# Add this function before main():
def get_completed_artefacts() -> set:
    if not os.path.exists(RESULTS_FILE):
        return set()
    try:
        with open(RESULTS_FILE, "r") as f:
            data = json.load(f)
        if isinstance(data, list):
            return {entry.get("artefact") for entry in data if "averaged" in entry}
    except Exception:
        pass
    return set()

def main():
    cache = load_cache()
    completed = get_completed_artefacts()
    if completed:
        print(f"Resuming — skipping already completed: {completed}")
    print(f"Evaluating {len(ALL_INDICES)} artefacts × {N_RUNS} runs each\n")


    all_averages = []

    for idx in ALL_INDICES:
        cache_key = f"museum-experience_{idx}"
        if cache_key not in cache:
            print(f"⚠️  Cache key not found: {cache_key} — skipping")
            continue

        cached   = cache[cache_key]
        artefact = cached["artefact"]
        profile  = cached["profile"]
        title    = artefact.get("title", f"Artefact {idx}")

        if title in completed:
            print(f"⏭️  Skipping {title} — already evaluated")
            continue 
        print(f"\n{'#'*60}")
        print(f"  ARTEFACT {idx+1}/10: {title}")
        print(f"{'#'*60}")

        all_runs = []
        for run_num in range(1, N_RUNS + 1):
            result = run_once(artefact, profile, run_num, N_RUNS)
            all_runs.append(result)

        avg = average_results(all_runs)
        print_summary(avg, title)

        output = {
            "artefact": title,
            "index":    idx,
            "n_runs":   N_RUNS,
            "averaged": avg,
            "runs":     all_runs,
        }

        save_result(output)
        all_averages.append((title, avg["overall_avg"]))
        print(f"  ✅ Saved results for {title}")

    # ── Final summary across all artefacts ───────────────────
    if all_averages:
        print(f"\n{'='*60}")
        print(f"  FINAL SUMMARY — ALL ARTEFACTS")
        print(f"{'='*60}")
        for title, score in all_averages:
            print(f"  {title[:40]:<40} {score:.2f}")
        overall_mean = round(sum(s for _, s in all_averages) / len(all_averages), 2)
        print(f"  {'─'*50}")
        print(f"  Mean overall score : {overall_mean:.2f}")
        print(f"{'='*60}")
        print(f"\nAll results saved → {RESULTS_FILE}")


if __name__ == "__main__":
    main()