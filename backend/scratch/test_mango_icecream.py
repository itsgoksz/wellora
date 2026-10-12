import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from agents.food_db import lookup_food

def test_mango_ice_cream():
    print("Testing 'mango ice cream' lookup...")
    
    # 1. Plain lookup without "cup" or "scoop"
    res_serving = lookup_food("mango ice cream")
    print("\nPlain Lookup (serving):")
    print(res_serving)
    assert res_serving is not None
    assert res_serving["calories"] == 126, f"Expected 126 kcal per scoop, got {res_serving['calories']}"
    assert res_serving["serving_unit"] == "scoop"
    
    # 2. Lookup with "1 scoop"
    res_scoop = lookup_food("1 scoop of mango ice cream")
    print("\nScoop Lookup:")
    print(res_scoop)
    assert res_scoop is not None
    assert res_scoop["calories"] == 126, f"Expected 126 kcal per scoop (100g baseline), got {res_scoop['calories']}"
    assert res_scoop["serving_unit"] == "scoop"
    assert res_scoop["protein"] == 3.4
    assert res_scoop["carbs"] == 11.1
    assert res_scoop["fats"] == 7.6
    assert res_scoop["fibre"] == 0.5
    
    print("\n[ALL MANGO TESTS PASSED SUCCESSFULLY!]")

if __name__ == "__main__":
    test_mango_ice_cream()
