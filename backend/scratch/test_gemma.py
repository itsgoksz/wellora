from langchain_ollama import ChatOllama

# Let's test WITHOUT format="json"
llm = ChatOllama(model="gemma3:4b", temperature=0.0)

prompt = """<SYSTEM_INSTRUCTIONS>
You are a Professional Nutrition Data Scientist. Your task is to extract ALL food entries from a conversation and associate each food with its respective meal type (breakfast, lunch, dinner, or snack).

CRITICAL RULES:
1. ASSOCIATE MEALS: For each food item, identify which meal it belongs to.
2. COMPLETE MEAL STATE: You MUST include ALL foods mentioned in the ENTIRE conversation history, not just the latest message.
3. NO ADDITIONS: Do NOT add descriptions like "plain", "masala", "coconut", or "sambar" unless the User explicitly wrote them.
4. STATE RESOLUTION: When the conversation contains clarification Q&A (like asking "what kind of dosa" or "how many servings of chutney"), you MUST combine those answers with their respective items. For example, if the user said "3 dosas" earlier, then clarifies "masala", then adds "coconut chutney", and then clarifies "2 servings", you MUST combine them into "3 masala dosa" and "2 coconut chutney".
5. EVERY food mentioned by the user MUST appear in the output. If the user said "3 dosas" earlier and later clarified "rava dosa", output "3 rava dosa".
</SYSTEM_INSTRUCTIONS>

<EXAMPLES>
Example 1 - Simple:
User: "I had 2 dosas" -> {"foods": [{"food": "2 dosa", "meal_type": "snack"}]}

Example 2 - Multi-meal:
User: "I had 2 dosas for breakfast today with coconut chutney, for lunch I had 3 chapatis with rajma gravy" -> 
{
  "foods": [
    {"food": "2 dosa", "meal_type": "breakfast"},
    {"food": "1 coconut chutney", "meal_type": "breakfast"},
    {"food": "3 chapati", "meal_type": "lunch"},
    {"food": "1 rajma gravy", "meal_type": "lunch"}
  ]
}
</EXAMPLES>

<CONVERSATION_HISTORY>
User: I had 3 dosas with 1 serving of coconut chutney for breakfast and 2 chapatis with rajmah curry for lunch
</CONVERSATION_HISTORY>

<USER_SEMANTIC_MEMORY>

</USER_SEMANTIC_MEMORY>

<OUTPUT_SPECIFICATION>
Return ONLY a valid JSON object. Include ALL foods from the entire conversation.
{
  "foods": [
    {
      "food": "quantity name",
      "meal_type": "string"
    }
  ]
}
</OUTPUT_SPECIFICATION>"""

res = llm.invoke(prompt)
print("=== RESPONSE ===")
print(res.content)
