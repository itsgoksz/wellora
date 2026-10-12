import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from agents.food_db import lookup_food

def test_coffee():
    terms = ["coffee", "cup of coffee", "tea", "cup of tea"]
    for t in terms:
        res = lookup_food(t)
        if res:
            print(f"Term: '{t}' -> matched: '{res['food_name']}' ({res['calories']} kcal)")
        else:
            print(f"Term: '{t}' -> NO MATCH")

if __name__ == "__main__":
    test_coffee()
