from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
import json
import re
from .food_db import lookup_food

# Model: Gemma 3 4B (Optimized for JSON and Reasoning)
llm = ChatOllama(model="gemma3:4b", temperature=0.0)

def _parse_json_robustly(text: str) -> dict:
    text = text.strip()
    # Handle markdown code blocks
    markdown_match = re.search(r'```(?:json)?\s*([\s\S]+?)\s*```', text)
    if markdown_match:
        text = markdown_match.group(1).strip()
    
    # Try finding the first '{' and last '}'
    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end != -1:
        text = text[start:end+1]
        
    try:
        return json.loads(text)
    except Exception as e:
        print(f"[Extractor] Robust JSON parse error: {e}. Raw was: {text}")
        return {}

# Expert-Refined Prompt for Gemma 3 Architecture (Flat Objects Multi-Meal Extraction)
PROMPT_TEMPLATE = """<SYSTEM_INSTRUCTIONS>
You are a Professional Nutrition Data Scientist. Your task is to extract ALL food entries from a conversation and associate each food with its respective meal type (breakfast, lunch, dinner, or snack).

CRITICAL RULES:
1. ASSOCIATE MEALS: For each food item, identify which meal it belongs to.
2. COMPLETE MEAL STATE: You MUST include ALL foods mentioned in the ENTIRE conversation history, not just the latest message.
3. NO ADDITIONS: Do NOT add descriptions like "plain", "masala", "coconut", or "sambar" unless the User explicitly wrote them.
4. STATE RESOLUTION: When the conversation contains clarification Q&A (like asking "what kind of dosa" or "how many servings of chutney"), you MUST combine those answers with their respective items. For example, if the user said "3 dosas" earlier, then clarifies "masala", then adds "coconut chutney", and then clarifies "2 servings", you MUST combine them into "3 masala dosa" and "2 coconut chutney".
5. EVERY food mentioned by the user MUST appear in the output. If the user said "3 dosas" earlier and later clarified "rava dosa", output "3 rava dosa".
</SYSTEM_INSTRUCTIONS>

<EXAMPLES>
Example 1 - Simple:
User: "I had 2 dosas" -> {{"foods": [{{"food": "2 dosa", "meal_type": "snack"}}]}}

Example 2 - Multi-meal:
User: "I had 2 dosas for breakfast today with coconut chutney, for lunch I had 3 chapatis with rajma gravy" -> 
{{
  "foods": [
    {{"food": "2 dosa", "meal_type": "breakfast"}},
    {{"food": "1 coconut chutney", "meal_type": "breakfast"}},
    {{"food": "3 chapati", "meal_type": "lunch"}},
    {{"food": "1 rajma gravy", "meal_type": "lunch"}}
  ]
}}

Example 3 - Follow-up clarification (IMPORTANT):
User: I had 3 dosas for breakfast
Wellora: What kind of dosa was that?
User: rava dosa
Wellora: Did you have it with any side dish?
User: with coconut chutney
Wellora: How many servings of chutney?
User: 2 servings
-> {{"foods": [{{"food": "3 rava dosa", "meal_type": "breakfast"}}, {{"food": "2 coconut chutney", "meal_type": "breakfast"}}]}}

Example 4 - Multi-step follow-up clarification (IMPORTANT):
User: I had 3 dosas for breakfast
Wellora: What type of dosa did you have? 🌸
User: masala dosa
Wellora: And what did you have with them? 🌸
User: coconut chutney
Wellora: How much coconut chutney did you have? 🌸
User: 2 servings
-> {{"foods": [{{"food": "3 masala dosa", "meal_type": "breakfast"}}, {{"food": "2 coconut chutney", "meal_type": "breakfast"}}]}}
</EXAMPLES>

<CONVERSATION_HISTORY>
{transcript}
</CONVERSATION_HISTORY>

<USER_SEMANTIC_MEMORY>
{semantic_context}
</USER_SEMANTIC_MEMORY>

<OUTPUT_SPECIFICATION>
Return ONLY a valid JSON object. Include ALL foods from the entire conversation.
{{
  "foods": [
    {{
      "food": "quantity name",
      "meal_type": "string"
    }}
  ]
}}
</OUTPUT_SPECIFICATION>"""

