# ============================================================
# main.py
# Flask backend for KH Museum Agent
# Connects Collector → Interactor → Evaluator pipeline
#
# Endpoints:
# POST /init-agent         - Generate character from artefact
# POST /evaluate-agent     - Evaluate agent performance
# POST /init-conversation  - Start visitor conversation
# POST /response           - Continue visitor conversation
# ============================================================

import os
import json
import re
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
from collector import generate_profile
from interactor import Interactor

load_dotenv()

app = Flask(__name__)
CORS(app)

# Global storage for active sessions
sessions = {}

# Path to pre-generated agent cache
CACHE_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "cached_agents.json"
)


def load_cache() -> dict:
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    return {}


def extract_name_from_profile(profile: str) -> str:
    """Extract character name from profile JSON string."""
    try:
        data = json.loads(profile)
        if isinstance(data, dict) and "name" in data:
            return data["name"]
    except Exception:
        pass
    match = re.search(r'"name"\s*:\s*"([^"]+)"', profile)
    if match:
        return match.group(1)
    return None


@app.route("/")
def index():
    return send_from_directory("../frontend", "index.html")


@app.route("/init-conversation", methods=["POST"])
def init_conversation():
    try:
        data        = request.get_json()
        agent       = data.get("agent", "Museum Guide")
        storyname   = data.get("storyname", "museum-experience")
        event_index = int(data.get("event_index", 0))

        cache_key = f"{storyname}_{event_index}"
        cache     = load_cache()

        if cache_key in cache:
            print(f"Cache hit for '{cache_key}' — skipping generation")
            cached             = cache[cache_key]
            artefact           = cached["artefact"]
            profile            = cached["profile"]
            image_url          = cached["image_url"]
            existing_character = cached.get("existing_character")
        else:
            print(f"Cache miss for '{cache_key}' — generating live...")
            artefact           = load_artefact(storyname, event_index)
            existing_character = artefact.pop("existing_character", None)
            result             = generate_profile(artefact)
            profile            = result["profile"]
            image_url          = result["image_url"]

        if existing_character:
            profile = f"Your name is {existing_character}.\n\n" + profile

        # Extract name from profile to send to frontend
        character_name = extract_name_from_profile(profile)
        if existing_character:
            character_name = existing_character

        interactor  = Interactor(profile)
        first_reply = interactor.start()

        session_id = f"{storyname}_{event_index}_{agent}"
        sessions[session_id] = {
            "artefact":         artefact,
            "profile":          profile,
            "interactor":       interactor,
            "agent":            agent,
            "image_url":        image_url,
            "character_name":   character_name,
            "character_source": "existing" if existing_character else "generated"
        }

        return jsonify({
            "response":        first_reply,
            "conversation_id": session_id,
            "image_url":       image_url,
            "character_name":  character_name   # ✅ returned to frontend
        })

    except Exception as e:
        print(f"Error in init_conversation: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/response", methods=["POST"])
def response():
    try:
        data            = request.get_json()
        user_message    = (data.get("response") or "").strip()
        conversation_id = data.get("conversation_id")

        if not conversation_id or conversation_id not in sessions:
            return jsonify({"error": "Session not found"}), 404
        if not user_message:
            return jsonify({"error": "Empty message"}), 400

        interactor = sessions[conversation_id]["interactor"]
        reply      = interactor.chat(user_message)

        return jsonify({"response": reply, "conversation_id": conversation_id})

    except Exception as e:
        print(f"Error in response: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/evaluate-agent", methods=["POST"])
def evaluate_agent():
    try:
        data            = request.get_json()
        conversation_id = data.get("conversation_id")

        if conversation_id not in sessions:
            return jsonify({"error": "Session not found"}), 404

        session = sessions[conversation_id]
        from evaluation_pipeline.run_evaluation import run_full_evaluation
        results = run_full_evaluation(session["interactor"], session["artefact"])

        return jsonify({
            "status":          "success",
            "conversation_id": conversation_id,
            "evaluation":      results
        })

    except Exception as e:
        print(f"Error in evaluate_agent: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/agent-images/<path:filename>")
def agent_images(filename):
    """Serve locally downloaded agent images."""
    images_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data", "images"
    )
    return send_from_directory(images_dir, filename)

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "running"})


def load_artefact(storyname: str, event_index: int) -> dict:
    """Fallback: load artefact from AutoGame-copy event.json."""
    event_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "..", "AutoGame-copy", "frontend", "public", "story",
        storyname, "event.json"
    )
    if not os.path.exists(event_path):
        raise FileNotFoundError(f"event.json not found for story: {storyname}")

    with open(event_path, "r") as f:
        data = json.load(f)

    events = data.get("event", [])
    if not events:
        raise ValueError(f"No events found in event.json for story: {storyname}")
    if event_index >= len(events):
        raise ValueError(f"Event index {event_index} out of range.")

    event    = events[event_index]
    artifact = event.get("artifact", {})
    chars    = event.get("character", [])

    return {
        "title":              artifact.get("name", "Unknown"),
        "summary":            artifact.get("description", ""),
        "current_location":   artifact.get("current_location", ""),
        "materials":          artifact.get("material", ""),
        "origin":             artifact.get("origin", ""),
        "created":            artifact.get("date", ""),
        "infobox_raw":        json.dumps(artifact),
        "existing_character": chars[0] if chars else None
    }


if __name__ == "__main__":
    print("Starting KH Museum Agent API...")
    print(f"Cache: {'✅' if os.path.exists(CACHE_FILE) else '❌ Not found — will generate live'}")
    print("  POST /init-conversation")
    print("  POST /response")
    print("  POST /evaluate-agent")
    app.run(host="0.0.0.0", port=5005, debug=True)