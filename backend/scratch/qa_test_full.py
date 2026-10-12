import json
import os
import sys

# Add current directory to path so we can import agents
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agents.extractor import extract_food

def run_scenario(name, sequence):
    print(f"\n🚀 SCENARIO: {name}")
    print("="*60)
    context = ""
    for i, msg in enumerate(sequence):
        print(f"Turn {i+1} | User: {msg}")
        res = extract_food(msg, context)
        
        q = res.get("followup_question")
        foods = res.get("normalized_foods")
        meal = res.get("meal_type")
        cals = res.get("calories")
        
        print(f"       | Wellora: {q if q else '[LOGGED] ' + str(foods) + ' (' + str(cals) + ' kcal)'}")
        print(f"       | Meal Type: {meal}")
        
        # Update context for next turn
        context += f"\nUser: {msg}\nWellora: {q or 'Enjoy!'}"
    print("="*60)

if __name__ == "__main__":
    # 1. The "Dosa Path" (Perfect Flow)
    run_scenario("Standard Dosa Flow", [
        "I had 3 dosas for breakfast",
        "plain dosa",
        "with chutney",
        "coconut chutney"
    ])

    # 2. The "Direct Completion"
    run_scenario("Full Detail Entry", [
        "I had 1 masala dosa with sambar for lunch"
    ])

    # 3. The "Decline Side"
    run_scenario("Declining Sambar/Chutney", [
        "I had 2 idlis",
        "no, just idlis"
    ])

    # 4. Hallucination Guard Test
    run_scenario("Hallucination Prevention", [
        "I had 3 pooris"
    ])

    # 5. Multiple Items
    run_scenario("Multi-item Extraction", [
        "I had 2 idlis and a coffee",
        "with sambar"
    ])

    # 6. Chutney Ambiguity
    run_scenario("Chutney Type Clarification", [
        "I had plain dosa with chutney",
        "tomato chutney"
    ])

    # 7. Interrupted Context (Switching items)
    run_scenario("Switching Focus", [
        "I had 2 dosas",
        "wait, I actually had 2 pooris for breakfast",
        "no, just that"
    ])
