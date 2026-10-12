import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

import asyncio
from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
import json

llm = ChatOllama(model="gemma3:4b", temperature=0.0, format="json")

# Prompt A (from test_flat_objects.py)
PROMPT_A = """<SYSTEM_INSTRUCTIONS>
You are a Professional Nutrition Data Scientist. Your task is to extract ALL food entries from a conversation and associate each food with its respective meal type (breakfast, lunch, dinner, or snack).

CRITICAL RULES:
1. ASSOCIATE MEALS: For each food item, identify which meal it belongs to (e.g. if the user says "For breakfast 2 dosas, and lunch 3 chapatis", the dosas are "breakfast" and the chapatis are "lunch").
2. COMPLETE MEAL STATE: You MUST include ALL foods mentioned in the ENTIRE conversation history.
3. NO ADDITIONS: Do NOT add descriptions like "plain", "masala", "coconut", or "sambar" unless the User explicitly wrote them.
4. STATE RESOLUTION: Combine clarification replies with their parent items.
</SYSTEM_INSTRUCTIONS>

<EXAMPLES>
User: "I had 2 dosas" -> {{"foods": [{{"food": "2 dosa", "meal_type": "snack"}}]}}
User: "I had 2 dosas for breakfast today with coconut chutney, for lunch I had 3 chapatis with rajma gravy" -> 
{{
  "foods": [
    {{"food": "2 dosa", "meal_type": "breakfast"}},
    {{"food": "1 coconut chutney", "meal_type": "breakfast"}},
    {{"food": "3 chapati", "meal_type": "lunch"}},
    {{"food": "1 rajma gravy", "meal_type": "lunch"}}
  ]
}}
</EXAMPLES>

<CONVERSATION_HISTORY>
{transcript}
</CONVERSATION_HISTORY>

<USER_SEMANTIC_MEMORY>
{semantic_context}
</USER_SEMANTIC_MEMORY>

<OUTPUT_SPECIFICATION>
Return ONLY a valid JSON object in this format.
{{
  "foods": [
    {{
      "food": "quantity name",
      "meal_type": "string"
    }}
  ]
}}
</OUTPUT_SPECIFICATION>"""

# Prompt B (from extractor.py)
from agents.extractor import PROMPT_TEMPLATE as PROMPT_B

async def test():
    transcript = "User: I had 3 dosas for breakfast today with coconut chutney, for lunch I had 3 chapatis with rajma gravy"
    semantic_context = ""
    
    # Test Prompt A
    prompt_a = PromptTemplate(template=PROMPT_A, input_variables=["transcript", "semantic_context"])
    f_a = prompt_a.format(transcript=transcript, semantic_context=semantic_context)
    res_a = llm.invoke(f_a)
    print("--- RESPONSE A ---")
    print(res_a.content)
    
    # Test Prompt B
    prompt_b = PromptTemplate(template=PROMPT_B, input_variables=["transcript", "semantic_context"])
    f_b = prompt_b.format(transcript=transcript, semantic_context=semantic_context)
    res_b = llm.invoke(f_b)
    print("--- RESPONSE B ---")
    print(res_b.content)

if __name__ == "__main__":
    asyncio.run(test())
