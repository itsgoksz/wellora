import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from agents.food_db import lookup_food

def test_matching():
    scenarios = [
        "rajma gravy",
        "rajma curry",
        "rajmah curry",
        "kidney bean curry",
        "kidney bean curry (rajmah curry)",
        "rajma",
        "kidney bean"
    ]
    
    print("=== NUTRITION LOOKUP MATCHING TEST ===")
    all_passed = True
    for scenario in scenarios:
        res = lookup_food(scenario)
        if res:
            print(f"✅ '{scenario}' matched to: '{res['food_name']}' ({res['calories']} kcal, {res['protein']}g protein)")
            if "kidney bean curry" not in res['food_name'].lower() and "rajmah curry" not in res['food_name'].lower():
                print(f"❌ Failed: matched to incorrect item")
                all_passed = False
        else:
            print(f"❌ '{scenario}' failed to match!")
            all_passed = False
            
    if all_passed:
        print("\n🎉 ALL RAJMA/KIDNEY BEAN MATCHING SCENARIOS PASSED PERFECTLY!")
    else:
        print("\n⚠️ SOME MATCHING SCENARIOS FAILED!")

if __name__ == "__main__":
    test_matching()
