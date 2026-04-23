# ============================================================
# consistency_guard.py
# Challenge #2 — Maintaining Profile Consistency
#
# Prevents the agent from drifting away from its character
# profile as conversations grow longer by periodically
# reinjecting the profile into the conversation history.
# ============================================================

from typing import List, Dict

# Reinject the profile every N visitor turns
REINJECT_EVERY_N_TURNS = 8

# Profile reminder injected into the conversation
REINJECT_TEMPLATE = (
    "[PROFILE REMINDER] You are still the character described below. "
    "Stay fully in character — your name, background, personality, and knowledge "
    "scope must remain consistent with this profile throughout the conversation.\n\n"
    "{profile}"
)


def should_reinject(turn_count: int) -> bool:
    """
    Returns True if the profile should be reinjected at this turn.
    Called before each Mistral API call.
    """
    return turn_count > 0 and turn_count % REINJECT_EVERY_N_TURNS == 0


def build_reinject_message(profile: str) -> Dict[str, str]:
    """
    Build a system-style user message that reinjecting the profile
    into the conversation as a reminder.
    """
    return {
        "role": "user",
        "content": REINJECT_TEMPLATE.format(profile=profile)
    }


def reinject_profile(
    history: List[Dict[str, str]],
    profile: str,
    turn_count: int
) -> List[Dict[str, str]]:
    """
    If it's time to reinject, insert a profile reminder message
    just before the latest user message (second to last entry).

    Returns the updated history.
    """
    if not should_reinject(turn_count):
        return history

    reminder = build_reinject_message(profile)

    # Insert the reminder before the last user message
    if len(history) >= 1:
        history = history[:-1] + [reminder] + [history[-1]]
    else:
        history = [reminder] + history

    return history


def check_drift(
    response: str,
    profile: str,
    character_name: str
) -> bool:
    """
    Basic drift detection — checks if the agent's response
    still references its character name or key profile terms.

    Returns True if drift is detected (name missing from response).
    """
    if not character_name:
        return False

    name_lower     = character_name.lower()
    response_lower = response.lower()

    # Extract first name for a looser check
    first_name = name_lower.split()[0] if name_lower.split() else ""

    return first_name not in response_lower and name_lower not in response_lower