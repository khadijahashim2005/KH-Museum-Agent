import json
import random
from typing import Any, Dict, List

from evaluation.utils import clean_value, generate_expected_keywords, slugify
from api.config.llm_client import call_llm

INPUT_FILE = "data/british_museum_collections.json"
OUTPUT_FILE = "data/soft_testing_set.json"

def load_dataset(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("Dataset must be a list containing an 'artifacts' list.")
    return data


# This function returns the prompt text.
def build_soft_mcq_prompt(title: str, summary: str, categories: str | None) -> str:
    categories_text = categories if categories else "None"

    return f"""
You are generating evaluation multiple-choice questions for a museum artifact dataset.

Use only the information explicitly stated in the artifact summary and categories below.
Do not invent facts.
Do not use outside knowledge.
Do not use the URL or any information not provided here.

Generate 1 to 5 factual multiple-choice questions.

Rules:
- Each question must be clearly answerable from the provided summary or categories.
- Prioritise the summary. Use categories only if they provide clear factual support.
- Avoid vague, opinion-based, or interpretive questions.
- Avoid repeating obvious hard-knowledge fields where possible.
- Each question must have exactly 1 correct answer and 3 plausible distractors.
- Distractors must be incorrect but believable in context.
- Return only valid JSON.
- Do not wrap the JSON in markdown code fences.
- Do not include any explanation before or after the JSON.
- Return a JSON list of objects in exactly this format:
[
  {{
    "question": "...",
    "correct_answer": "...",
    "distractors": ["...", "...", "..."]
  }}
]

Artifact title: {title}
Summary: {summary}
Categories: {categories_text}
""".strip()

# This function calls the LLM with the prompt and returns the parsed response.


def parse_soft_mcq_response(response_text: str) -> List[Dict[str, Any]]:
    if not response_text:
        return []

    cleaned = response_text.strip()

    if cleaned.startswith("```json"):
        cleaned = cleaned[len("```json"):].strip()
    elif cleaned.startswith("```"):
        cleaned = cleaned[len("```"):].strip()

    if cleaned.endswith("```"):
        cleaned = cleaned[:-3].strip()

    try:
        data = json.loads(cleaned)
        if isinstance(data, list):
            return data
    except json.JSONDecodeError as e:
        print(f"Soft MCQ JSON parsing failed: {e}")
        print("Response was:")
        print(response_text)

    return []
    
# This is the main function to build soft MCQ question objects for an artifact. 
# It extracts the title, summary, and categories, builds the prompt, calls the LLM, and parses the response. 
# The returned list of question objects can then be used for evaluation.
def build_soft_question_objects(artifact: Dict[str, Any]) -> List[Dict[str, Any]]:
    title = clean_value(artifact.get("title"))
    summary = clean_value(artifact.get("summary"))
    categories = clean_value(artifact.get("categories"))

    if not title or not summary:
        return []
    
    prompt = build_soft_mcq_prompt(title, summary, categories)
    response = call_llm(prompt)
    raw_questions = parse_soft_mcq_response(response)

    question_objects: List[Dict[str, Any]] = []

    for i, item in enumerate(raw_questions):
        question = clean_value(item.get("question"))
        correct_answer = clean_value(item.get("correct_answer"))
        distractors = item.get("distractors", [])

        if not question or not correct_answer:
            continue    
        
        if not isinstance(distractors, list) or len(distractors) != 3:
            continue

        cleaned_distractors = [clean_value(d) for d in distractors if clean_value(d)]
        if any(not d for d in cleaned_distractors):
            continue

        options = cleaned_distractors + [correct_answer]
        random.shuffle(options)
        question_objects.append({
            "id": f"{slugify(title)}_soft_{i+1}",
            "artifact_title": title,
            "question_type": "soft",
            "source_field": "summary/categories",
            "question": question,
            "correct_answer": correct_answer,
            "distractors": cleaned_distractors,
            "options": options,
            "expected_keywords": generate_expected_keywords(correct_answer),
            "source_summary": summary
        })

    return question_objects
    
def build_full_soft_testing_set(dataset: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    full_set: List[Dict[str, Any]] = []

    for artifact in dataset:
        title = clean_value(artifact.get("title")) or "UNKNOWN_ARTIFACT"
        print(f"Generating soft questions for: {title}")

        try:
            questions = build_soft_question_objects(artifact)
            full_set.extend(questions)
        except Exception as e:
            print(f"Soft question generation failed for {title}: {e}")

    print(f"Generated {len(full_set)} total soft questions.")
    return full_set


def save_json(data: List[Dict[str, Any]], path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main() -> None:
    dataset = load_dataset(INPUT_FILE)
    soft_testing_set = build_full_soft_testing_set(dataset)
    save_json(soft_testing_set, OUTPUT_FILE)
    print(f"Saved soft testing set to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()