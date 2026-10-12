import sys
import asyncio
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from agents.extractor import llm, prompt

async def test():
    transcript = "User: I had 3 dosas for breakfast today with coconut chutney, for lunch I had 3 chapatis with rajma gravy"
    semantic_context = ""
    
    formatted = prompt.format(transcript=transcript, semantic_context=semantic_context)
    print("--- PROMPT ---")
    print(formatted)
    print("--------------")
    
    res = llm.invoke(formatted)
    print("--- LLM RESPONSE ---")
    print(res.content)
    print("--------------------")

if __name__ == "__main__":
    asyncio.run(test())
