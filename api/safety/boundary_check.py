# ============================================================
# boundary_check.py
# Challenge #1 — Handling Out-of-Boundary Information
#
# Detects queries that fall outside the museum guide's role
# and returns a polite, in-character refusal that redirects
# the visitor back to the artefact topic.
# ============================================================

import re
from typing import Optional

# ── Out-of-scope pattern categories ────────────────────────
BOUNDARY_PATTERNS = [
    # Homework / academic tasks
    (r"\b(homework|assignment|essay|coursework|write\s+my|do\s+my|finish\s+my)\b",
     "homework"),

    # Medical advice
    (r"\b(medical\s+advice|diagnos|prescri|symptoms|treatment|medication|doctor)\b",
     "medical"),

    # Legal advice
    (r"\b(legal\s+advice|lawsuit|sue|lawyer|attorney|court|illegal)\b",
     "legal"),

    # Harmful or violent content
    (r"\b(how\s+(to|do\s+i|can\s+i)\s+(make|build|create)\s+(a\s+)?(weapon|bomb|poison|drug)|hurt\s+someone|harm|kill)\b",
     "harmful"),

    # Political opinions
    (r"\b(political\s+(views?|opinion|party)|who\s+should\s+i\s+vote|democrat|republican|labour|tory)\b",
     "political"),

    # Personal / romantic
    (r"\b(are\s+you\s+real|do\s+you\s+love|will\s+you\s+marry|be\s+my\s+(girlfriend|boyfriend|friend))\b",
     "personal"),

    # Financial advice
    (r"\b(invest(ment|ing)?|stock\s+market|crypto|bitcoin|financial\s+advice|buy\s+shares)\b",
     "financial"),

    # Completely unrelated topics
    (r"\b(weather|sports|football|netflix|tiktok|instagram|recipe|cook(ing)?)\b",
     "off_topic"),
]

# ── Polite refusals per category — stays in character ──────
REFUSALS = {
    "homework": (
        "I appreciate your enthusiasm, but helping with homework is a little outside "
        "my expertise as a museum guide! What I can do is share fascinating facts about "
        "this artefact that might inspire your work. What would you like to know?"
    ),
    "medical": (
        "That's a question best directed to a medical professional — I'm afraid ancient "
        "artefacts are more my area! Shall we return to exploring the history and "
        "significance of what's on display here?"
    ),
    "legal": (
        "Legal matters are well beyond my knowledge as a museum guide. "
        "I'm much better placed to help you discover the stories behind this artefact. "
        "Is there something about it you'd like to explore?"
    ),
    "harmful": (
        "That's not something I'm able to help with. As a museum guide, my purpose "
        "is to educate and inspire curiosity about history and culture. "
        "Shall we get back to the fascinating story of this artefact?"
    ),
    "political": (
        "Political opinions are outside my role as a museum guide — I prefer to let "
        "the artefacts speak for themselves! There's plenty of fascinating history "
        "here to explore. What would you like to know?"
    ),
    "personal": (
        "I'm a museum guide, and while I love connecting with curious visitors, "
        "that's a little outside what I can offer! I'm here to bring history to life. "
        "What would you like to discover about this artefact?"
    ),
    "financial": (
        "Financial advice is definitely outside my expertise as a museum guide! "
        "What I can offer is something far more valuable — a window into the past. "
        "Shall we continue exploring this artefact?"
    ),
    "off_topic": (
        "That's a little outside my area as a museum guide! I'm here to help you "
        "explore and understand the remarkable artefacts in this collection. "
        "Is there something about this piece you'd like to know more about?"
    ),
}

DEFAULT_REFUSAL = (
    "That question falls a little outside my role as a museum guide. "
    "I'm best placed to help you explore the history, culture, and significance "
    "of the artefacts on display. What would you like to discover?"
)


def boundary_check(message: str) -> Optional[str]:
    """
    Check if a visitor message is out of scope.

    Returns a refusal string if the message is out of boundary,
    or None if it's fine to proceed.
    """
    message_lower = message.lower().strip()

    for pattern, category in BOUNDARY_PATTERNS:
        if re.search(pattern, message_lower, re.IGNORECASE):
            return REFUSALS.get(category, DEFAULT_REFUSAL)

    return None  # message is in scope — proceed normally


def is_out_of_scope(message: str) -> bool:
    """Convenience function — returns True if message is out of scope."""
    return boundary_check(message) is not None