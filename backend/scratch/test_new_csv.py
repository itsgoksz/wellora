import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from agents.food_db import lookup_food

def test_new_csv_lookup():
    print("Testing lookup of new CSV foods...")
    
    # "cream cheese" is in FOOD-DATA-GROUP1.csv with 51 calories
    res = lookup_food("cream cheese")
    print("\nCream Cheese Lookup:")
    print(res)
    assert res is not None
    assert res["calories"] == 51, f"Expected 51 kcal, got {res['calories']}"
    assert res["serving_unit"] == "serving"
    assert res["protein"] == 0.9
    assert res["carbs"] == 0.8
    assert res["fats"] == 5.0
    assert res["fibre"] == 0.0
    
    print("\n[NEW CSV LOOKUP TEST PASSED SUCCESSFULLY!]")

if __name__ == "__main__":
    test_new_csv_lookup()
