# ============================================================
# test_evaluation.py
# Runs a full evaluation directly from the command line
# without needing the Flask UI.
#
# Usage: python scripts/test_evaluation.py
# Requires: data/cached_agents.json
# Output:   data/evaluation_results.json
# ============================================================

import os
import sys

# Add project root and api/ to path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, "api"))

from dotenv import load_dotenv
load_dotenv()

import json
from api.interactor import Interactor
from evaluation_pipeline.run_evaluation import run_full_evaluation

BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_FILE = os.path.join(BASE_DIR, "data", "cached_agents.json")

# ── Pick which artefact to evaluate ─────────────────────────
# Change this to test a different artefact (0-9)
TEST_INDEX = 0  # Abbott Papyrus
N_RUNS = 5  # Number of evaluation runs to perform (for stability testing)

def main():
    print("Loading cache...")
    if not os.path.exists(CACHE_FILE):
        print(f"❌ Cache not found: {CACHE_FILE}")
        print("Run scripts/generate_agents.py first.")
        sys.exit(1)

    with open(CACHE_FILE, "r") as f:
        cache = json.load(f)

    cache_key = f"museum-experience_{TEST_INDEX}"
    if cache_key not in cache:
        print(f"❌ Cache key not found: {cache_key}")
        sys.exit(1)

    cached   = cache[cache_key]
    artefact = cached["artefact"]
    profile  = cached["profile"]

    print(f"Artefact : {artefact.get('title')}")
    print(f"Profile  : {len(profile)} chars\n")

    # Start interactor
    print("Starting Interactor...")
    interactor = Interactor(profile)
    interactor.start()
    print("Interactor ready\n")

    # Run full evaluation
    all_scores = []
    for i in range(N_RUNS):
        print(f"\nRun {i+1}/{N_RUNS}...")
        results = run_full_evaluation(interactor, artefact)
        all_scores.append(results["overall_score"])

    print(f"\nIndividual scores : {all_scores}")
    print(f"Average score     : {round(sum(all_scores)/len(all_scores), 2)}")
    print(f"Results saved to data/evaluation_results.json")

if __name__ == "__main__":
    main()