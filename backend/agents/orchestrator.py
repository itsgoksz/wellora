"""
Wellora Orchestrator v2
-----------------------
Main AI pipeline with voice generation, interruptible dialogue,
and improved conversational realism.

Flow:
  User → classify → extract → generate companion response → generate voice
  → return { text, audio_url, structured_data }
"""

from sqlalchemy.orm import Session
from .classifier import classify_intent
from .extractor import extract_food
from .memory import build_short_term_context, build_meal_context, get_long_term_insights, update_habit_streak, get_semantic_context
from .companion import generate_companion_response, generate_followup_question
from .conversation_style import get_voice_directives
from .voicebox_service import generate_voice
from core.events import bus
import models
import asyncio


# --- Async Event Handlers ---
@bus.subscribe("HABIT_UPDATE")
def handle_habit_update(user_id: int, habit_name: str):
    from database import SessionLocal
    db = SessionLocal()
    try:
        update_habit_streak(user_id, habit_name, db)
        print(f"[EventBus] Habit '{habit_name}' updated for user {user_id}")
    finally:
        db.close()

@bus.subscribe("EMOTION_LOGGED")
def handle_emotion_logged(user_id: int, tone: str):
    # In a full system, we would calculate moving averages of tone here
    print(f"[EventBus] Emotion '{tone}' logged for user {user_id}")


def should_use_semantic_memory(message: str) -> bool:
    """
    Context Confidence Routing.
    Only returns True if the user's message is referential, vague, or explicitly 
    requests their regular/preferred choices. Returns False for fresh authoritative statements.
    """
    msg = message.lower()
    
    # 1. High-confidence referential keywords
    REFERENTIAL_PATTERNS = [
        "usual", "same as", "regular", "like yesterday", 
        "the normal", "as yesterday", "as usual", "standard",
        "habit", "normally", "preferred"
    ]
    if any(p in msg for p in REFERENTIAL_PATTERNS):
        return True
        
    # 2. Check for possessive "my [food]" referential pattern, e.g. "my coffee", "my breakfast"
    import re
    if re.search(r"\bmy\s+[a-z]+", msg):
        return True
        
    # Default to False for authoritative statements (e.g. "I had 2 dosas")
    return False


def is_fresh_logging_declaration(message: str, is_resolved: bool = True) -> bool:
    """
    Checks if a user message is a fresh authoritative food logging statement
    (e.g., "I had 2 dosas", "I ate a banana", "For breakfast 2 idlis", "2 dosas")
    which signals a conversational interruption/new meal session.
    """
    if not is_resolved:
        return False  # Never wipe context during an active, unresolved follow-up!

    msg_clean = message.lower().strip()
    FRESH_LOGGING_PATTERNS = [
        "i had", "i ate", "i drank", "i logged", "for breakfast", 
        "for lunch", "for dinner", "today i", "yesterday i", 
        "i've had", "i have had", "had a", "ate a"
    ]
    if any(pat in msg_clean for pat in FRESH_LOGGING_PATTERNS):
        return True
        
    # Check if it starts with a number followed by a word (e.g. "2 dosas", "1 coffee")
    if is_resolved:
        import re
        if re.match(r'^\d+\s+[a-z]+', msg_clean):
            return True
        
    return False


def is_previous_meal_resolved(user_id: int, db: Session) -> bool:
    """
    Pure conversation-based Dialogue State Tracking.
    If Wellora's last response was a resolved confirmation (no question mark),
    the previous meal logging session is closed and we start fresh.
    """
    last_assistant_msg = db.query(models.ConversationHistory).filter(
        models.ConversationHistory.user_id == user_id,
        models.ConversationHistory.role == "assistant"
    ).order_by(models.ConversationHistory.created_at.desc(), models.ConversationHistory.id.desc()).first()
    
    if not last_assistant_msg:
        return True  # No history yet, start fresh
        
    content = last_assistant_msg.content
    # If the last response contained a question mark or the follow-up emoji, it was an active follow-up!
    has_question = "?" in content or "🌸" in content
    return not has_question


