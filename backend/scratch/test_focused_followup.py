import sys
sys.path.insert(0, '.')
from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate

llm = ChatOllama(model="qwen2.5:3b", temperature=0.3)

followup_prompt = PromptTemplate(
    template="""You are Wellora, a friendly and casual wellness companion.
Your task is to naturally and dynamically phrase a brief follow-up question.

RULES:
- Keep it to exactly ONE short, conversational sentence.
- Sound like a smart friend texting, not a robotic form or a therapist.
- Use casual, natural language.
- End with the "🌸" emoji.
- You must actually ask the question described in the instructions! Do not ask philosophical or unrelated questions.

USER'S CURRENT STATEMENT: "{message}"
CONVERSATION HISTORY:
{short_term_memory}

INSTRUCTIONS: {instruction}

Natural response (one short question, end with 🌸):""",
    input_variables=["message", "short_term_memory", "instruction"]
)

chain = followup_prompt | llm

def test(message, history, instruction):
    res = chain.invoke({
        "message": message,
        "short_term_memory": history,
        "instruction": instruction
    })
    print(f"Instruction: {instruction}")
    print(f"Response: {res.content.strip()}")
    print("-" * 40)

# Test 1: ask_side_dish
test(
    message="masala dosa",
    history="User: I had 3 dosas for breakfast today\nWellora: What kind of dosa was that? 🌸",
    instruction="Ask if they had any side dishes like chutney, sambar, or anything else with their masala dosa. Keep it casual and brief."
)

# Test 2: ask_chutney_servings
test(
    message="I had coconut chutney",
    history="User: I had 3 dosas for breakfast today\nWellora: What kind of dosa was that? 🌸\nUser: masala dosa\nWellora: Did you have it with any side dish? 🌸",
    instruction="Ask roughly how many servings of coconut chutney they had. Keep it conversational and brief."
)
