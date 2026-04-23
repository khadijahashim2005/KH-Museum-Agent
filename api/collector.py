# ============================================================
# collector.py
# Step 1: Takes artefact data and generates a digital
# character profile using the Collector agent
# ============================================================

import os
import json
from mistralai.client import Mistral
from dotenv import load_dotenv

load_dotenv()


def generate_profile(artefact: dict) -> dict:
    """Generate character profile and extract image URL using Collector agent."""
    client             = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))
    collector_agent_id = os.getenv("COLLECTOR_AGENT_ID")

    response = client.beta.conversations.start(
        agent_id=collector_agent_id,
        inputs=[{
            "role":    "user",
            "content": json.dumps(artefact)
        }],
    )

    profile_text = ""
    image_url    = None

    for output in response.outputs:
        if output.type == "message.output":
            if isinstance(output.content, str):
                profile_text = output.content
            elif isinstance(output.content, list):
                for chunk in output.content:
                    if hasattr(chunk, "text"):
                        profile_text += chunk.text
                    elif hasattr(chunk, "file_id"):
                        image_url = get_image_url(client, chunk.file_id)

    return {
        "profile":   profile_text,
        "image_url": image_url
    }


def get_image_url(client: Mistral, file_id: str) -> str:
    """Get signed URL for a generated image."""
    try:
        response = client.files.get_signed_url(file_id=file_id)
        return response.url
    except Exception as e:
        print(f"Could not get image URL: {e}")
        return None