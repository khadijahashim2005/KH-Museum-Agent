import json
from typing import Any, Dict, List

from .hard_mcq_generator import load_dataset, build_hard_question_objects
from .soft_mcq_generator import build_soft_question_objects

INPUT_FILE = "data/british_museum_collections.json"
OUTPUT_FILE = "data/full_testing_set.json"


def build_combined_question_objects(artifact: Dict[str, Any]) -> List[Dict[str, Any]]:
    hard_questions = build_hard_question_objects(artifact)

    try:
        soft_questions = build_soft_question_objects(artifact)
    except Exception as e:
        title = artifact.get("title", "UNKNOWN_ARTIFACT")
        print(f"Soft question generation failed for {title}: {e}")
        soft_questions = []
    print(f"Generated {len(hard_questions)} hard and {len(soft_questions)} soft questions for artifact: {artifact.get('title', 'UNKNOWN_ARTIFACT')}")
    return hard_questions + soft_questions


def save_json(data: List[Dict[str, Any]], path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main() -> None:
    dataset = load_dataset(INPUT_FILE)
    full_testing_set: List[Dict[str, Any]] = []
    skipped: List[str] = []

    for artifact in dataset:
        title = artifact.get("title", "UNKNOWN_ARTIFACT")
        print(f"Processing: {title}")

        questions = build_combined_question_objects(artifact)

        if len(questions) >= 4:
            full_testing_set.extend(questions)
        else:
            skipped.append({
                "title": title,
                "question_count": len(questions)
            })

    save_json(full_testing_set, OUTPUT_FILE)
    print(f"Saved {len(full_testing_set)} total questions to {OUTPUT_FILE}")
    print(f"Skipped {len(skipped)} artifacts with fewer than 4 total combined questions.")

    if skipped:
        print("Examples of skipped artifacts:")
        for item in skipped[:20]:
            print(f"- {item['title']} ({item['question_count']} questions)")


if __name__ == "__main__":
    main()