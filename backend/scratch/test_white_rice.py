import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from agents.food_db import lookup_food

def test_white_rice_raw():
    print("Testing 'white rice raw' lookup...")
    res = lookup_food("white rice raw")
    print(res)
    assert res is not None
    assert res["calories"] == 361, f"Expected 361 kcal, got {res['calories']}"
    assert res["protein"] == 7.4
    assert res["carbs"] == 78.2
    assert res["fats"] == 0.9
    assert res["fibre"] == 1.8
    print("[TEST PASSED]")

if __name__ == "__main__":
    test_white_rice_raw()
