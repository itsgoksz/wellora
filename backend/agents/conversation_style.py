"""
Wellora Conversation Style Engine
---------------------------------
Human rhythm system: variable responses, anti-repetition, phrase cooldowns,
acknowledgment diversity, and emotional pacing directives.

This module ensures Wellora never sounds like a chatbot, therapist, or
customer support agent. It sounds like a calm, grounded human companion.
"""

import random
import time
from collections import defaultdict
from datetime import datetime

# ── Phrase Cooldown Registry ─────────────────────────────────────────────
# Tracks recently used phrases to prevent repetition within a session.
_phrase_history: dict[int, list[tuple[str, float]]] = defaultdict(list)
_COOLDOWN_SECONDS = 300  # 5 minutes before a phrase can be reused


def _is_phrase_on_cooldown(user_id: int, phrase_key: str) -> bool:
    """Check if a phrase category was used recently for this user."""
    now = time.time()
    history = _phrase_history[user_id]
    # Clean expired entries
    _phrase_history[user_id] = [(p, t) for p, t in history if now - t < _COOLDOWN_SECONDS]
    return any(p == phrase_key for p, _ in _phrase_history[user_id])


def _mark_phrase_used(user_id: int, phrase_key: str):
    """Record that a phrase category was just used."""
    _phrase_history[user_id].append((phrase_key, time.time()))


# ── Acknowledgment Pools ────────────────────────────────────────────────
# Organized by category so we never repeat the same style back-to-back.

MEAL_LOGGED_CONFIRMATIONS = {
    "concise": [
        "Got it — {foods}. Logged.",
        "Logged {foods}.",
        "{foods} — noted.",
        "Added {foods}.",
        "All logged — {foods}.",
    ],
    "warm": [
        "Nice, {foods} sounds good. Logged 🌿",
        "{foods} — that's a solid {meal_type}. All set.",
        "Got it, {foods}! 🌿",
        "Sounds like a good {meal_type}. {foods} logged.",
    ],
    "casual": [
        "Cool, {foods}. Done.",
        "Okay, {foods}. Logged it.",
        "{foods}. Got you.",
        "Done — {foods}.",
    ],
}

INSTANT_ACKS = [
    "Got it…",
    "Okay, one sec…",
    "Let me log that…",
    "Sure, processing…",
    "Alright…",
]

SIDE_DISH_PROMPTS = [
    "Did you have it with anything on the side?",
    "Any sides with that?",
    "Did you have it with chutney, sambar, or anything?",
    "Was there any side dish?",
]

HYDRATION_ACKS = [
    "Nice, staying hydrated 🌿",
    "Good call on the water.",
    "Hydration logged.",
    "Water noted 🌿",
]

GREETING_RESPONSES = [
    "Hey! What have you had to eat today?",
    "Hi there — what's on the menu today?",
    "Hey! How's the day going so far?",
    "Hi! Anything to log today?",
]


# ── Response Diversity Engine ────────────────────────────────────────────

def pick_meal_confirmation(foods_str: str, meal_type: str, user_id: int = 1) -> str:
    """
    Select a non-repetitive meal confirmation message.
    Rotates through categories to prevent same-style confirmations.
    """
    # Find a category that isn't on cooldown
    available_categories = [
        cat for cat in MEAL_LOGGED_CONFIRMATIONS
        if not _is_phrase_on_cooldown(user_id, f"meal_confirm_{cat}")
    ]
    
    if not available_categories:
        # All on cooldown — reset and pick any
        available_categories = list(MEAL_LOGGED_CONFIRMATIONS.keys())
    
    category = random.choice(available_categories)
    template = random.choice(MEAL_LOGGED_CONFIRMATIONS[category])
    _mark_phrase_used(user_id, f"meal_confirm_{category}")
    
    return template.format(foods=foods_str, meal_type=meal_type)


def pick_instant_ack(user_id: int = 1) -> str:
    """Pick a quick acknowledgment for latency-masking while processing."""
    available = [
        ack for i, ack in enumerate(INSTANT_ACKS)
        if not _is_phrase_on_cooldown(user_id, f"instant_ack_{i}")
    ]
    if not available:
        available = INSTANT_ACKS
    
    ack = random.choice(available)
    idx = INSTANT_ACKS.index(ack)
    _mark_phrase_used(user_id, f"instant_ack_{idx}")
    return ack