def _is_topic_change_interruption(message: str, is_resolved: bool) -> bool:
    """
    Detect if a new food statement arrives during an unresolved follow-up.
    If so, the old follow-up chain should be abandoned immediately.
    
    This handles the case where:
    - Wellora: "What kind of dosa was that?"
    - User: "I had 3 chapatis for lunch" (new meal entirely — abandon dosa follow-up)
    """
    if is_resolved:
        return False  # No active follow-up to interrupt
    
    msg_clean = message.lower().strip()
    # A new meal declaration during an active follow-up = topic change
    INTERRUPTION_PATTERNS = [
        "for breakfast", "for lunch", "for dinner",
        "for snack", "for evening"
    ]
    return any(pat in msg_clean for pat in INTERRUPTION_PATTERNS)


from .food_db import lookup_food

def extract_food_name_from_query(query: str) -> str:
    """
    Extracts the potential food name subject from a user's question.
    """
    q = query.lower()
    patterns = [
        r"how many calories (does|do|is|are in|in|of)?",
        r"how much (calories|calorie|protein|carb|carbs|fat|fats|fiber|fibre) (is|are|does|in|of)?",
        r"what is the (calorie|calories|nutrition|nutritional value) (of|in)?",
        r"what are the (calories|nutrition) (of|in)?",
        r"calories in", r"calorie in", r"calories of", r"calorie of",
        r"nutrition in", r"nutrition of",
        r"tell me about", r"information on", r"info on"
    ]
    import re
    # Remove punctuation first to avoid regex boundary errors and clean the string
    q = re.sub(r"[?.,!]", "", q)
    for pat in patterns:
        q = re.sub(pat, "", q)
    for word in ["have", "has", "contain", "contains", "about", "a", "an", "the"]:
        q = re.sub(r"\b" + word + r"\b", "", q)
    return q.strip()