prompt = PromptTemplate(template=PROMPT_TEMPLATE, input_variables=["transcript", "semantic_context"])

# ── Deterministic lists ─────────────────────────────────────
NEEDS_SIDE_CHECK = {"dosa", "idli", "vada", "parotta", "chapati", "roti", "naan", "puri", "poori", "uttapam"}
SIDE_KEYWORDS = {"sambar", "sambhar", "chutney", "dal", "dhal", "curry", "kurma", "sabzi", "podi", "chatni", "gravy"}
CHUTNEY_TYPES = ["coconut", "tomato", "mint", "pudina", "ginger", "garlic", "onion", "peanut", "plum", "kara", "red", "green"]
MODIFIERS = ["plain", "masala", "rava", "set", "wheat", "paneer", "chicken", "mutton", "veg", "egg"]

def _parse_qty_and_name(item: str) -> tuple[int, str]:
    match = re.match(r'^(\d+)\s+(.+)$', item.strip())
    if match:
        return int(match.group(1)), match.group(2).strip()
    return 1, item.strip()

def _process_single_meal(food_items: list[str], meal_type: str, user_only_text: str, is_multi_meal: bool = False) -> dict:
    """Apply ironclad guards, dedup, and lookup nutrition for a single meal."""
    # ── IRONCLAD ANTI-HALLUCINATION GUARDS ──
    verified_foods = []
    for item in food_items:
        qty, name = _parse_qty_and_name(item)
        n_low = name.lower()
        
        # 1. MODIFIER GUARD: Remove hallucinated adjectives (plain, masala, etc.)
        for mod in (MODIFIERS + CHUTNEY_TYPES):
            if mod in n_low and mod not in user_only_text:
                name = name.replace(mod, "").replace("  ", " ").strip()
                n_low = name.lower()

        # 2. SIDE DISH GUARD: Remove hallucinated side dishes (chutney, sambar, etc.)
        is_hallucinated_side = False
        if any(side in n_low for side in SIDE_KEYWORDS):
            if not any(kw in user_only_text for kw in SIDE_KEYWORDS if kw in n_low):
                is_hallucinated_side = True
        
        if not is_hallucinated_side:
            verified_foods.append(f"{qty} {name}")
    
    food_items = verified_foods

    # 3. MODIFIER PERSISTENCE
    for i, item in enumerate(food_items):
        qty, name = _parse_qty_and_name(item)
        n_low = name.lower()
        for mod in MODIFIERS:
            if mod in user_only_text and mod not in n_low:
                if "dosa" in n_low or "dosai" in n_low:
                    if mod in ["masala", "plain", "rava", "set", "wheat", "paneer", "chicken", "mutton", "veg"]:
                        food_items[i] = f"{qty} {mod} {name}"
                elif "biryani" in n_low or "pulao" in n_low:
                    if mod in ["chicken", "mutton", "veg", "beef", "prawn", "egg"]:
                        food_items[i] = f"{qty} {mod} {name}"

    # 3.5 DEDUPLICATION & QUANTITY MERGING
    merged_foods = {}
    for item in food_items:
        qty, name = _parse_qty_and_name(item)
        n_low = name.lower().strip()
        
        matched_key = None
        for key in list(merged_foods.keys()):
            if key in n_low or n_low in key:
                matched_key = key
                break
        
        if matched_key:
            specific_name = n_low if len(n_low) > len(matched_key) else matched_key
            max_qty = max(qty, merged_foods[matched_key])
            if specific_name != matched_key:
                del merged_foods[matched_key]
            merged_foods[specific_name] = max_qty
        else:
            merged_foods[n_low] = qty
            
    food_items = [f"{qty} {name}" for name, qty in merged_foods.items()]

    # 4. SIDE PERSISTENCE
    for side_kw in SIDE_KEYWORDS:
        if side_kw in user_only_text:
            existing_idx = -1
            for idx, f in enumerate(food_items):
                if side_kw in f.lower():
                    existing_idx = idx
                    break
            
            modifier = None
            if side_kw in ["chutney", "chatni"]:
                for t in CHUTNEY_TYPES:
                    if t in user_only_text:
                        modifier = t
                        break
            
            if existing_idx >= 0:
                existing_item = food_items[existing_idx]
                qty, name = _parse_qty_and_name(existing_item)
                if modifier and modifier not in name.lower():
                    food_items[existing_idx] = f"{qty} {modifier} {name}"
            else:
                # Only add new side dishes heuristically if it is NOT a multi-meal message
                # to prevent cross-meal side dish pollution.
                if not is_multi_meal:
                    resolved_side = f"1 {side_kw}"
                    if modifier:
                        resolved_side = f"1 {modifier} {side_kw}"
                    food_items.append(resolved_side)

    parsed = [_parse_qty_and_name(item) for item in food_items]
    
    # ── Nutrition Lookup ───────────────────────────
    total_cal, total_protein, total_carbs, total_fats, total_fibre = 0, 0.0, 0.0, 0.0, 0.0
    matched_names = []
    formatted_names = []
    for qty, name in parsed:
        info = lookup_food(name)
        if info:
            total_cal += info["calories"] * qty
            total_protein += info["protein"] * qty
            total_carbs += info["carbs"] * qty
            total_fats += info["fats"] * qty
            total_fibre += info.get("fibre", 0.0) * qty
            food_disp = info["food_name"]
            matched_names.append(food_disp)
        else:
            food_disp = name.strip().capitalize()
            matched_names.append(name)

        if qty > 1:
            if any(food_disp.lower().endswith(x) for x in ["dosa", "chapati", "idli", "roti", "poori", "puri", "parotta"]):
                formatted_names.append(f"{qty} {food_disp}s")
            else:
                formatted_names.append(f"{qty} {food_disp}")
        else:
            formatted_names.append(food_disp)

    return {
        "normalized_foods": matched_names,
        "formatted_foods": formatted_names,
        "meal_type": meal_type,
        "calories": total_cal,
        "protein": round(total_protein, 1),
        "carbs": round(total_carbs, 1),
        "fats": round(total_fats, 1),
        "fibre": round(total_fibre, 1),
    }

