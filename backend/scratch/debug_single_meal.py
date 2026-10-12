import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from agents.extractor import _process_single_meal, MODIFIERS, CHUTNEY_TYPES, SIDE_KEYWORDS, _parse_qty_and_name
from agents.food_db import lookup_food

def test_meal():
    user_text = "I had 3 dosas with coconut chutney for breakfast and 2 chapatis with rajma curry for lunch"
    print("=== DEBUGGING breakfast ===")
    res = _process_single_meal(["3 dosa", "1 coconut chutney"], "breakfast", user_text)
    print("Result:", res)

if __name__ == "__main__":
    test_meal()
