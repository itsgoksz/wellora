import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from agents.food_db import _FOOD_DB, _NAME_INDEX

q = "coconut rajmah curry"
q_tokens = [w for w in q.split() if w not in ["with", "and", "or", "for", "gravy", "curry", "sauce", "masala"]]

best_token_match = None
best_overlap_score = 0
best_name_len = 999

for name_lower, idx in _NAME_INDEX.items():
    name_tokens = name_lower.split()
    clean_name_tokens = [w.strip("(),").lower() for w in name_tokens]
    
    overlap = 0
    for qt in q_tokens:
        if any(qt in nt or nt in qt for nt in clean_name_tokens):
            overlap += 1
            
    if overlap > 0:
        if overlap > best_overlap_score:
            best_overlap_score = overlap
            best_token_match = (name_lower, idx)
            best_name_len = len(name_lower)
        elif overlap == best_overlap_score:
            if len(name_lower) < best_name_len:
                best_token_match = (name_lower, idx)
                best_name_len = len(name_lower)

print(f"Best match found: {best_token_match} with overlap score {best_overlap_score}")
