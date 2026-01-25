"""
Enum definitions for review system

Defines valid intention tags for the dual-track review system:
- Medical intentions (pain relief, sleep, anxiety, etc.)
- Mood/Wellness intentions (socializing, creativity, focus, etc.)
"""
from enum import Enum


class MedicalIntention(str, Enum):
    """Medical use cases for cannabis products"""
    PAIN = "pain"
    INSOMNIA = "insomnia"
    ANXIETY = "anxiety"
    NAUSEA = "nausea"
    SPASMS = "spasms"


class MoodIntention(str, Enum):
    """Mood and wellness use cases for cannabis products"""
    SOCIALIZING = "socializing"
    CREATIVITY = "creativity"
    DEEP_RELAXATION = "deep_relaxation"
    FOCUS = "focus"
    POST_WORKOUT = "post_workout"


# Helper dictionary for queries and validation
ALL_INTENTIONS = {
    "medical": [i.value for i in MedicalIntention],
    "mood": [i.value for i in MoodIntention]
}


def validate_intention(intention_type: str, intention_tag: str) -> bool:
    """
    Validate that an intention tag is valid for the given intention type.

    Args:
        intention_type: Either "medical" or "mood"
        intention_tag: Specific intention tag value

    Returns:
        True if valid, False otherwise
    """
    if intention_type not in ALL_INTENTIONS:
        return False
    return intention_tag in ALL_INTENTIONS[intention_type]
