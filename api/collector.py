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

COLLECTOR_INSTRUCTIONS = """For the given information about antique, please create a digital instructor's profile. 
Please make sure the instructor and antique should be related, include:
1) from the same culture background
2) have connection during the discovering
3) education purpose
4) be interesting to the child

The profile should be in json format, Include:
name, gender, age, summarisation of antique, additional information"""


def generate_profile(artefact: dict) -> str:
    """Generate character profile"""
    client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))

    response = client.chat.complete(
        model="mistral-small-latest",
        messages=[
            {"role": "system", "content": COLLECTOR_INSTRUCTIONS},
            {"role": "user", "content": json.dumps(artefact)}
        ],
        temperature=0.7,
        max_tokens=2048,
    )
    return response.choices[0].message.content


def generate_image(profile: str) -> str:
    """Generate character image, returns image file ID"""
    client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))
    collector_agent_id = os.getenv("COLLECTOR_AGENT_ID")

    prompt = f"Generate a portrait image of the museum digital instructor described in this profile: {profile[:500]}"

    response = client.beta.conversations.start(
        agent_id=collector_agent_id,
        inputs=[{"role": "user", "content": prompt}],
    )

    for output in response.outputs:
        if hasattr(output, 'content') and isinstance(output.content, list):
            for chunk in output.content:
                if hasattr(chunk, 'file_id'):
                    return chunk.file_id

    return None


if __name__ == "__main__":
    with open("data/double_headed_serpent.json", "r") as f:
        artefact = json.load(f)

    print("Generating profile...")
    profile = generate_profile(artefact)
    print("Profile generated!")
    print(profile)