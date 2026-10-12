import sys
import asyncio
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from agents.extractor import extract_food
from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
import json

async def test():
    message = "I had 3 dosas for breakfast today with coconut chutney, for lunch I had 3 chapatis with rajma gravy"
    
    print("=== RUNNING EXTRACT_FOOD ===")
    res_extractor = extract_food(message, context="")
    print("Extractor returned:", res_extractor)
    
    print("\n=== RUNNING DIRECT FLAT OBJECTS PROMPT ===")
    llm = ChatOllama(model="gemma3:4b", temperature=0.0, format="json")
    PROMPT_TEMPLATE = """<SYSTEM_INSTRUCTIONS>
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
Return ONLY a valid JSON object.
{{
  "foods": [
    {{
      "food": "quantity name",
      "meal_type": "string"
    }}
  ]
}}
</OUTPUT_SPECIFICATION>"""

    prompt = PromptTemplate(template=PROMPT_TEMPLATE, input_variables=["transcript", "semantic_context"])
    transcript = "User: I had 3 dosas for breakfast today with coconut chutney, for lunch I had 3 chapatis with rajma gravy"
    formatted = prompt.format(transcript=transcript, semantic_context="")
    res = llm.invoke(formatted)
    print("Direct Prompt returned:", res.content)

if __name__ == "__main__":
    asyncio.run(test())
