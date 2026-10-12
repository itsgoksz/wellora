import sys
import asyncio
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
import json

llm = ChatOllama(model="gemma3:4b", temperature=0.0, format="json")

PROMPT_TEMPLATE = """<SYSTEM_INSTRUCTIONS>
You are a Professional Nutrition Data Scientist. Your task is to extract ALL food entries from a conversation.

CRITICAL RULES:
1. COMPLETE MEAL STATE: You MUST include ALL foods mentioned in the ENTIRE conversation history for this meal. If the user mentions a main dish earlier, and a side dish later, your output must contain BOTH. Do NOT drop previously mentioned foods.
2. NO ADDITIONS: Do NOT add descriptions like "plain", "masala", "coconut", or "sambar" unless the User explicitly wrote them.
3. STATE RESOLUTION: Combine clarification replies with their parent items. E.g. if the user says "I had 2 dosas" and clarifies "rava", output ONLY "2 rava dosa". Do NOT output both "2 dosa" and "2 rava dosa".
</SYSTEM_INSTRUCTIONS>

<EXAMPLES>
User: "I had 2 dosas" -> {{"foods": ["2 dosa"], "meal_type": "snack"}}
User: "I had 2 dosas" + Context: "plain" -> {{"foods": ["2 plain dosa"], "meal_type": "snack"}}
User: "I had 2 dosas" + Context: "with coconut chutney" -> {{"foods": ["2 dosa", "1 coconut chutney"], "meal_type": "snack"}}
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
  "foods": ["quantity name", ...],
  "meal_type": "string"
}}
</OUTPUT_SPECIFICATION>"""

prompt = PromptTemplate(template=PROMPT_TEMPLATE, input_variables=["transcript", "semantic_context"])

async def test():
    transcript = "User: I had 3 dosas for breakfast today with coconut chutney, for lunch I had 3 chapatis with rajma gravy"
    semantic_context = ""
    formatted = prompt.format(transcript=transcript, semantic_context=semantic_context)
    res = llm.invoke(formatted)
    print("--- ORIGINAL PROMPT LLM RESPONSE ---")
    print(res.content)
    print("------------------------------------")

if __name__ == "__main__":
    asyncio.run(test())