def pick_greeting(user_id: int = 1) -> str:
    """Pick a varied greeting response."""
    return random.choice(GREETING_RESPONSES)


def pick_hydration_ack(user_id: int = 1) -> str:
    """Pick a varied hydration acknowledgment."""
    return random.choice(HYDRATION_ACKS)


# ── Emotional Pacing Directives ──────────────────────────────────────────

def get_voice_directives(emotional_tone: str) -> dict:
    """
    Returns voice and conversational pacing directives based on
    the user's detected emotional state.
    
    These directives control:
    - Speech speed hints (for TTS)
    - Response verbosity
    - Emoji usage
    - Tone warmth level
    """
    now = datetime.now()
    is_late_night = now.hour >= 22 or now.hour < 6
    
    base = {
        "speed": "normal",       # slow, normal, fast
        "verbosity": "concise",  # minimal, concise, conversational
        "emoji": True,
        "warmth": "neutral",     # cool, neutral, warm
    }
    
    if is_late_night:
        base["speed"] = "slow"
        base["verbosity"] = "minimal"
        base["emoji"] = False
        base["warmth"] = "cool"
        return base
    
    if emotional_tone in ("stressed", "sad", "anxious"):
        base["speed"] = "slow"
        base["verbosity"] = "concise"
        base["warmth"] = "warm"
        return base
    
    if emotional_tone == "tired":
        base["speed"] = "slow"
        base["verbosity"] = "minimal"
        base["warmth"] = "neutral"
        return base
    
    if emotional_tone in ("motivated", "happy", "excited"):
        base["speed"] = "normal"
        base["verbosity"] = "concise"
        base["warmth"] = "warm"
        return base
    
    return base


# ── Follow-Up Priority System ───────────────────────────────────────────

# Nutritional impact thresholds — only ask clarifying questions when the
# caloric difference between options is significant enough to matter.

FOLLOWUP_PRIORITY = {
    # HIGH PRIORITY — large caloric variance between options
    "biryani_type": {
        "priority": "high",
        "reason": "veg vs chicken biryani differs by ~200 kcal",
        "ask": True,
    },
    "sugar_coffee": {
        "priority": "high", 
        "reason": "sugar adds ~40-80 kcal per cup",
        "ask": True,
    },
    "quantity_ambiguity": {
        "priority": "high",
        "reason": "2 vs 4 dosas is 276 kcal difference",
        "ask": True,
    },
    
    # MEDIUM PRIORITY — moderate caloric variance
    "dosa_type": {
        "priority": "medium",
        "reason": "plain vs masala dosa differs by ~60 kcal",
        "ask": True,  # Still ask, but accept first answer without further probing
    },
    
    # LOW PRIORITY — minimal caloric impact, log approximate values
    "chutney_type": {
        "priority": "low",
        "reason": "coconut vs tomato chutney differs by ~20 kcal",
        "ask": False,  # Default to coconut chutney
    },
    "chutney_servings": {
        "priority": "low",
        "reason": "each serving is only ~67 kcal",
        "ask": False,  # Default to 1 serving
    },
    "side_dish": {
        "priority": "low",
        "reason": "side dishes are typically 50-100 kcal",
        "ask": False,  # Skip unless user mentions it
    },
    "coffee_container": {
        "priority": "low",
        "reason": "mug vs cup differs by ~50 kcal",
        "ask": False,  # Default to 1 regular cup
    },
}


def should_ask_followup(followup_type: str) -> bool:
    """
    Determine if a follow-up question should be asked based on
    nutritional priority. Returns False for low-impact clarifications
    to avoid interrogation-style conversations.
    """
    config = FOLLOWUP_PRIORITY.get(followup_type, {})
    return config.get("ask", False)


def get_followup_chain_limit() -> int:
    """
    Maximum number of consecutive follow-up questions before Wellora
    should log approximate values and move on.
    
    RULE: Never more than 1 clarification question per meal entry.
    Human conversations tolerate ambiguity.
    """
    return 1
