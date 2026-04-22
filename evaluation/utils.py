# Utility functions for question generation and evaluation
# These functions handle tasks like:
# - Cleaning and standardizing field values -> slugify(), clean_value(), 
# - Parsing the infobox_raw field -> parse_infobox_raw()
# - Extracting dimensions -> extract_dimensions()
# - Generating expected keywords for evaluation -> generate_expected_keywords()
# - Generating distractors for MCQs -> build_distractors()
# - field fallback logic -> get_field_with_fallback()

import json
import re
import random
from typing import Any, Dict, List, Optional

def slugify(text: str) -> str:
    text = text.lower().strip() # convert to lowercase and remove leading/trailing spaces
    text = re.sub(r"[^a-z0-9]+", "_", text) # replace non-alphanumeric characters with underscores
    return text.strip("_") # remove leading/trailing underscores

def parse_infobox_raw(artifact: Dict[str, Any]) -> Dict[str, Any]:
    raw = artifact.get("infobox_raw") 
    if not raw:
        return {}
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}
    return {}

def clean_value(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, list):
        value = ", ".join(str(v).strip() for v in value if str(v).strip())
    elif isinstance(value, dict):
        value = json.dumps(value, ensure_ascii=False)
    else:
        value = str(value).strip()
    return value if value else None

def get_field_with_fallback(artifact: Dict[str, Any], infobox: Dict[str, Any],top_level_key: str,infobox_keys: List[str]) -> Optional[str]:
   
    top_value = clean_value(artifact.get(top_level_key))
    if top_value:
        return top_value

    for key in infobox_keys:
        value = clean_value(infobox.get(key))
        
        if value:
            return value
    
    return None

def extract_dimensions(artifact: Dict[str, Any], infobox: Dict[str, Any]) -> Dict[str, str]:
    results: Dict[str, str] = {}

    height = get_field_with_fallback(artifact, infobox, "height", ["height", "length"])
    width = get_field_with_fallback(artifact, infobox, "width", ["width", "breadth"])

    if height:
        results["height"] = height
    if width:
        results["width"] = width

    dimensions = clean_value(artifact.get("dimensions"))
    if not dimensions:
        return results

    if "height" not in results:
        height_match = re.search(r"height[:\s]*([\d.]+\s*cm)", dimensions, re.IGNORECASE)
        first_number_match = re.match(r"([\d.]+\s*cm)", dimensions, re.IGNORECASE)

        if height_match:
            results["height"] = height_match.group(1).strip()
        elif first_number_match:
            results["height"] = first_number_match.group(1).strip()

    if "width" not in results:
        width_match = re.search(r"width[:\s]*([\d.]+\s*cm)", dimensions, re.IGNORECASE)
        if width_match:
            results["width"] = width_match.group(1).strip()

    return results

def generate_expected_keywords(answer: str) -> List[str]:
    parts = re.split(r"[,;/()]|\band\b", answer.lower())
    keywords: List[str] = []

    for part in parts:
        cleaned = re.sub(r"\s+", " ", part).strip()
        if cleaned and cleaned not in keywords:
            keywords.append(cleaned)

    return keywords[:5]

def build_distractors(correct_answer: str, source_field: str) -> List[str]:
    pools = {
        "materials": ["Limestone", "Basalt", "Marble", "Bronze", "Clay"],
        "current_location": [
            "Louvre Museum, Paris",
            "Egyptian Museum, Cairo",
            "Metropolitan Museum of Art, New York",
            "Ashmolean Museum, Oxford",
        ],
        "dimensions": [
            "50 cm × 70 cm",
            "80 cm × 120 cm",
            "100 cm × 150 cm",
            "30 cm × 45 cm",
        ],
        "created": ["c. 600 BC", "c. 900 BC", "c. 300 BC", "c. 722 AD"],
        "height": ["75 cm", "105 cm", "120 cm", "150 cm"],
        "width": ["110 cm", "125 cm", "145 cm", "160 cm"],
        "categories": [
            "Ancient Greek pottery",
            "Roman mosaics",
            "Medieval manuscripts",
            "Bronze Age tools",
        ],
        "discovery_site": [
            "Alexandria, Egypt",
            "Athens, Greece",
            "Rome, Italy",
            "Babylon, Iraq",
        ],
        "discovered_by": [
            "Howard Carter",
            "Jean-François Champollion",
            "Austen Henry Layard",
            "Flinders Petrie",
        ],
        "language": ["Latin", "Akkadian", "Coptic", "Old Persian"],
        "culture": ["Roman", "Greek", "Byzantine", "Assyrian"],
        "weight": ["5 kg", "12 kg", "25 kg", "40 kg"],
        "origin": ["Egypt", "Greece", "Mesopotamia", "Persia"],
        "period": ["Bronze Age", "Iron Age", "Ptolemaic period", "Roman period"],
    }
   
    pool = pools.get(source_field, ["Unknown", "Not recorded", "Private collection", "Uncertain"])

    distractors = [x for x in pool if x.lower() != correct_answer.lower()]

    random.shuffle(distractors)

    return distractors[:3]