# ============================================================
# generate_agents.py
# Run ONCE to pre-generate all museum agents
# Usage: python scripts/generate_agents.py
# Generates:
#   museum-experience_0  to _9   ← KH individual artefacts
#   museum-experience_10 to _11  ← Group project artefacts
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
# ── Group artefacts — use existing images, just generate profiles
GROUP_ARTEFACTS = [
    {
        "cache_key":  "museum-experience_10",
        "title":      "Magdeburg Ivories",
        "agent_name": "Brother Albrecht von Magdeburg",
        "image_url":  "/story/museum-experience/images/brother-albrecht.png",
    },
    {
        "cache_key":  "museum-experience_11",
        "title":      "Rosetta Stone",
        "agent_name": "Dr. Amina Farouk",
        "image_url":  "/story/museum-experience/images/dr-amina-farouk.png",
    },
]



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
# ── Group artefacts — helpers for profile-only generation (existing images)
def generate_profile_only(artefact: dict, agent_name: str) -> str:
    """
    Generate profile only — no image generation.
    Used for group artefacts which already have images.
    Injects the agent name so the Collector builds the profile
    around that specific character.
    """
    client = Mistral(
        api_key=os.getenv("MISTRAL_API_KEY"),
        timeout_ms=300000
    )
    collector_agent_id = os.getenv("COLLECTOR_AGENT_ID")
 
    # Inject the required character name into the artefact payload
    artefact_with_name = dict(artefact)
    artefact_with_name["requested_character_name"] = agent_name
    artefact_with_name["character_instruction"] = (
        f"The character's name must be exactly: {agent_name}. "
        f"Build the entire profile around this specific person."
    )
 
    response = client.beta.conversations.start(
        agent_id=collector_agent_id,
        inputs=[{"role": "user", "content": json.dumps(artefact_with_name)}],
    )
 
    profile_text = ""
 
    for output in response.outputs:
        if output.type == "message.output":
            if isinstance(output.content, str):
                profile_text = output.content
            elif isinstance(output.content, list):
                for chunk in output.content:
                    if hasattr(chunk, "text"):
                        profile_text += chunk.text
 
    # Guarantee the name is in the profile
    if agent_name not in profile_text:
        profile_text = (
            f"Your name is {agent_name}. "
            f"Always refer to yourself as {agent_name}.\n\n"
            + profile_text
        )
 
    return profile_text

def find_artefact_by_title(dataset: list, title: str) -> dict:
    """Find a specific artefact in the dataset by title."""
    title_lower = title.lower()
    for item in dataset:
        item_title = item.get("title", "").lower()
        if title_lower in item_title or item_title in title_lower:
            return item
    return None
 
 
def load_cache() -> dict:
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    return {}
 
 
def save_cache(cache: dict):
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)
 

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

# Group artefacts — use existing images, just generate profiles
def generate_group_agents():
    """
    Generate cached profiles for the 2 group project artefacts.
    Uses existing group images — profile generation only.
    Goes through the same Collector pipeline as KH artefacts.
    """
    print("\nGenerating group project agents...")
    print("(Profile only — using existing group images)\n")
 
    dataset = load_dataset()
    cache   = load_cache()
 
    for group_item in GROUP_ARTEFACTS:
        cache_key  = group_item["cache_key"]
        title      = group_item["title"]
        agent_name = group_item["agent_name"]
        image_url  = group_item["image_url"]
 
        if cache_key in cache:
            print(f"✅ Already cached: {title} ({agent_name}) — skipping\n")
            continue
 
        print(f"Generating: {title}")
        print(f"  Character : {agent_name}")
        print(f"  Image     : {image_url} (existing)")
 
        artefact_data = find_artefact_by_title(dataset, title)
        if not artefact_data:
            print(f"  ❌ Not found in dataset: {title}\n")
            continue
 
        artefact = {
            "title":            artefact_data.get("title", title),
            "url":              artefact_data.get("url", ""),
            "summary":          artefact_data.get("summary", ""),
            "current_location": artefact_data.get("current_location", ""),
            "materials":        artefact_data.get("materials", ""),
            "origin":           artefact_data.get("origin", ""),
            "culture":          artefact_data.get("culture", ""),
            "period":           artefact_data.get("period", ""),
            "discovery_site":   artefact_data.get("discovery_site", ""),
            "dimensions":       artefact_data.get("dimensions", ""),
            "categories":       artefact_data.get("categories", ""),
            "infobox_raw":      artefact_data.get("infobox_raw", "{}"),
        }
 
        try:
            # Profile only — no image generation
            profile = generate_profile_only(artefact, agent_name)
 
            cache[cache_key] = {
                "title":              title,
                "agent_name":         agent_name,
                "artefact":           artefact,
                "profile":            profile,
                "image_url":          image_url,   # ← existing group image
                "existing_character": agent_name,
            }
 
            save_cache(cache)
            print(f"  ✅ Done! Profile: ✅  Image: existing ✅\n")
 
        except Exception as e:
            print(f"  ❌ Failed: {e}\n")
 
    print(f"{'='*60}")
    print(f"✅ Group agents: {sum(1 for g in GROUP_ARTEFACTS if g['cache_key'] in cache)}/{len(GROUP_ARTEFACTS)} cached")
    print(f"Saved to: {CACHE_FILE}")
    print(f"{'='*60}")
 
if __name__ == "__main__":
    generate_all_agents()
    generate_group_agents()