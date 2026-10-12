# Wellora Food Database — CSV-backed with fuzzy matching
import csv
import os
from difflib import get_close_matches
from pathlib import Path

CSV_PATH = Path(__file__).resolve().parent.parent / "data" / "food-calorie-data.csv"

# ── Load CSV into memory once at import ────────────────────────────────
_FOOD_DB: list[dict] = []
_FOOD_NAMES: list[str] = []
_NAME_INDEX: dict[str, int] = {}   # lowercase name → index

def _load_csv():
    global _FOOD_DB, _FOOD_NAMES, _NAME_INDEX
    if _FOOD_DB:
        return
    
    # 1. Load the primary food-calorie-data.csv first
    if os.path.exists(CSV_PATH):
        with open(CSV_PATH, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                clean = {k.strip(): v.strip() for k, v in row.items()}
                _FOOD_DB.append(clean)
                name = clean.get("food_name", "").strip()
                _FOOD_NAMES.append(name)
                idx = len(_FOOD_DB) - 1
                _NAME_INDEX[name.lower()] = idx
                if "(" in name:
                    short = name[:name.index("(")].strip()
                    _NAME_INDEX[short.lower()] = idx

    # 2. Load all other CSV files in the data directory (e.g. FOOD-DATA-GROUP*.csv)
    data_dir = CSV_PATH.parent
    if os.path.exists(data_dir):
        for file_name in os.listdir(data_dir):
            if file_name.endswith(".csv") and file_name != "food-calorie-data.csv":
                path = data_dir / file_name
                with open(path, newline="", encoding="utf-8-sig") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        clean = {k.strip() if k else "": v.strip() for k, v in row.items()}
                        food_name = clean.get("food", "").strip()
                        if not food_name:
                            continue
                        
                        # Map group CSV headers to standard food-calorie-data headers
                        mapped_row = {
                            "food_name": food_name,
                            "energy_kcal": clean.get("Caloric Value", "0"),
                            "protein_g": clean.get("Protein", "0"),
                            "carb_g": clean.get("Carbohydrates", "0"),
                            "fat_g": clean.get("Fat", "0"),
                            "fibre_g": clean.get("Dietary Fiber", "0"),
                            "servings_unit": "serving",
                            "unit_serving_energy_kcal": clean.get("Caloric Value", "0"),
                            "unit_serving_protein_g": clean.get("Protein", "0"),
                            "unit_serving_carb_g": clean.get("Carbohydrates", "0"),
                            "unit_serving_fat_g": clean.get("Fat", "0"),
                            "unit_serving_fibre_g": clean.get("Dietary Fiber", "0"),
                        }
                        
                        _FOOD_DB.append(mapped_row)
                        idx = len(_FOOD_DB) - 1
                        
                        # Add to index if not already present
                        name_lower = food_name.lower()
                        if name_lower not in _NAME_INDEX:
                            _NAME_INDEX[name_lower] = idx
                            _FOOD_NAMES.append(food_name)
                            if "(" in food_name:
                                short = food_name[:food_name.index("(")].strip()
                                if short.lower() not in _NAME_INDEX:
                                    _NAME_INDEX[short.lower()] = idx

_load_csv()


def _safe_float(val: str, default: float = 0.0) -> float:
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


# ── Lookup a single food by name (fuzzy) ───────────────────────────────
def lookup_food(query: str) -> dict | None:
    """
    Look up a food item by name. Returns per-serving nutrition or None.
    Uses exact match first, then smart substring, then fuzzy, then token overlap.
    """
    q_orig = query.lower()
    has_scoop = "scoop" in q_orig or "scoops" in q_orig
    has_cup = "cup" in q_orig or "cups" in q_orig or has_scoop
    q = query.lower().strip()

    # Strip plural suffixes to map terms (e.g. chapatis -> chapati, dosas -> dosa)
    words = q.split()
    clean_words = []
    
    # Common auxiliary terms and quantity keywords to filter out for clean matching
    AUXILIARY_TERMS = {
        "serving", "servings", "portion", "portions", "quantity", "piece", "pieces",
        "cup", "cups", "bowl", "bowls", "plate", "plates", "glass", "glasses", "spoon",
        "spoons", "tablespoon", "tablespoons", "teaspoon", "teaspoons", "tbsp", "tsp",
        "scoop", "scoops", "of", "a", "an", "the", "some", "with", "and", "or", "for", "one",
        "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "about",
        "roughly", "servingsof"
    }
    
    for w in words:
        # Strip digits
        w = "".join([c for c in w if not c.isdigit()]).strip()
        if not w:
            continue
            
        if w in AUXILIARY_TERMS:
            continue
            
        if w.endswith("s") and len(w) > 3:
            if w.endswith("ies"):
                w = w[:-3] + "y"
            elif w.endswith("es") and w[:-2] in ["glass", "dish"]:
                w = w[:-2]
            elif w.endswith("s") and not w.endswith("ss"):
                w = w[:-1]
                
        if w not in AUXILIARY_TERMS:
            clean_words.append(w)
            
    q = " ".join(clean_words).strip()

    # Normalize spelling variations / spelling variants for popular Indian items
    NORMALIZATIONS = {
        "rajma": "rajmah",
        "paratha": "parantha",
        "biryani": "biriyani",
        "chicken biriyani": "chicken pulao",
        "chicken biryani": "chicken pulao",
        "sambar": "sambhar",
        "chana": "channa",
        "puri": "poori",
        "dal": "dhal",
        "kadhi": "kadi",
        "omelette": "omlet",
        "dosai": "dosa",
        "gravy": "curry",
        "subzi": "sabzi",
        "sabji": "sabzi",
    }
    
    for word, norm in NORMALIZATIONS.items():
        if word in q:
            q = q.replace(word, norm)

    # Default standard hot coffee/tea mapping if no cold/iced is specified to prevent hallucinations
    if "coffee" in q and not any(x in q for x in ["cold", "iced", "biscuit", "ice cream", "drops", "espreso", "espresso"]):
        q = "steeped hot coffee"
    elif "tea" in q and not any(x in q for x in ["iced", "cold", "green", "herbal", "black"]):
        q = "hot tea (garam chai)"

    # Default generic chutney to coconut chutney (standard South Indian side)
    if "chutney" in q or "chatni" in q:
        # If no specific chutney type is mentioned, treat as generic and map to coconut chutney
        if not any(t in q for t in ["coconut", "tomato", "mint", "pudina", "ginger", "garlic", "onion", "peanut", "plum", "kara", "red", "green", "saunth", "sonth", "tamarind", "imli", "mango", "hare", "dhaniye", "gooseberry", "amla", "walnut", "akhrot", "dates", "khajoor", "schezwan"]):
            q = "coconut chutney"

    # 1. Exact match
    if q in _NAME_INDEX:
        row = _FOOD_DB[_NAME_INDEX[q]]
        return _row_to_nutrition(row, has_cup=has_cup, has_scoop=has_scoop)

    # 2. Smart Substring Match
    potential_matches = []
    for name_lower, idx in _NAME_INDEX.items():
        # Strip trailing modifiers in DB lookup to handle paren variants
        name_clean = name_lower
        if "(" in name_clean:
            name_clean = name_clean[:name_clean.index("(")].strip()
            
        if q == name_clean or q == name_lower:
             return _row_to_nutrition(_FOOD_DB[idx], has_cup=has_cup, has_scoop=has_scoop)
        if q in name_lower or q in name_clean:
            potential_matches.append((name_lower, idx))
    
    if potential_matches:
        def calculate_score(item):
            name_lower, idx = item
            name_clean = name_lower
            if "(" in name_clean:
                name_clean = name_clean[:name_clean.index("(")].strip()
                
            components = [c.strip() for c in name_clean.split("/")]
            normalized_components = []
            for c in components:
                nc = c.lower()
                for word, norm in NORMALIZATIONS.items():
                    if word in nc:
                        nc = nc.replace(word, norm)
                normalized_components.append(nc)
                
            # 1. Exact match of one of the slash-split components
            if q in normalized_components:
                if "plain" in name_lower or "plain" in name_clean:
                    return (4, -len(name_lower))
                return (3, -len(name_lower))
                
            # 2. Match with "plain" modifier
            for nc in normalized_components:
                if nc == f"plain {q}" or nc == f"{q} plain" or (nc.startswith("plain ") and nc.endswith(q)):
                    return (4, -len(name_lower))
                    
            # 3. Starts with query
            starts_with_q = False
            for nc in normalized_components:
                if nc.startswith(q):
                    starts_with_q = True
                    break
            if starts_with_q:
                if "plain" in name_lower or "plain" in name_clean:
                    return (2, -len(name_lower))
                return (1, -len(name_lower))
                
            # 4. Fallback substring match
            if "plain" in name_lower or "plain" in name_clean:
                return (0, -len(name_lower))
            return (-1, -len(name_lower))

        scored_matches = [(m, calculate_score(m)) for m in potential_matches]
        scored_matches.sort(key=lambda x: x[1], reverse=True)
        best_match = scored_matches[0][0]
        return _row_to_nutrition(_FOOD_DB[best_match[1]], has_cup=has_cup, has_scoop=has_scoop)

    # 3. Smart multi-word token matching (e.g. "coconut rajma gravy" -> "rajmah curry")
    # Break query into tokens
    q_tokens = [w for w in q.split() if w not in ["with", "and", "or", "for", "gravy", "curry", "sauce", "masala"]]
    if q_tokens:
        best_token_match = None
        best_overlap_score = 0
        best_name_len = 999
        
        # Smart prioritization: if query contains a high priority dish keyword, prioritize matching that keyword
        HIGH_PRIORITY_KEYWORDS = [
            "rajmah", "dosa", "biriyani", "chapati", "roti", "paneer", "chicken",
            "mutton", "fish", "egg", "dal", "dhal", "idli", "sambhar", "chutney",
            "poha", "upma", "vada", "coffee", "tea", "burger", "pizza", "fries"
        ]
        q_prio = [kw for kw in HIGH_PRIORITY_KEYWORDS if kw in q]
        
        for name_lower, idx in _NAME_INDEX.items():
            # If query has high priority keywords, DB name must contain at least one of them
            if q_prio and not any(kw in name_lower for kw in q_prio):
                continue
                
            name_tokens = name_lower.split()
            clean_name_tokens = [w.strip("(),").lower() for w in name_tokens if w.strip("(),")]
            
            overlap = 0
            for qt in q_tokens:
                if len(qt) < 3:
                    continue
                if any((qt in nt or nt in qt) and len(nt) >= 3 for nt in clean_name_tokens):
                    overlap += 1
            
            if overlap > 0:
                if overlap > best_overlap_score:
                    best_overlap_score = overlap
                    best_token_match = idx
                    best_name_len = len(name_lower)
                elif overlap == best_overlap_score:
                    if len(name_lower) < best_name_len:
                        best_token_match = idx
                        best_name_len = len(name_lower)
                        
        if best_token_match is not None and (best_overlap_score / len(q_tokens)) >= 0.3:
            return _row_to_nutrition(_FOOD_DB[best_token_match], has_cup=has_cup, has_scoop=has_scoop)

    # 4. Fuzzy match fallback
    matches = get_close_matches(q, list(_NAME_INDEX.keys()), n=1, cutoff=0.75)
    if matches:
        return _row_to_nutrition(_FOOD_DB[_NAME_INDEX[matches[0]]], has_cup=has_cup, has_scoop=has_scoop)

    return None


def _row_to_nutrition(row: dict, has_cup: bool = False, has_scoop: bool = False) -> dict:
    """Extract per-serving nutrition from a CSV row."""
    food_name_lower = row.get("food_name", "").lower()
    if food_name_lower == "white rice raw":
        return {
            "food_name": row.get("food_name", ""),
            "serving_unit": "serving",
            "calories": 361,
            "protein": 7.4,
            "carbs": 78.2,
            "fats": 0.9,
            "fibre": 1.8,
            "source": "white_rice_raw_override",
        }

    is_ice_cream = "ice cream" in row.get("food_name", "").lower() or "ice-cream" in row.get("servings_unit", "").lower()

    if is_ice_cream:
        serving_unit = "cup" if (has_cup and not has_scoop) else "scoop"
        return {
            "food_name": row.get("food_name", ""),
            "serving_unit": serving_unit,
            "calories": round(_safe_float(row.get("energy_kcal"))),
            "protein": round(_safe_float(row.get("protein_g")), 1),
            "carbs": round(_safe_float(row.get("carb_g")), 1),
            "fats": round(_safe_float(row.get("fat_g")), 1),
            "fibre": round(_safe_float(row.get("fibre_g")), 1),
            "source": "csv_per_100g_ice_cream",
        }

    # Prefer unit_serving values (per piece/cup/plate); fall back to per-100g
    has_serving = bool(row.get("unit_serving_energy_kcal", "").strip())

    if has_serving:
        return {
            "food_name": row.get("food_name", ""),
            "serving_unit": row.get("servings_unit", "serving"),
            "calories": round(_safe_float(row.get("unit_serving_energy_kcal"))),
            "protein": round(_safe_float(row.get("unit_serving_protein_g")), 1),
            "carbs": round(_safe_float(row.get("unit_serving_carb_g")), 1),
            "fats": round(_safe_float(row.get("unit_serving_fat_g")), 1),
            "fibre": round(_safe_float(row.get("unit_serving_fibre_g")), 1),
            "source": "csv_per_serving",
        }
    else:
        return {
            "food_name": row.get("food_name", ""),
            "serving_unit": "100g",
            "calories": round(_safe_float(row.get("energy_kcal"))),
            "protein": round(_safe_float(row.get("protein_g")), 1),
            "carbs": round(_safe_float(row.get("carb_g")), 1),
            "fats": round(_safe_float(row.get("fat_g")), 1),
            "fibre": round(_safe_float(row.get("fibre_g")), 1),
            "source": "csv_per_100g",
        }


# ── Multi-food lookup for the extractor ────────────────────────────────
def lookup_foods(food_names: list[str]) -> list[dict]:
    """Look up multiple foods. Returns list of nutrition dicts."""
    results = []
    for name in food_names:
        result = lookup_food(name)
        if result:
            results.append(result)
    return results


# ── Reference string for LLM context (top ~40 common items) ───────────
_COMMON_FOODS = [
    "Plain dosa", "Masala dosa", "Idli", "Sambar",
    "Coconut chutney", "Chapati/Roti", "Parotta",
    "Mutton biryani/biriyani", "Vegetable biryani/biriyani",
    "Paneer butter masala", "Chicken curry", "Dal/Dhal",
    "Poha", "Upma", "Curd rice",
    "Naan", "Puri", "Vada",
    "Filter coffee", "Hot tea",
    "Chocolate ice cream", "Vanilla ice cream without egg", "Mango ice cream",
    "Burger", "French fries", "Pizza",
    "Egg fried rice", "Chicken fried rice",
    "Masala dosa mixed vegetable fillings", "Masala dosa paneer fillings",
    "Mint and coriander chutney",
]

def get_food_reference_string() -> str:
    """Returns a compact nutrition reference for the LLM prompt."""
    lines = ["NUTRITION DATABASE (per serving):"]
    for name in _COMMON_FOODS:
        info = lookup_food(name)
        if info:
            lines.append(
                f"- {info['food_name']} (1 {info['serving_unit']}): "
                f"{info['calories']} kcal, {info['protein']}g protein, "
                f"{info['carbs']}g carbs, {info['fats']}g fat"
            )
    lines.append(f"\n(Full database: {len(_FOOD_DB)} foods available)")
    return "\n".join(lines)
