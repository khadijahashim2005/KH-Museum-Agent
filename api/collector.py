# ============================================================
# collector.py
# Step 1: Takes artefact data and generates a digital 
# character profile using the Collector agent
# ============================================================
import os
import json
from mistralai.client import Mistral
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def generate_profile(artefact: dict) -> str:
    """
    Takes a structured artefact dictionary and returns
    a generated character profile string.
    """
    client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))
    collector_agent_id = os.getenv("COLLECTOR_AGENT_ID")

    response = client.beta.conversations.start(
        agent_id=collector_agent_id,
        inputs=[{
            "role": "user",
            "content": json.dumps(artefact)
        }],
    )

    # Find the MessageOutputEntry (skip ToolExecutionEntry)
    for output in response.outputs:
        if output.type == "message.output":
            # content can be a string or list of chunks
            if isinstance(output.content, str):
                return output.content
            elif isinstance(output.content, list):
                # extract text chunks
                text = ""
                for chunk in output.content:
                    if hasattr(chunk, 'text'):
                        text += chunk.text
                return text

    return ""

if __name__ == "__main__":
    # Test with Double-headed Serpent
    with open("data/double_headed_serpent.json", "r") as f:
        artefact = json.load(f)

    profile = generate_profile(artefact)
    print("Generated Profile:")
    print(profile)