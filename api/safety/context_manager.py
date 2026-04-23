# ============================================================
# context_manager.py
# Challenge #3 — Managing Conversation Length and Context Limits
#
# Keeps the conversation history within the 8k token limit
# by compressing older turns into a summary while preserving
# the profile and recent context.
# ============================================================

import os
from typing import List, Dict
from mistralai.client import Mistral
from dotenv import load_dotenv

load_dotenv()

# ── Token budget ─────────────────────────────────────────────
MAX_TOKENS        = 8000   # Mistral API hard limit
COMPRESSION_TARGET = 4000  # compress when we exceed this
RECENT_TURNS_KEEP = 4      # always keep the last N turns intact
CHARS_PER_TOKEN   = 4      # rough estimate: 1 token ≈ 4 characters

SUMMARY_PROMPT_TEMPLATE = """Summarise the following museum guide conversation in 3-5 sentences.
Preserve: the visitor's main questions, the guide's key answers, and any important facts mentioned.
Be concise but keep all factual details about the artefact.

Conversation:
{history_text}"""


def estimate_tokens(history: List[Dict[str, str]]) -> int:
    """
    Estimate total token count from conversation history.
    Uses character count / 4 as a rough approximation.
    """
    total_chars = sum(len(m.get("content", "")) for m in history)
    return total_chars // CHARS_PER_TOKEN


def needs_compression(history: List[Dict[str, str]]) -> bool:
    """Returns True if the history is approaching the token limit."""
    return estimate_tokens(history) > COMPRESSION_TARGET


def summarise_history(
    history: List[Dict[str, str]],
    profile_message: Dict[str, str]
) -> List[Dict[str, str]]:
    """
    Compress old conversation turns into a summary using Mistral.
    Always keeps:
      - The original profile message (index 0)
      - The last RECENT_TURNS_KEEP turns
    Summarises everything in between.
    """
    # Nothing to compress if history is short
    if len(history) <= RECENT_TURNS_KEEP + 2:
        return history

    # Split: profile + old turns + recent turns
    old_turns    = history[1 : -RECENT_TURNS_KEEP]   # skip profile, skip recent
    recent_turns = history[-RECENT_TURNS_KEEP:]

    if not old_turns:
        return history

    # Build text to summarise
    history_text = "\n".join(
        f"{m['role'].capitalize()}: {m['content']}"
        for m in old_turns
    )

    # Call Mistral to summarise
    try:
        client   = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))
        response = client.chat.complete(
            model="mistral-small-latest",
            messages=[{
                "role":    "user",
                "content": SUMMARY_PROMPT_TEMPLATE.format(history_text=history_text)
            }]
        )
        summary = response.choices[0].message.content.strip()
    except Exception as e:
        # If summarisation fails, just drop the old turns rather than crash
        print(f"Context compression failed: {e} — dropping old turns")
        summary = "Earlier parts of this conversation have been condensed."

    # Rebuild: profile → summary → recent turns
    summary_message = {
        "role":    "user",
        "content": f"[CONVERSATION SUMMARY] {summary}"
    }
    summary_ack = {
        "role":    "assistant",
        "content": "Thank you, I have the context of our earlier conversation."
    }

    compressed = [profile_message, summary_message, summary_ack] + recent_turns

    old_tokens  = estimate_tokens(history)
    new_tokens  = estimate_tokens(compressed)
    print(f"Context compressed: ~{old_tokens} → ~{new_tokens} tokens")

    return compressed


def manage_context(
    history: List[Dict[str, str]],
    profile: str
) -> List[Dict[str, str]]:
    """
    Main entry point — call before each Mistral API call.
    Compresses history if token budget is exceeded.

    Returns the (possibly compressed) history.
    """
    if not needs_compression(history):
        return history

    # The profile message is always the first entry
    profile_message = history[0] if history else {
        "role":    "user",
        "content": f"Here is your profile:\n{profile}"
    }

    return summarise_history(history, profile_message)