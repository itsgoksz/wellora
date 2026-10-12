import sys
import asyncio
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from database import SessionLocal, engine
import models
from agents.orchestrator import process_user_message

async def run_flow_test():
    db = SessionLocal()
    
    # Clean previous meal and conversation history entries
    db.query(models.MealEntry).filter(models.MealEntry.user_id == 1).delete()
    db.query(models.ConversationHistory).filter(models.ConversationHistory.user_id == 1).delete()
    db.commit()
    
    # --- TURN 1 ---
    print("\n--- TURN 1 ---")
    msg1 = "I had coconut chutney"
    print(f"User: '{msg1}'")
    
    # Store user message
    user_msg = models.ConversationHistory(user_id=1, role="user", content=msg1)
    db.add(user_msg)
    db.commit()
    
    reply1, data1 = await process_user_message(msg1, 1, db)
    print(f"Wellora: '{reply1}'")
    print("Needs Followup:", data1.get("needs_followup"))
    
    # Store assistant response
    assist_msg = models.ConversationHistory(user_id=1, role="assistant", content=reply1)
    db.add(assist_msg)
    db.commit()
    
    assert data1.get("needs_followup") == True, "Should request servings follow-up!"
    assert "servings of chutney" in reply1, "Incorrect follow-up question!"
    
    # --- TURN 2 ---
    print("\n--- TURN 2 ---")
    msg2 = "2 servings"
    print(f"User: '{msg2}'")
    
    # Store user message
    user_msg = models.ConversationHistory(user_id=1, role="user", content=msg2)
    db.add(user_msg)
    db.commit()
    
    reply2, data2 = await process_user_message(msg2, 1, db)
    print(f"Wellora: '{reply2}'")
    print("Needs Followup:", data2.get("needs_followup"))
    
    # Store assistant response
    assist_msg = models.ConversationHistory(user_id=1, role="assistant", content=reply2)
    db.add(assist_msg)
    db.commit()
    
    assert data2.get("needs_followup") == False, "Should resolve and save!"
    
    # Check DB
    meals = db.query(models.MealEntry).filter(models.MealEntry.user_id == 1).all()
    print(f"DB Saved Meals Count: {len(meals)}")
    for m in meals:
        print(f"- Meal: {m.original_text} | Normalized: {m.normalized_foods} | Cal: {m.calories} kcal")
    assert any("coconut chutney" in m.original_text.lower() for m in meals), "Should save chutney!"
    
    # Clear for next flow
    db.query(models.MealEntry).filter(models.MealEntry.user_id == 1).delete()
    db.query(models.ConversationHistory).filter(models.ConversationHistory.user_id == 1).delete()
    db.commit()
    
    # --- TURN 3 ---
    print("\n--- TURN 3 ---")
    msg3 = "I had a coffee"
    print(f"User: '{msg3}'")
    
    # Store user message
    user_msg = models.ConversationHistory(user_id=1, role="user", content=msg3)
    db.add(user_msg)
    db.commit()
    
    reply3, data3 = await process_user_message(msg3, 1, db)
    print(f"Wellora: '{reply3}'")
    print("Needs Followup:", data3.get("needs_followup"))
    
    # Store assistant response
    assist_msg = models.ConversationHistory(user_id=1, role="assistant", content=reply3)
    db.add(assist_msg)
    db.commit()
    
    assert data3.get("needs_followup") == True, "Should request coffee mug follow-up!"
    assert "coffee mug or a tea mug" in reply3, "Incorrect follow-up question!"
    
    # --- TURN 4 ---
    print("\n--- TURN 4 ---")
    msg4 = "a coffee mug and 2 cups"
    print(f"User: '{msg4}'")
    
    # Store user message
    user_msg = models.ConversationHistory(user_id=1, role="user", content=msg4)
    db.add(user_msg)
    db.commit()
    
    reply4, data4 = await process_user_message(msg4, 1, db)
    print(f"Wellora: '{reply4}'")
    print("Needs Followup:", data4.get("needs_followup"))
    
    # Store assistant response
    assist_msg = models.ConversationHistory(user_id=1, role="assistant", content=reply4)
    db.add(assist_msg)
    db.commit()
    
    assert data4.get("needs_followup") == False, "Should resolve and save!"
    
    # Check DB
    meals = db.query(models.MealEntry).filter(models.MealEntry.user_id == 1).all()
    print(f"DB Saved Meals Count: {len(meals)}")
    for m in meals:
        print(f"- Meal: {m.original_text} | Normalized: {m.normalized_foods} | Cal: {m.calories} kcal")
    
    print("\n🎉 ALL MULTI-TURN DYNAMIC CHAT FLOW TESTS PASSED PERFECTLY!")
    db.close()

if __name__ == "__main__":
    asyncio.run(run_flow_test())
