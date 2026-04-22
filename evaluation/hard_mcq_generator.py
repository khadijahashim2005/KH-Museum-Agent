import json
import random
import re
from typing import Any, Dict, List, Optional
from evaluation.utils import (
    clean_value,
    get_field_with_fallback,
    extract_dimensions,
    generate_expected_keywords,
    build_distractors,
    slugify,
    parse_infobox_raw,
)

INPUT_FILE = "data/british_museum_collections.json"
OUTPUT_FILE = "data/hard_testing_set.json"
# Tells the script which fields in the infobox to check for each top-level field when the top-level field is empty.
FALLBACK_MAP = {
    "current_location": ["present location", "location", "owner"],
    "created": ["created", "year", "date"],
    "materials": ["material", "medium"],
    "dimensions": ["dimensions", "size", "length"],
    "weight": ["weight"],
    "discovery_site": ["place discovered", "discovery place", "found at", "location discovered", "place"],
    "discovered_by": ["discovered by"],
    "language": ["language", "writing", "original language"],
    "culture": ["culture", "period/culture"],
    "origin": ["country", "country of origin", "countries", "region"],
    "period": ["movement"],
}
# Tells the script which question template to use for each field.
QUESTION_MAP = {
    "current_location": "Where is the {title} currently located?",
    "created": "In which year was the {title} created?",
    "materials": "What material is the {title} made of?",
    "dimensions": "What are the dimensions of the {title}?",
    "height": "What is the height of the {title}?",
    "width": "What is the width of the {title}?",
    "weight": "What is the weight of the {title}?",
    "discovery_site": "Where was the {title} discovered?",
    "discovered_by": "Who discovered the {title}?",
    "language": "What language or writing system appears in or is associated with the {title}?",
    "culture": "Which culture is associated with the {title}?",
    "origin": "Which country or region is associated with the origin of the {title}?",
    "period": "Which period is associated with the {title}?",
}

def load_dataset(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    if not isinstance(data, list):
        raise ValueError("Dataset must be a list containing an 'artifacts' list.")
    return data

def build_hard_question_objects(artifact: Dict[str, Any]) -> List[Dict[str, Any]]:
    infobox = parse_infobox_raw(artifact)
    title = clean_value(artifact.get("title"))

    if not title:
        return []

    artifact_slug = slugify(title)
    candidate_questions: List[Dict[str, Any]] = []
    questions: List[Dict[str, Any]] = []
    q_num = 1

    dimensions = extract_dimensions(artifact, infobox)

    for field_name, infobox_keys in FALLBACK_MAP.items():
        if field_name == "dimensions":
            continue

        value = get_field_with_fallback(artifact, infobox, field_name, infobox_keys)
        if value and field_name in QUESTION_MAP:
            candidate_questions.append({
                "source_field": field_name,
                "question": QUESTION_MAP[field_name].format(title=title),
                "correct_answer": value,
            })

    if "height" in dimensions:
        candidate_questions.append({
            "source_field": "height",
            "question": QUESTION_MAP["height"].format(title=title),
            "correct_answer": dimensions["height"],
        })

    if "width" in dimensions:
        candidate_questions.append({
            "source_field": "width",
            "question": QUESTION_MAP["width"].format(title=title),
            "correct_answer": dimensions["width"],
        })

    if "height" not in dimensions and "width" not in dimensions:
        full_dimensions = get_field_with_fallback(
            artifact,
            infobox,
            "dimensions",
            FALLBACK_MAP["dimensions"],
        )
        if full_dimensions:
            candidate_questions.append({
                "source_field": "dimensions",
                "question": QUESTION_MAP["dimensions"].format(title=title),
                "correct_answer": full_dimensions,
            })

    for item in candidate_questions:
        distractors = build_distractors(item["correct_answer"], item["source_field"])
        if len(distractors) < 3:
            continue

        all_options = [item["correct_answer"]] + distractors[:3]
        random.shuffle(all_options)

        questions.append({
            "id": f"{artifact_slug}_hard_{q_num}",
            "artifact_title": title,
            "question_type": "hard",
            "source_field": item["source_field"],
            "question": item["question"],
            "correct_answer": item["correct_answer"],
            "distractors": distractors,
            "options": all_options,
            "expected_keywords": generate_expected_keywords(item["correct_answer"]),
        })
        q_num += 1

    return questions

def build_full_testing_set(dataset: List[Dict[str, Any]], min_questions_per_artifact: int = 4) -> List[Dict[str, Any]]:
    full_set: List[Dict[str, Any]] = []

    for artifact in dataset:
        full_set.extend(build_hard_question_objects(artifact))

    print(f"Generated {len(full_set)} total hard questions.")
    return full_set

# Save the generated dataset to a JSON file
def save_json(data: List[Dict[str, Any]], path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# Main function to run the whole process
def main() -> None:
    dataset = load_dataset(INPUT_FILE)
    full_testing_set = build_full_testing_set(dataset, min_questions_per_artifact=4)
    save_json(full_testing_set, OUTPUT_FILE)
    print(f"Saved full testing set to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()