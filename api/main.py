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
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from collector import generate_profile
from interactor import Interactor

load_dotenv()

app = Flask(__name__)
CORS(app)

# Global storage for active sessions
sessions = {}

@app.route("/init-agent", methods=["POST"])
def init_agent():
    """
    Step 1 + 2: Takes artefact data, generates profile 
    using Collector, initialises Interactor agent.
    """
    try:
        data = request.get_json()

        # Accept artefact from request or load from file
        if "artefact" in data:
            artefact = data["artefact"]
        else:
            with open("data/double_headed_serpent.json", "r") as f:
                artefact = json.load(f)

        print(f"Generating profile for: {artefact.get('title')}")

        # Step 1 - Collector generates profile
        profile = generate_profile(artefact)
        print("Profile generated!")

        # Step 2 - Initialise Interactor with profile
        interactor = Interactor(profile)
        first_reply = interactor.start()

        # Store session
        session_id = artefact.get("title", "default").replace(" ", "_").lower()
        sessions[session_id] = {
            "artefact": artefact,
            "profile": profile,
            "interactor": interactor,
            "image_id": None # image generation can be added later if needed
        }

        return jsonify({
            "status": "success",
            "session_id": session_id,
            "profile": profile,
            "first_reply": first_reply
        })

    except Exception as e:
        print(f"Error in init_agent: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/generate-image", methods=["POST"])
def generate_image_endpoint():
    """
    Separate endpoint for image generation.
    Called after init-agent so it doesn't slow down the main pipeline.
    """
    try:
        data = request.get_json()
        session_id = data.get("session_id")

        if session_id not in sessions:
            return jsonify({"status": "error", "message": "Session not found"}), 404

        profile = sessions[session_id]["profile"]

        from collector import generate_image
        image_id = generate_image(profile)

        sessions[session_id]["image_id"] = image_id

        return jsonify({
            "status": "success",
            "image_id": image_id
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/evaluate-agent", methods=["POST"])
def evaluate_agent():
    """
    Step 3: Evaluates the agent using hard and soft 
    knowledge tests.
    """
    try:
        data = request.get_json()
        session_id = data.get("session_id")

        if session_id not in sessions:
            return jsonify({"status": "error", "message": "Session not found"}), 404

        session = sessions[session_id]
        artefact = session["artefact"]
        profile = session["profile"]
        interactor = session["interactor"]

        # Import evaluator here to avoid circular imports
        from evaluator import Evaluator
        evaluator = Evaluator(artefact, profile, interactor)

        # Run hard knowledge evaluation
        print("Running hard knowledge evaluation...")
        hard_results = evaluator.evaluate_hard_knowledge()

        # Run soft knowledge evaluation
        print("Running soft knowledge evaluation...")
        soft_results = evaluator.evaluate_soft_knowledge()

        return jsonify({
            "status": "success",
            "session_id": session_id,
            "hard_knowledge": hard_results,
            "soft_knowledge": soft_results
        })

    except Exception as e:
        print(f"Error in evaluate_agent: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/init-conversation", methods=["POST"])
def init_conversation():
    """
    Start a visitor conversation with the agent.
    Uses existing session if available, creates new one if not.
    """
    try:
        data = request.get_json()
        session_id = data.get("session_id")

        if session_id not in sessions:
            return jsonify({"status": "error", "message": "Session not found. Call /init-agent first."}), 404

        session = sessions[session_id]
        interactor = session["interactor"]

        first_reply = interactor.start()

        return jsonify({
            "status": "success",
            "response": first_reply,
            "session_id": session_id
        })

    except Exception as e:
        print(f"Error in init_conversation: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/response", methods=["POST"])
def response():
    """
    Continue a visitor conversation.
    """
    try:
        data = request.get_json()
        session_id = data.get("session_id")
        visitor_message = data.get("message", "").strip()

        if not session_id or session_id not in sessions:
            return jsonify({"status": "error", "message": "Session not found"}), 404

        if not visitor_message:
            return jsonify({"status": "error", "message": "Empty message"}), 400

        session = sessions[session_id]
        interactor = session["interactor"]

        reply = interactor.chat(visitor_message)

        return jsonify({
            "status": "success",
            "response": reply,
            "session_id": session_id
        })

    except Exception as e:
        print(f"Error in response: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint"""
    return jsonify({"status": "running"})


if __name__ == "__main__":
    print("Starting KH Museum Agent API...")
    print("Endpoints:")
    print("  POST /init-agent         - Generate character from artefact")
    print("  POST /evaluate-agent     - Evaluate agent performance")
    print("  POST /init-conversation  - Start visitor conversation")
    print("  POST /response           - Continue visitor conversation")
    app.run(host="0.0.0.0", port=5004, debug=True)