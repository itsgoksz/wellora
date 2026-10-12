import sys
import asyncio
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from database import SessionLocal, engine
import models
from agents.orchestrator import process_user_message

async def run_regression_test():
    db = SessionLocal()
    
    # 1. Clear DB entries
    db.query(models.MealEntry).filter(models.MealEntry.user_id == 1).delete()
    db.commit()
    
    message = "I had 3 dosas with coconut chutney for breakfast and 2 chapatis with rajma curry for lunch"
    print(f"Testing Message: '{message}'")
    
    reply, data = await process_user_message(message, 1, db)
    
    print("\n--- RESULTS ---")
    print("Wellora Reply:", reply)
    
    meals = db.query(models.MealEntry).filter(models.MealEntry.user_id == 1).all()
    print(f"\nSaved Meal Entries in DB: {len(meals)}")
    
    assert len(meals) == 2, f"Expected 2 meals, got {len(meals)}"
    
    breakfast = [m for m in meals if m.meal_type == "breakfast"][0]
    lunch = [m for m in meals if m.meal_type == "lunch"][0]
    
    print(f"Breakfast Original Text: '{breakfast.original_text}'")
    print(f"Lunch Original Text: '{lunch.original_text}'")
    
    # Assertions to ensure no cross-pollution
    assert "burfi" not in breakfast.original_text.lower(), "Polluted breakfast with burfi!"
    assert "chutney" not in lunch.original_text.lower(), "Polluted lunch with chutney!"
    assert "curry" not in breakfast.original_text.lower() and "rajma" not in breakfast.original_text.lower(), "Polluted breakfast with curry/rajma!"
    
    print("\n🎉 REGRESSION TEST PASSED PERFECTLY! NO CROSS-MEAL POLLUTION DETECTED!")
    db.close()

if __name__ == "__main__":
    asyncio.run(run_regression_test())
