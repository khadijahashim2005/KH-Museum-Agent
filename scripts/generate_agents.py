# ============================================================
# generate_agents.py
# Run ONCE to pre-generate all museum agents
# Usage: python scripts/generate_agents.py
# ============================================================

import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from mistralai.client import Mistral

load_dotenv()

DATASET_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "..", "AutoGame-copy", "data", "british_museum_collections.json"
)

CACHE_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "cached_agents.json"
)

EVENTS_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "museum_events.json"
)

COLLECTOR_INSTRUCTIONS = """For the given information about antique, please create a digital instructor's profile. 
Please make sure the instructor and antique should be related, include:
1) from the same culture background
2) have connection during the discovering
3) education purpose
4) be interesting to the child

The profile should be in json format, Include:
name, gender, age, summarisation of antique, additional information"""


def generate_profile_with_image(artefact: dict) -> dict:
    """Generate profile + image using Collector agent with extended timeout"""
    client = Mistral(
        api_key=os.getenv("MISTRAL_API_KEY"),
        timeout_ms=300000  # 5 minutes - plenty of time for web search + image generation
    )
    collector_agent_id = os.getenv("COLLECTOR_AGENT_ID")

    response = client.beta.conversations.start(
        agent_id=collector_agent_id,
        inputs=[{
            "role": "user",
            "content": json.dumps(artefact)
        }],
    )

    profile_text = ""
    image_url = None

    for output in response.outputs:
        if output.type == "message.output":
            if isinstance(output.content, str):
                profile_text = output.content
            elif isinstance(output.content, list):
                for chunk in output.content:
                    if hasattr(chunk, 'text'):
                        profile_text += chunk.text
                    elif hasattr(chunk, 'file_id'):
                        try:
                            url_response = client.files.get_signed_url(
                                file_id=chunk.file_id
                            )
                            image_url = url_response.url
                            print(f"    Image generated ✅")
                        except Exception as e:
                            print(f"    Image URL failed: {e}")

    return {
        "profile": profile_text,
        "image_url": image_url
    }


def load_dataset() -> list:
    with open(DATASET_FILE, "r") as f:
        return json.load(f)


def pick_best_artefacts(dataset: list, count: int = 10) -> list:
    scored = []
    for item in dataset:
        score = 0
        if item.get("summary"): score += 3
        if item.get("materials"): score += 2
        if item.get("current_location"): score += 2
        if item.get("discovery_site"): score += 1
        if item.get("culture"): score += 1
        if item.get("period"): score += 1
        if item.get("dimensions"): score += 1
        if item.get("url"): score += 1
        if score >= 5:
            scored.append((score, item))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in scored[:count]]


def generate_all_agents():
    print("Loading British Museum dataset...")
    dataset = load_dataset()
    print(f"Found {len(dataset)} artefacts\n")

    print("Selecting best 10 artefacts...")
    selected = pick_best_artefacts(dataset, count=10)
    for i, item in enumerate(selected):
        print(f"  {i+1}. {item.get('title')}")

    print(f"\nGenerating agents (this will take 10-20 minutes)...\n")

    cached_agents = {}
    museum_events = {
        "total events": len(selected),
        "current index": 0,
        "event": []
    }

    for i, item in enumerate(selected):
        title = item.get("title", "Unknown")
        print(f"[{i+1}/{len(selected)}] {title}...")

        artefact = {
            "title": title,
            "url": item.get("url", ""),
            "summary": item.get("summary", ""),
            "current_location": item.get("current_location", ""),
            "materials": item.get("materials", ""),
            "origin": item.get("origin", ""),
            "culture": item.get("culture", ""),
            "period": item.get("period", ""),
            "discovery_site": item.get("discovery_site", ""),
            "dimensions": item.get("dimensions", ""),
            "categories": item.get("categories", ""),
            "infobox_raw": item.get("infobox_raw", "{}")
        }

        try:
            result = generate_profile_with_image(artefact)
            profile = result["profile"]
            image_url = result["image_url"]

            cache_key = f"museum-experience_{i}"
            cached_agents[cache_key] = {
                "title": title,
                "artefact": artefact,
                "profile": profile,
                "image_url": image_url,
                "existing_character": None
            }

            museum_events["event"].append({
                "event": f"Visitor approaches the {title}",
                "character": [],
                "location": item.get("current_location", "British Museum"),
                "description": item.get("summary", "")[:200],
                "artifact": {
                    "name": title,
                    "material": item.get("materials", ""),
                    "origin": item.get("origin", ""),
                    "date": item.get("period", ""),
                    "current_location": item.get("current_location", ""),
                    "description": item.get("summary", "")
                }
            })

            # Save after each agent in case script fails
            with open(CACHE_FILE, "w") as f:
                json.dump(cached_agents, f, indent=2, ensure_ascii=False)

            print(f"  ✅ Done! Profile: ✅ Image: {'✅' if image_url else '❌'}\n")

        except Exception as e:
            print(f"  ❌ Failed: {e}\n")

    # Save museum events
    with open(EVENTS_FILE, "w") as f:
        json.dump(museum_events, f, indent=2, ensure_ascii=False)

    print(f"{'='*60}")
    print(f"✅ Generated {len(cached_agents)}/{len(selected)} agents")
    print(f"Saved to: {CACHE_FILE}")
    print(f"{'='*60}")


if __name__ == "__main__":
    generate_all_agents()