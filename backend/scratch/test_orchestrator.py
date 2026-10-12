import sys
import asyncio
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from database import SessionLocal, engine
import models
from agents.orchestrator import process_user_message

# Make sure tables are created
models.Base.metadata.create_all(bind=engine)

async def test():
    db = SessionLocal()
    # Ensure test user 1 exists
    user = db.query(models.User).filter(models.User.id == 1).first()
    if not user:
        user = models.User(id=1, email="test@wellora.app", name="User")
        db.add(user)
        db.commit()

    # Clear previous meals for test
    db.query(models.MealEntry).filter(models.MealEntry.user_id == 1).delete()
    db.commit()

    message = "I had 3 dosas for breakfast today with coconut chutney, for lunch I had 3 chapatis with rajma gravy"
    print(f"User message: '{message}'\n")

    # Run orchestrator
    reply, data = await process_user_message(message, 1, db)

    print(f"Wellora Reply: '{reply}'\n")
    print("Extracted Data:", data, "\n")

    # Fetch database entries
    meals = db.query(models.MealEntry).filter(models.MealEntry.user_id == 1).all()
    print(f"Number of Database Meal Entries Saved: {len(meals)}")
    for m in meals:
        print(f"- ID: {m.id} | Meal Type: {m.meal_type} | Original Text: {m.original_text} | Normalized: {m.normalized_foods} | Calories: {m.calories} kcal | Protein: {m.protein}g")

    db.close()

if __name__ == "__main__":
    asyncio.run(test())