def extract_food(message: str, context: str = "", semantic_context: str = ""):
    try:
        # ── LOCAL LLM INSTANTIATION TO PREVENT STATE POLLUTION ──
        llm = ChatOllama(model="gemma3:4b", temperature=0.0)

        # ── TRANSCRIPT PREPARATION ──
        history_lines = [line for line in context.strip().split("\n") if "User:" in line or "Wellora:" in line]
        # Use more history lines for follow-up chains to ensure full meal reconstruction
        transcript = "\n".join(history_lines[-10:] + [f"User: {message}"]).strip()

        # ── LLM INVOCATION ──
        formatted_prompt = prompt.format(transcript=transcript, semantic_context=semantic_context)
        print("--- FORMATTED PROMPT SENT TO LLM ---")
        print(formatted_prompt)
        print("------------------------------------")
        res = llm.invoke(formatted_prompt)
        print("--- EXTRACTOR RAW LLM RESPONSE ---")
        print(res.content)
        print("----------------------------------")
        raw = _parse_json_robustly(res.content)
        
        foods_raw = raw.get("foods", [])
        print("Foods Raw:", foods_raw)
        
        # Group raw foods by their extracted meal_type
        # ── FALLBACK: If LLM returned empty but there ARE foods in conversation ──
        if not foods_raw:
            print("[Extractor] WARNING: LLM returned empty. Attempting context-based recovery...")
            # Re-extract by building a simplified transcript with just user messages
            user_messages = [line.replace("User:", "").strip() for line in history_lines if "User:" in line]
            user_messages.append(message)
            combined_user_text = ". ".join(user_messages)
            retry_transcript = f"User: {combined_user_text}"
            retry_prompt = prompt.format(transcript=retry_transcript, semantic_context=semantic_context)
            print("--- RETRY PROMPT ---")
            print(retry_prompt)
            print("--------------------")
            retry_res = llm.invoke(retry_prompt)
            print("--- RETRY RAW RESPONSE ---")
            print(retry_res.content)
            print("--------------------------")
            retry_raw = _parse_json_robustly(retry_res.content)
            foods_raw = retry_raw.get("foods", [])
            print("Retry Foods Raw:", foods_raw)
        
        # Group raw foods by their extracted meal_type
        grouped_meals = {}
        for item in foods_raw:
            if isinstance(item, dict):
                f_text = item.get("food", "")
                m_type = item.get("meal_type", "snack") or "snack"
                if m_type not in grouped_meals:
                    grouped_meals[m_type] = []
                grouped_meals[m_type].append(f_text)
            else:
                m_type = raw.get("meal_type", "snack") or "snack"
                if m_type not in grouped_meals:
                    grouped_meals[m_type] = []
                grouped_meals[m_type].append(item)

        user_only_text = " ".join([line.lower() for line in (history_lines + [f"User: {message}"]) if "User:" in line])

        processed_meals = []
        for m_type, foods in grouped_meals.items():
            # Map meal type if explicitly stated in text
            history_meal = None
            for line in (history_lines + [f"User: {message}"]):
                l = line.lower()
                if "breakfast" in l: history_meal = "breakfast"
                elif "lunch" in l: history_meal = "lunch"
                elif "dinner" in l: history_meal = "dinner"
            if m_type == "snack" and history_meal:
                m_type = history_meal
                
            processed = _process_single_meal(foods, m_type, user_only_text, is_multi_meal=(len(grouped_meals) > 1))
            processed_meals.append(processed)

        # ── Deterministic follow-up checks across all meals ──────────────────
        needs_followup = False
        followup_question = None

        # Get last assistant question to avoid repeating follow-up questions
        last_assistant_msg = ""
        for line in reversed(history_lines):
            if "wellora:" in line.lower():
                last_assistant_msg = line.lower()
                break

        # ONLY perform follow-up checks if there is at most one meal in processed_meals
        # (Bypass follow-ups for multi-meal logs to prevent interrupting detailed logs)
        meal_list_for_checks = processed_meals if len(processed_meals) <= 1 else []
        for meal in meal_list_for_checks:
            food_names = [name.lower() for name in meal["normalized_foods"]]
            
            # 1. Ambiguity Check (Main Food)
            for name in food_names:
                n_low = name.lower()
                if "dosa" in n_low or "dosai" in n_low:
                    if not any(t in user_only_text for t in ["masala", "plain", "rava", "semolina", "set", "wheat", "paneer", "chicken", "mutton", "veg"]):
                        needs_followup = True
                        followup_question = "ask_dosa_type"
                        break
                elif "biryani" in n_low or "pulao" in n_low:
                    if not any(t in user_only_text for t in ["chicken", "mutton", "veg", "beef", "prawn", "egg"]):
                        needs_followup = True
                        followup_question = "ask_biryani_type"
                        break
            
            # 2. Side Dish Check
            if not needs_followup:
                has_main_needing_side = any(any(base in name for base in NEEDS_SIDE_CHECK) for name in food_names)
                if has_main_needing_side:
                    has_side = any(any(side in name for side in SIDE_KEYWORDS) for name in food_names)
                    is_decline = any(kw in message.lower() for kw in ["no", "nope", "nothing", "just that", "thats it", "nah", "only", "none"])
                    if not has_side and not is_decline:
                        needs_followup = True
                        followup_question = "ask_side_dish"
            
            # 3. Chutney Ambiguity Check
            if not needs_followup:
                for name in food_names:
                    if "chutney" in name or "chatni" in name:
                        if not any(t in user_only_text for t in CHUTNEY_TYPES):
                            needs_followup = True
                            followup_question = "ask_chutney_type"
                            break

            # 4. Chutney Serving Clarification Check
            if not needs_followup:
                for name in food_names:
                    if "chutney" in name or "chatni" in name:
                        # Dynamic already asked detection based on conversation history keywords
                        already_asked = "chutney" in last_assistant_msg and any(x in last_assistant_msg for x in ["serving", "how many", "how much", "quantity", "amount", "scoop", "spoon", "bowl"])
                        if not already_asked:
                            import re
                            pattern = r'\b(\d+|one|two|three|four|five|six|seven|eight|nine|a\s+bowl|a\s+serving|bowl|serving|servings|bowls|spoons|cups|katoris|tbsp|tsp|plates)\b'
                            specified = bool(re.search(pattern, user_only_text))
                            if not specified:
                                needs_followup = True
                                followup_question = "ask_chutney_servings"
                                break

            # 5. Coffee Mug vs Tea Mug & Cups Check
            if not needs_followup:
                for name in food_names:
                    if "coffee" in name:
                        # Dynamic already asked detection based on coffee container keywords
                        already_asked = any(x in last_assistant_msg for x in ["coffee", "mug", "cup", "glass", "size", "how many"])
                        if not already_asked:
                            import re
                            has_container = any(x in user_only_text for x in ["mug", "cup", "glass"])
                            qty_pattern = r'\b(\d+|one|two|three|four|five|six|seven|eight|nine|a|an)\b'
                            has_qty = bool(re.search(qty_pattern, user_only_text))
                            specified = has_container or has_qty
                            if not specified:
                                needs_followup = True
                                followup_question = "ask_coffee_details"
                                break
            
            if needs_followup:
                break

        # If needs follow-up, reset calories to 0
        if needs_followup:
            for m in processed_meals:
                m["calories"] = 0

        # Build combined summary response for legacy compatibility
        all_normalized = []
        all_formatted = []
        all_meal_types = []
        total_cal = 0
        total_prot = 0.0
        total_carb = 0.0
        total_fat = 0.0
        total_fib = 0.0

        for m in processed_meals:
            all_normalized.extend(m["normalized_foods"])
            all_formatted.extend(m["formatted_foods"])
            if m["meal_type"] not in all_meal_types:
                all_meal_types.append(m["meal_type"])
            total_cal += m["calories"]
            total_prot += m["protein"]
            total_carb += m["carbs"]
            total_fat += m["fats"]
            total_fib += m["fibre"]

        return {
            "meals": processed_meals,
            "normalized_foods": all_normalized,
            "formatted_foods": all_formatted,
            "meal_type": ", ".join(all_meal_types) if all_meal_types else "snack",
            "calories": total_cal,
            "protein": round(total_prot, 1),
            "carbs": round(total_carb, 1),
            "fats": round(total_fat, 1),
            "fibre": round(total_fib, 1),
            "confidence": 0.95 if not needs_followup else 0.5,
            "needs_followup": needs_followup,
            "followup_question": followup_question,
        }
    except Exception as e:
        print(f"Extractor Error: {e}")
        return {
            "meals": [],
            "normalized_foods": [],
            "formatted_foods": [],
            "meal_type": "snack",
            "calories": 0,
            "protein": 0.0,
            "carbs": 0.0,
            "fats": 0.0,
            "fibre": 0.0,
            "confidence": 0.0,
            "needs_followup": False,
            "followup_question": None
        }