async def process_user_message(message: str, user_id: int, db: Session):
    """
    Wellora AI Pipeline v2:
    1. Memory Retrieval (Short + Long)
    2. Intent Classification
    3. Interruptible Follow-Up Check
    4. Structured Extraction
    5. Companion Generation
    6. Voice Generation (non-blocking, graceful fallback)
    7. Return { text, audio_url, structured_data }
    """
    
    # 1. Memory
    short_term_memory = build_short_term_context(user_id, db, skip_last=True)
    meal_context = build_meal_context(user_id, db)
    long_term_insights = get_long_term_insights(user_id, db)

    
    # 2. Intent & Emotion Classification
    intent, emotional_tone = classify_intent(message, context=short_term_memory)
    print(f"[Wellora] Intent: {intent} | Tone: {emotional_tone}")

    # Fire background emotion tracking event
    asyncio.create_task(bus.publish("EMOTION_LOGGED", user_id=user_id, tone=emotional_tone))
    
    # Get voice directives based on emotional state
    voice_directives = get_voice_directives(emotional_tone)
    
    extracted_data = {"intent": intent, "emotional_tone": emotional_tone}
    instructions = ""
    audio_url = None

    # 3. Route by intent
    if intent == "food_log":
        # Check for topic change interruption — abandon old follow-up if user starts a new meal
        is_resolved = is_previous_meal_resolved(user_id, db)
        is_interruption = _is_topic_change_interruption(message, is_resolved)
        
        if is_interruption:
            print("[Wellora] Topic change detected — abandoning previous follow-up chain")
            is_resolved = True  # Force fresh context
        
        # Determine extractor context
        extractor_context = short_term_memory
        if is_resolved or is_fresh_logging_declaration(message, is_resolved):
            print("[Wellora] Episodic Memory Cleared: New fresh log or previous meal was resolved.")
            extractor_context = ""
        
        # Fetch semantic preferences (e.g., "usual coffee is filter coffee")
        semantic_context = ""
        if should_use_semantic_memory(message):
            semantic_context = get_semantic_context(user_id, db, category="food_preference")
            print(f"[Wellora] Semantic Memory Routing: ON. Context: '{semantic_context}'")
        else:
            print("[Wellora] Semantic Memory Routing: OFF (Authoritative Statement)")
        
        data = extract_food(message, context=extractor_context, semantic_context=semantic_context)
        extracted_data.update(data)

        
        if data.get("needs_followup"):
            # The extractor returns a structured intent like "ask_dosa_type"
            # We route it through the companion LLM for natural, dynamic phrasing
            followup_intent = data.get("followup_question") or "ask_more_details"
            
            # Map structured intents to companion instructions
            FOLLOWUP_INSTRUCTIONS = {
                "ask_dosa_type": "Ask the user what kind of dosa they had (e.g., plain, masala, rava). Keep it short and natural — one sentence.",
                "ask_biryani_type": "Ask the user if it was veg, chicken, or mutton biryani. Keep it short and natural — one sentence.",
                "ask_side_dish": "Ask if they had any side dishes like chutney, sambar, or anything else with their meal. Keep it casual and brief.",
                "ask_chutney_type": "Ask what kind of chutney it was — coconut, tomato, mint, etc. Keep it natural and short.",
                "ask_chutney_servings": "Ask roughly how many servings of chutney they had. Keep it conversational and brief.",
                "ask_coffee_details": "Ask whether it was a regular coffee mug or a small cup, and how many they had. Keep it natural.",
                "ask_more_details": "Ask the user to tell you a bit more about what they ate. Be brief and natural.",
            }
            
            instruction = FOLLOWUP_INSTRUCTIONS.get(followup_intent, FOLLOWUP_INSTRUCTIONS["ask_more_details"])
            
            # Generate through focused companion for natural follow-up questions
            response_text = generate_followup_question(
                message=message,
                short_term_memory=short_term_memory,
                instruction=instruction
            )
            
            # Safety: ensure 🌸 is present (state detection depends on it)
            if "🌸" not in response_text:
                response_text = response_text.rstrip('.!') + " 🌸"
            # Safety: ensure it contains a question mark
            if "?" not in response_text:
                response_text = response_text.rstrip() + "?"
                if "🌸" not in response_text:
                    response_text += " 🌸"
            
            # Generate voice for the follow-up question (non-blocking)
            audio_url = await generate_voice(response_text, speed=voice_directives["speed"])
            
            extracted_data["audio_url"] = audio_url
            return response_text, extracted_data

        else:
            # Confident extraction — save each meal as a separate entry to DB!
            meals_list = data.get("meals", [])
            has_alcohol = False
            for m in meals_list:
                m_norm = ", ".join(m.get("normalized_foods", []))
                m_form = ", ".join(m.get("formatted_foods", [])) if m.get("formatted_foods") else m_norm
                m_type = m.get("meal_type") or "snack"
                if not m_type or m_type.strip() == "":
                    m_type = "snack"

                from .classifier import ALCOHOL_KEYWORDS
                is_alc = any(word in m_norm.lower() or word in m_form.lower() for word in ALCOHOL_KEYWORDS)
                if is_alc:
                    has_alcohol = True

                meal_entry = models.MealEntry(
                    user_id=user_id,
                    original_text=m_form,
                    normalized_foods=m_norm,
                    meal_type=m_type,
                    calories=m.get("calories"),
                    protein=m.get("protein"),
                    carbs=m.get("carbs"),
                    fats=m.get("fats"),
                    fibre=m.get("fibre", 0.0),
                    confidence_score=data.get("confidence", 1.0),
                    needs_followup=False,
                    is_alcohol=is_alc
                )
                print(f"[Orchestrator DB] Adding MealEntry: {m_form} (user_id={user_id}, cal={m.get('calories')}, is_alcohol={is_alc})")
                db.add(meal_entry)
            db.commit()
            print(f"[Orchestrator DB] Committed successfully! Total meals count in session: {db.query(models.MealEntry).count()} session={id(db)}")
            
            # Publish event instead of blocking to update habits
            asyncio.create_task(bus.publish("HABIT_UPDATE", user_id=user_id, habit_name="logging_meals"))
            
            # Format the companion instructions to acknowledge the meals naturally
            meal_descriptions = []
            for m in meals_list:
                m_form = ", ".join(m.get("formatted_foods", []))
                meal_descriptions.append(f"{m_form}")
                
            desc_str = " and ".join(meal_descriptions)
            if has_alcohol:
                instructions = (
                    f"The user successfully logged {desc_str}. "
                    f"COMPANION_MODE: minimal. Acknowledge this extremely concisely, naturally, and warmly. "
                    f"Suggest having some water alongside it in a gentle, warm, completely non-judgmental and realistic tone. "
                    f"Example: 'Logged your Budweiser 🌿 Maybe have some water alongside it too.' "
                    f"CRITICAL CONSTRAINT: Do NOT shame, guilt-trip, sound clinical, parental, or medical. "
                    f"Keep the calm, luxury brand identity intact. Exactly one short, realistic sentence."
                )
            else:
                instructions = (
                    f"The user successfully logged {desc_str}. "
                    f"COMPANION_MODE: minimal. Acknowledge this extremely concisely, naturally, and warmly. "
                    f"Example: 'Logged your {desc_str}! 🌿' or 'Nice, {desc_str} sounds great. 🌿'. "
                    f"Keep it to exactly one brief, subtle, realistic sentence. "
                    f"Do NOT over-comment, celebrate, or use emotional clichés like 'delightful' or 'brighten your day'."
                )

    
    elif intent == "hydration_log":
        # Robust hydration parsing supporting casual phrasing, volumes, containers, and liquids
        import re
        msg_lower = message.lower()
        
        ml = 0
        # 1. Match numeric expressions first, e.g. "500ml", "2 liters", "3 glasses", "1.5 l"
        num_match = re.search(r'(\d+(?:\.\d+)?)\s*(ml|milliliters|millilitres|glass|glasses|cup|cups|liter|liters|litre|litres|l|pint|pints|bottle|bottles)', msg_lower)
        if num_match:
            val = float(num_match.group(1))
            unit = num_match.group(2)
            if unit in ['ml', 'milliliters', 'millilitres']:
                ml = int(val)
            elif unit in ['glass', 'glasses', 'cup', 'cups']:
                ml = int(val * 250)
            elif unit in ['liter', 'liters', 'litre', 'litres', 'l']:
                ml = int(val * 1000)
            elif unit in ['bottle', 'bottles']:
                ml = int(val * 500)
            elif unit in ['pint', 'pints']:
                ml = int(val * 473)
        else:
            # 2. Check for singular casual expressions without explicit numbers
            if "half litre" in msg_lower or "half liter" in msg_lower or "half a litre" in msg_lower or "half a liter" in msg_lower:
                ml = 500
            elif "bottle" in msg_lower:
                ml = 500
            elif "glass" in msg_lower or "cup" in msg_lower:
                ml = 250
            elif "litre" in msg_lower or "liter" in msg_lower:
                ml = 1000
            elif "pint" in msg_lower:
                ml = 473
            elif "some water" in msg_lower or "hydrated a bit" in msg_lower or "glass of water" in msg_lower or "cup of water" in msg_lower:
                ml = 250
            else:
                ml = 250 # Default safe fallback
            
        wellness = models.WellnessEntry(user_id=user_id, type="water", value=float(ml), notes=message)
        db.add(wellness)
        db.commit()
        
        # Update habit async
        asyncio.create_task(bus.publish("HABIT_UPDATE", user_id=user_id, habit_name="hydration"))
        
        instructions = f"The user logged {ml}ml of water. Acknowledge it positively and briefly. Maybe say something like 'Nice, staying hydrated! 🌿'"
        
    elif intent == "sleep_log":
        # Extract hours
        import re
        hours = 0.0
        match = re.search(r'(\d+\.?\d*)\s*(hours|hrs|hr)', message.lower())
        if match:
            hours = float(match.group(1))
        
        wellness = models.WellnessEntry(user_id=user_id, type="sleep", value=hours, notes=message)
        db.add(wellness)
        db.commit()
        instructions = "The user mentioned sleep. Acknowledge it with empathy. If they slept poorly, be gentle and supportive."
        
    elif intent == "mood_log":
        wellness = models.WellnessEntry(user_id=user_id, type="mood", value=1.0, notes=message) # Value 1.0 just means entry exists
        db.add(wellness)
        db.commit()
        instructions = "The user shared their mood. Validate their feelings warmly. Never try to fix it, just be present."

    elif intent == "goal_setting":
        instructions = "The user is expressing a goal or preference. Validate their choice without judgment. Support them warmly. Reference what they actually said."

    elif intent == "wellness_question":
        # Check if it is a food/calorie lookup query
        food_candidate = extract_food_name_from_query(message)
        info = lookup_food(food_candidate) if food_candidate else None
        
        if info:
            # Provide exact database metrics to the companion LLM
            instructions = (
                f"The user is asking about the calorie/nutrition information for '{info['food_name']}'. "
                f"You MUST use this exact, authoritative database information in your response to ensure 100% accuracy:\n"
                f"- Food Name: {info['food_name']}\n"
                f"- Serving Size: 1 {info['serving_unit']}\n"
                f"- Calories: {info['calories']} kcal\n"
                f"- Protein: {info['protein']}g\n"
                f"- Carbs: {info['carbs']}g\n"
                f"- Fats: {info['fats']}g\n"
                f"- Fibre: {info.get('fibre', 0.0)}g\n\n"
                f"Respond in a deeply human, conversational, and warm tone. "
                f"State the calorie count clearly first, and proactively provide the macronutrient breakdown (protein, carbs, fats, and fiber) "
                f"so the user gets a comprehensive breakdown. Keep it engaging, natural, and brief (2-3 sentences)."
            )
        else:
            msg_lower = message.lower()
            if any(k in msg_lower for k in ["cramp", "period", "menstrua", "stomach ache", "stomach pain", "belly ache", "tummy ache", "bloat", "bloating", "nausea"]):
                # Cross-reference today's meals for active cramp-soothing ingredients
                eaten_today = []
                m_low = meal_context.lower()
                if "banana" in m_low: eaten_today.append("bananas")
                if "spinach" in m_low or "palak" in m_low: eaten_today.append("leafy greens")
                if "ginger" in m_low: eaten_today.append("ginger")
                if "yogurt" in m_low or "curd" in m_low or "dahi" in m_low: eaten_today.append("yogurt")
                if "salmon" in m_low or "fish" in m_low: eaten_today.append("fatty fish")
                if "chocolate" in m_low: eaten_today.append("dark chocolate")
                
                eaten_str = ""
                if eaten_today:
                    eaten_str = f"Mention that you noticed they already had {', '.join(eaten_today)} today, which is excellent for easing muscle contractions and cramps! "
                
                instructions = (
                    f"The user is asking for advice to soothe period cramps, stomach aches, or bloating. "
                    f"You MUST suggest anti-inflammatory and hydrating foods that relax muscles and reduce bloating:\n"
                    f"- Ginger: warm ginger tea to ease cramps/nausea (natural anti-inflammatory).\n"
                    f"- Bananas: high in potassium and B6 to prevent muscle spasms and bloating.\n"
                    f"- Magnesium-rich foods: Dark Chocolate (relaxes uterine muscles) and Leafy Greens (calcium & magnesium to prevent spasms, replenishes iron).\n"
                    f"- Fatty Fish: Omega-3s act as natural muscle relaxants and reduce inflammation.\n"
                    f"- Yogurt: Probiotics to soothe the stomach and calcium.\n\n"
                    f"CRITICAL DIRECTIVE: Acknowledge the symptom with deep, warm, realistic empathy. "
                    f"{eaten_str}"
                    f"Keep your response strictly to 2-3 sentences. Sound like a calm, smart friend texting, not clinical or preachy. Comfort them naturally."
                )
            else:
                instructions = f"The user is asking for advice. Give a SHORT, warm, practical tip. Reference their recent meals if relevant: {meal_context}. Do NOT lecture."
    
    elif intent == "progress_check":
        instructions = f"The user wants to know how they're doing. Summarize warmly based on: {meal_context}. Be encouraging."
    
    elif intent == "greeting":
        instructions = "The user said hi. Greet them warmly and ask what they've had to eat, or how they're feeling."
    
    else:  # casual_chat
        instructions = "Respond naturally and warmly like a caring friend. Keep it short."

    # Emotional Intelligence Adaptation
    if emotional_tone == "stressed" or emotional_tone == "sad":
        instructions += " The user seems stressed or down. Use extra empathy, very calm language, and keep it brief to not overwhelm them."
    elif emotional_tone == "tired":
        instructions += " The user is tired. Be gentle, encouraging, and don't ask heavy questions."
    elif emotional_tone == "motivated" or emotional_tone == "happy":
        instructions += " The user is in a great mood! Match their positive energy."

    # Background tasks for Semantic Memory building
    if "usual" in message.lower() or "always" in message.lower() or "favorite" in message.lower():
        # In a real production system, this would trigger a background LLM agent 
        # to parse the message and add a fact to the SemanticMemory table.
        pass

    # 4. Generate response via companion LLM
    companion_meal_context = "" if intent == "food_log" else (meal_context + "\n" + long_term_insights)
    response_text = generate_companion_response(
        message=message,
        short_term_memory=short_term_memory,
        meal_context=companion_meal_context,
        instructions=instructions
    )
    
    # 5. Generate voice (non-blocking, graceful fallback)
    audio_url = await generate_voice(response_text, speed=voice_directives["speed"])
    extracted_data["audio_url"] = audio_url
    
    return response_text, extracted_data
