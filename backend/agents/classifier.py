from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
import re

llm = ChatOllama(model="gemma3:4b", temperature=0.0, format="json")


# Keyword-based pre-classifier for reliability
# Keyword-based pre-classifier for reliability
FOOD_KEYWORDS = {
    "ate", "eaten", "had", "dosa", "dosai", "idli", "idly", "biryani", "rice", 
    "roti", "chapati", "naan", "parotta", "poha", "upma", "sambar", "chutney",
    "paneer", "chicken", "mutton", "fish", "egg", "omelette", "toast", "bread",
    "burger", "pizza", "fries", "sandwich", "pasta", "noodles", "maggi",
    "coffee", "chai", "tea", "juice", "milkshake", "lassi", "buttermilk",
    "breakfast", "lunch", "dinner", "snack", "meal", "food", "eat", "eating",
    "curd", "dal", "dhal", "sabzi", "curry", "masala", "vada", "puri", "poori",
    "uttapam", "appam", "puttu", "pesarattu", "bajji", "bonda", "pav bhaji",
    "skipped breakfast", "skipped lunch", "skipped dinner",
    "serving", "servings", "bowl", "plate", "cup", "mug",
}

HYDRATION_KEYWORDS = {
    "water", "hydration", "hydrated", "glass", "glasses", "bottle", "bottles",
    "cup", "cups", "litre", "litres", "liter", "liters", "ml", "electrolyte", 
    "electrolytes", "coconut water", " Gatorade", "powerade", "liquid iv"
}

ALCOHOL_KEYWORDS = {
    "beer", "beers", "budweiser", "wine", "wines", "whiskey", "whisky", "vodka",
    "rum", "cocktail", "cocktails", "tequila", "gin", "champagne", "cider", "alcohol",
    "booze", "drink", "drinks", "drinking", "ale", "lager", "stout", "brandy", 
    "liqueur", "chardonnay", "cabernet", "merlot", "pinot", "sauvignon", "margarita",
    "martini", "mojito", "shot", "shots", "erdinger", "weizenbier", "went out drinking", "grabbed beers"
}

SLEEP_KEYWORDS = {"sleep", "slept", "woke", "insomnia", "nap", "bedtime", "tired"}
MOOD_KEYWORDS = {"feeling", "mood", "stressed", "anxious", "happy", "sad", "low energy"}
GREETING_KEYWORDS = {"hi", "hello", "hey", "good morning", "good evening", "good afternoon"}

def keyword_classify(message: str) -> str | None:
    msg = message.lower().strip()
    
    if msg in GREETING_KEYWORDS or msg.startswith(("hi ", "hey ", "hello")):
        return "greeting"
        
    # Intercept nutrition/calorie queries to classify as wellness_question instead of logging
    nutrition_queries = [
        "how many calories", "how much calorie", "how many calorie", "how much calories",
        "calories does", "calories in", "calorie in", "calories of", "calorie of",
        "nutrition in", "nutrition of", "nutritional value", "what is the calorie",
        "what are the calories", "how much protein", "how much carb", "how much fat",
        "how much fiber", "how much fibre", "protein in", "carbs in", "fat in", "fiber in"
    ]
    if any(q in msg for q in nutrition_queries):
        return "wellness_question"
        
    # Intercept symptom/wellness questions to classify as wellness_question instead of logging
    symptom_queries = [
        "cramp", "period", "menstrua", "stomach ache", "stomach pain", "belly ache",
        "tummy ache", "bloat", "bloating", "nausea", "headache", "migraine",
        "indigestion", "what should i eat for", "what to eat for", "how to soothe",
        "remedy for", "help with cramps"
    ]
    if any(q in msg for q in symptom_queries):
        return "wellness_question"
    
    words = set(re.findall(r'\b\w+\b', msg))
    
    # 1. HYDRATION FIRST (so "I had a glass of water" matches hydration first)
    if (words & HYDRATION_KEYWORDS and "water" in msg) or any(x in msg for x in ["water", "coconut water", "electrolyte", " Gatorade", "powerade"]):
        return "hydration_log"
        
    # 2. ALCOHOL (treated as food_log so we extract calories, but flag it)
    if (words & ALCOHOL_KEYWORDS) or any(x in msg for x in ["had a drink", "went out drinking", "grabbed beers"]):
        return "food_log"
        
    # 3. FOOD SECOND
    if words & FOOD_KEYWORDS:
        return "food_log"
        
    if words & SLEEP_KEYWORDS:
        return "sleep_log"
    if words & MOOD_KEYWORDS:
        return "mood_log"
    
    return None


class IntentResult(BaseModel):
    intent: str = Field(description="The classified intent")
    emotional_tone: str = Field(description="The emotional tone of the user: calm, stressed, happy, sad, tired, motivated, neutral")

parser = JsonOutputParser(pydantic_object=IntentResult)

prompt = PromptTemplate(
    template="""Classify this message.
CONTEXT:
{context}

Message: "{message}"

POLICIES:
- If the user is answering a question about food (from context), intent is "food_log".
- Short answers like "no", "yes", "just that", "with chutney" in a food context are "food_log".
- Determine the emotional tone (calm, stressed, happy, sad, tired, motivated, neutral) based on phrasing, punctuation, and word choice.

{format_instructions}
""",
    input_variables=["message", "context"],
    partial_variables={"format_instructions": parser.get_format_instructions()},
)

chain = prompt | llm | parser

VALID_INTENTS = {"food_log", "hydration_log", "mood_log", "sleep_log", 
                 "wellness_question", "casual_chat", "goal_setting", 
                 "progress_check", "greeting"}

def classify_intent(message: str, context: str = "") -> tuple[str, str]:
    # 1. Fast keyword check (with neutral tone assumption)
    keyword_result = keyword_classify(message)
    if keyword_result and keyword_result != "casual_chat":
        # For simple functional logs, assume neutral to save time and prevent state pollution
        return keyword_result, "neutral"
    
    # 2. LLM with context for deep cognitive intent & tone extraction
    try:
        res = chain.invoke({"message": message, "context": context})
        intent = res.get("intent", "casual_chat")
        tone = res.get("emotional_tone", "neutral")
        
        intent = intent if intent in VALID_INTENTS else "casual_chat"
        return intent, tone.lower()
    except Exception as e:
        print(f"Classifier error: {e}")
        return keyword_result or "casual_chat", "neutral"
