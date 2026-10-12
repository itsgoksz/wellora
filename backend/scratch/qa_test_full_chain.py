import sys
sys.path.insert(0, '.')
import asyncio
from database import SessionLocal
import models
from agents.orchestrator import process_user_message

async def main():
    db = SessionLocal()
    # Clean previous history for user 999
    db.query(models.ConversationHistory).filter(models.ConversationHistory.user_id == 999).delete()
    db.query(models.MealEntry).filter(models.MealEntry.user_id == 999).delete()
    db.query(models.WellnessEntry).filter(models.WellnessEntry.user_id == 999).delete()
    db.commit()

    # Step 1
    print("=== Step 1: User: I had 3 dosas for breakfast today ===")
    db.add(models.ConversationHistory(user_id=999, role="user", content="I had 3 dosas for breakfast today"))
    db.commit()
    response, data = await process_user_message("I had 3 dosas for breakfast today", 999, db)
    db.add(models.ConversationHistory(user_id=999, role="assistant", content=response))
    db.commit()
    print(f"Wellora: {response}")
    print(f"Extracted: {data}\n")

    # Step 2
    print("=== Step 2: User: masala dosa ===")
    db.add(models.ConversationHistory(user_id=999, role="user", content="masala dosa"))
    db.commit()
    
    # Print current DB rows for debugging
    print("--- DB history before Step 2 ---")
    rows = db.query(models.ConversationHistory).filter(models.ConversationHistory.user_id == 999).order_by(models.ConversationHistory.created_at.asc()).all()
    for r in rows:
        print(f"  {r.role}: {r.content} ({r.created_at})")
    
    response, data = await process_user_message("masala dosa", 999, db)
    db.add(models.ConversationHistory(user_id=999, role="assistant", content=response))
    db.commit()
    print(f"Wellora: {response}")
    print(f"Extracted: {data}\n")

    # Step 3
    print("=== Step 3: User: I had coconut chutney ===")
    db.add(models.ConversationHistory(user_id=999, role="user", content="I had coconut chutney"))
    db.commit()
    response, data = await process_user_message("I had coconut chutney", 999, db)
    db.add(models.ConversationHistory(user_id=999, role="assistant", content=response))
    db.commit()
    print(f"Wellora: {response}")
    print(f"Extracted: {data}\n")

    # Step 4
    print("=== Step 4: User: 2 servings ===")
    db.add(models.ConversationHistory(user_id=999, role="user", content="2 servings"))
    db.commit()
    response, data = await process_user_message("2 servings", 999, db)
    db.add(models.ConversationHistory(user_id=999, role="assistant", content=response))
    db.commit()
    print(f"Wellora: {response}")
    print(f"Extracted: {data}\n")

    # Check meals logged
    meals = db.query(models.MealEntry).filter(models.MealEntry.user_id == 999).all()
    print("=== Logged Meals in DB ===")
    for m in meals:
        print(f"{m.meal_type}: {m.original_text} | {m.calories} kcal | protein={m.protein}g")

if __name__ == "__main__":
    asyncio.run(main())
