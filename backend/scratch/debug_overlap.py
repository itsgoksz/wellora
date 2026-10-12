import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from agents.food_db import _FOOD_DB, _NAME_INDEX

q = "coconut rajmah curry"
q_tokens = [w for w in q.split() if w not in ["with", "and", "or", "for", "gravy", "curry", "sauce", "masala"]]

name_lower = 'lentils and wheat porridge (dal wheat porridge/daliya )'
name_tokens = name_lower.split()
clean_name_tokens = [w.strip("(),").lower() for w in name_tokens]

print(f"q_tokens: {q_tokens}")
print(f"clean_name_tokens: {clean_name_tokens}")

for qt in q_tokens:
    for nt in clean_name_tokens:
        if qt in nt or nt in qt:
            print(f"Match: qt='{qt}' nt='{nt}' (qt in nt: {qt in nt}, nt in qt: {nt in qt})")
