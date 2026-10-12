import sys
import pprint
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from agents.extractor import extract_food

# Simulate the conversation state
context = "User: I had 3 chapatis for lunch\nWellora: Did you have it with chutney, sambar, or any other side dish? 🌸"
message = "I had it with chicken curry"

print("Simulating extraction with follow-up response:")
result = extract_food(message, context=context)
print("\nFinal Extracted Result:")

pprint.pprint(result)
