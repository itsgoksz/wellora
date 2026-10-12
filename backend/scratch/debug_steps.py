import sys
import re
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from agents.extractor import MODIFIERS, CHUTNEY_TYPES, SIDE_KEYWORDS, _parse_qty_and_name
from agents.food_db import lookup_food

def test_meal_step_by_step():
    food_items = ["3 dosa", "1 coconut chutney"]
    user_only_text = "I had 3 dosas with coconut chutney for breakfast and 2 chapatis with rajma curry for lunch"
    
    print("Initial food_items:", food_items)
    
    # 1. MODIFIER GUARD
    verified_foods = []
    for item in food_items:
        qty, name = _parse_qty_and_name(item)
        n_low = name.lower()
        for mod in (MODIFIERS + CHUTNEY_TYPES):
            if mod in n_low and mod not in user_only_text:
                name = name.replace(mod, "").replace("  ", " ").strip()
                n_low = name.lower()
        
        # 2. SIDE DISH GUARD
        is_hallucinated_side = False
        if any(side in n_low for side in SIDE_KEYWORDS):
            if not any(kw in user_only_text for kw in SIDE_KEYWORDS if kw in n_low):
                is_hallucinated_side = True
        
        if not is_hallucinated_side:
            verified_foods.append(f"{qty} {name}")
    
    food_items = verified_foods
    print("After MODIFIER & SIDE guards:", food_items)
    
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
                        
    print("After Modifier Persistence:", food_items)
    
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
    print("After Deduplication & Quantity Merging:", food_items)
    
    # 4. SIDE PERSISTENCE
    for side_kw in SIDE_KEYWORDS:
        if side_kw in user_only_text:
            existing_idx = -1
            for idx, f in enumerate(food_items):
                if side_kw in f.lower():
                    existing_idx = idx
                    break
            
            modifier = None
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
                resolved_side = f"1 {side_kw}"
                if modifier:
                    resolved_side = f"1 {modifier} {side_kw}"
                food_items.append(resolved_side)
                
    print("After Side Persistence:", food_items)
    
    # Nutrition Lookup
    parsed = [_parse_qty_and_name(item) for item in food_items]
    for qty, name in parsed:
        info = lookup_food(name)
        if info:
            print(f"Matched '{name}' -> '{info['food_name']}'")
        else:
            print(f"No match for '{name}'")

if __name__ == "__main__":
    test_meal_step_by_step()
