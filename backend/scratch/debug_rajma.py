import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from agents.food_db import _FOOD_DB, _NAME_INDEX

q = "coconut rajmah curry"
q_tokens = [w for w in q.split() if w not in ["with", "and", "or", "for", "gravy", "curry", "sauce", "masala"]]

print(f"q_tokens: {q_tokens}")

for name_lower, idx in _NAME_INDEX.items():
    name_tokens = name_lower.split()
    clean_name_tokens = [w.strip("(),").lower() for w in name_tokens]
    
    overlap = 0
    overlapping_tokens = []
    for qt in q_tokens:
        if any(qt in nt or nt in qt for nt in clean_name_tokens):
            overlap += 1
            overlapping_tokens.append(qt)
            
    if "rajmah" in name_lower or "rajma" in name_lower:
        print(f"DB Entry: '{name_lower}' | Clean Tokens: {clean_name_tokens} | Overlap: {overlap} | Overlapping: {overlapping_tokens}")
