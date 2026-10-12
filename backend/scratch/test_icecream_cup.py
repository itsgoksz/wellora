import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from agents.food_db import lookup_food

def test_chocolate_ice_cream():
    print("Testing 'chocolate ice cream' lookup...")
    
    # 1. Plain lookup without "cup"
    res_serving = lookup_food("chocolate ice cream")
    print("\nPlain Lookup (serving):")
    print(res_serving)
    assert res_serving is not None
    assert res_serving["calories"] == 178, f"Expected 178 kcal per scoop, got {res_serving['calories']}"
    assert res_serving["serving_unit"] == "scoop"
    
    # 2. Lookup with "1 cup"
    res_cup = lookup_food("1 cup of chocolate ice cream")
    print("\nCup Lookup:")
    print(res_cup)
    assert res_cup is not None
    assert res_cup["calories"] == 178, f"Expected 178 kcal per standard cup (100g baseline), got {res_cup['calories']}"
    assert res_cup["serving_unit"] == "cup"
    assert res_cup["protein"] == 4.5
    assert res_cup["carbs"] == 15.4
    assert res_cup["fats"] == 11.2
    assert res_cup["fibre"] == 0.0

    # 3. Lookup with "1 scoop"
    res_scoop = lookup_food("1 scoop of chocolate ice cream")
    print("\nScoop Lookup:")
    print(res_scoop)
    assert res_scoop is not None
    assert res_scoop["calories"] == 178, f"Expected 178 kcal per standard scoop (100g baseline), got {res_scoop['calories']}"
    assert res_scoop["serving_unit"] == "scoop"
    assert res_scoop["protein"] == 4.5
    assert res_scoop["carbs"] == 15.4
    assert res_scoop["fats"] == 11.2
    assert res_scoop["fibre"] == 0.0
    
    print("\n[ALL TESTS PASSED SUCCESSFULLY!]")

if __name__ == "__main__":
    test_chocolate_ice_cream()

