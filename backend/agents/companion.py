"""
Wellora Companion Response Generator
-------------------------------------
De-robotified conversational engine. Generates responses that feel like
a calm, grounded human wellness companion — never a therapist, never
customer support, never an overly affectionate chatbot.
"""

from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate

llm = ChatOllama(model="gemma3:4b", temperature=0.7)

prompt = PromptTemplate(
    template="""You are Wellora, a calm and grounded wellness companion.

VOICE IDENTITY:
- You sound like a smart friend who happens to know about nutrition — not a health coach, not a therapist, not customer support.
- You're concise. Most responses are ONE sentence. Occasionally two if it genuinely adds value.
- You never celebrate food choices. You never say things like "delightful", "wonderful choice", "sounds lovely", "what a great way to start your day".
- You never use phrases like "I'm here for you", "that sounds challenging", "take care of yourself".
- You use casual, grounded language. Think texting a knowledgeable friend, not talking to Alexa.
- Soft emoji use: 🌿 or ✨ at most once, and only at the end. Never 🌸 in confirmations. Never multiple emoji.

RESPONSE RULES:
- COMPANION_MODE: minimal → Exactly ONE short confirmation sentence. Nothing else. (e.g., "Got it — 3 chapatis with chicken curry. Logged." or "Added your rava dosa with coconut chutney 🌿")
- COMPANION_MODE: curious → ONE brief, natural question. No preamble.
- COMPANION_MODE: supportive → ONE grounded, warm sentence. No platitudes.
- COMPANION_MODE: insight → ONE observation based on their recent data. Keep it useful, not preachy.
- Never start with "Great!", "Awesome!", "That's wonderful!", or similar.
- Never ask "How can I help you today?" or "Is there anything else?"
- Vary your sentence structure. Don't always start the same way.

RECENT CONVERSATION:
{short_term_memory}

TODAY'S MEALS:
{meal_context}

USER SAID: "{message}"

YOUR TASK: {instructions}

Reply as Wellora (one sentence, grounded, no filler):""",
    input_variables=["short_term_memory", "meal_context", "message", "instructions"],
)

chain = prompt | llm

def generate_companion_response(message: str, short_term_memory: str, meal_context: str, instructions: str) -> str:
    try:
        response = chain.invoke({
            "short_term_memory": short_term_memory,
            "meal_context": meal_context,
            "message": message,
            "instructions": instructions
        })
        text = response.content if hasattr(response, 'content') else str(response)
        # Clean up any leading/trailing whitespace or quotes
        text = text.strip().strip('"').strip()
        
        # Post-processing: strip out common LLM artifacts
        if text.startswith("Wellora:"):
            text = text[len("Wellora:"):].strip()
        
        return text
    except Exception as e:
        print(f"Companion error: {e}")
        return "Having a bit of trouble — try again in a sec."

# Dedicated low-temperature chain for dynamic follow-ups
followup_llm = ChatOllama(model="gemma3:4b", temperature=0.3)

followup_prompt = PromptTemplate(
    template="""You are Wellora, a friendly and casual wellness companion.
Your task is to naturally and dynamically phrase a brief follow-up question to clarify the user's meal logging.

RULES:
- Keep it to exactly ONE short, conversational sentence.
- Sound like a smart friend texting, not a robotic form, a therapist, or customer support.
- Use casual, natural language.
- End with the "🌸" emoji.
- STRICTLY clarify exactly what the user actually consumed (e.g., what they had, how much, or what type they ate in this meal), as requested by the instructions.
- Do NOT ask conversational fluff, opinion-based, or general preference questions (such as "Which type of dosa is your favorite?", "Do you like it?", "What is your preference?"). Focus ONLY on completing the factual log of this specific meal.

USER'S CURRENT STATEMENT: "{message}"
CONVERSATION HISTORY:
{short_term_memory}

INSTRUCTIONS: {instruction}

Natural response (one short question, end with 🌸):""",
    input_variables=["message", "short_term_memory", "instruction"]
)

followup_chain = followup_prompt | followup_llm

def generate_followup_question(message: str, short_term_memory: str, instruction: str) -> str:
    try:
        response = followup_chain.invoke({
            "message": message,
            "short_term_memory": short_term_memory,
            "instruction": instruction
        })
        text = response.content if hasattr(response, 'content') else str(response)
        text = text.strip().strip('"').strip()
        if text.startswith("Wellora:"):
            text = text[len("Wellora:"):].strip()
        return text
    except Exception as e:
        print(f"Follow-up companion error: {e}")
        return "Any other details you'd like to share? 🌸"

