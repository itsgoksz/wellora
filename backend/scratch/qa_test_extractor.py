from agents.extractor import extract_food
import json

def test_case(name, sequence):
    print(f"\n=== TEST: {name} ===")
    context = ""
    for i, msg in enumerate(sequence):
        print(f"Turn {i+1} User: {msg}")
        res = extract_food(msg, context)
        print(f"Wellora Q: {res['followup_question']}")
        print(f"Foods: {res['normalized_foods']} | Cals: {res['calories']} | Meal: {res['meal_type']}")
        
        # Update context for next turn
        context += f"\nUser: {msg}\nWellora: {res['followup_question'] or 'Enjoy!'}"
    print("-" * 30)

# 1. The Reported Failure (3 dosas for breakfast -> plain -> chutney)
test_case("Reported Failure", [
    "I had 3 dosas for breakfast",
    "plain dosa",
    "with chutney"
])

# 2. Ambiguity + Decline (2 dosas -> masala -> no)
test_case("Ambiguity + Decline", [
    "I had 2 dosas",
    "masala",
    "no"
])

# 3. New Meal Interrupting (2 dosas -> what about lunch? -> I had 2 pooris)
test_case("New Meal Intent", [
    "I had 2 dosas",
    "I had 2 pooris for lunch"
])

# 4. Multi-item Extraction
test_case("Multi-item", [
    "I had 2 idlis and a coffee",
    "with sambar"
])
