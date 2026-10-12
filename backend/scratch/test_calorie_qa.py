import sys
import os
import asyncio
from database import SessionLocal
import models
from agents.orchestrator import process_user_message
from agents.food_db import lookup_food

async def main():
    db = SessionLocal()
    user_id = 1
    
    # Clean up previous conversation history and meals for user 1 to ensure a clean slate
    db.query(models.ConversationHistory).filter(models.ConversationHistory.user_id == user_id).delete()
    db.query(models.MealEntry).filter(models.MealEntry.user_id == user_id).delete()
    db.commit()
    
    print("\n" + "="*60)
    print("TEST 1: Calorie and Macronutrient Question-Answering")
    print("="*60)
    
    # 1. Calorie Query Test
    message = "how many calories does chicken biriyani have?"
    print(f"\nUser: {message}")
    response_text, extracted_data = await process_user_message(message, user_id, db)
    print(f"Wellora: {response_text}")
    print(f"Extracted Data: {extracted_data}")
    
    assert "723" in response_text or "723" in str(extracted_data), "Calorie count not correctly resolved!"
    print("\n[PASS] Calorie question-answering matches exact CSV database!")

    print("\n" + "="*60)
    print("TEST 2: Two-Turn Idli + Chutney + Sambar Flow")
    print("="*60)
    
    # Turn 1: Initial meal description with serving counts
    # Clean history again
    db.query(models.ConversationHistory).filter(models.ConversationHistory.user_id == user_id).delete()
    db.query(models.MealEntry).filter(models.MealEntry.user_id == user_id).delete()
    db.commit()
    
    message = "I had 2 idlis with one serving of chutney and one serving of sambar for breakfast"
    print(f"\nUser (Turn 1): {message}")
    
    # Record user message in history
    hist = models.ConversationHistory(user_id=user_id, role="user", content=message)
    db.add(hist)
    db.commit()
    
    response_text, extracted_data = await process_user_message(message, user_id, db)
    print(f"Wellora (Turn 1): {response_text}")
    
    # Record assistant message in history
    hist_assist = models.ConversationHistory(user_id=user_id, role="assistant", content=response_text)
    db.add(hist_assist)
    db.commit()
    
    # Assert that it asks for the chutney type (not serving size!)
    assert "type" in response_text.lower() or "what kind" in response_text.lower(), "Should ask for chutney type!"
    assert "how many" not in response_text.lower() and "how much" not in response_text.lower(), "Should NOT ask for serving count, it was already specified!"
    print("[PASS] Wellora correctly clarifies ONLY chutney type, preserving serving info!")
    
    # Turn 2: User clarifies type
    clarify_msg = "coconut chutney"
    print(f"\nUser (Turn 2): {clarify_msg}")
    
    # Record user turn 2 message
    hist2 = models.ConversationHistory(user_id=user_id, role="user", content=clarify_msg)
    db.add(hist2)
    db.commit()
    
    response_text2, extracted_data2 = await process_user_message(clarify_msg, user_id, db)
    print(f"Wellora (Turn 2): {response_text2}")
    print(f"Extracted Data (Turn 2): {extracted_data2}")
    
    # Verify that the final meal entry contains:
    # 2 Idlis (2*34=68kcal), 1 Coconut chutney (67kcal), 1 Sambar (249kcal) -> Total = 384kcal
    meal = db.query(models.MealEntry).filter(models.MealEntry.user_id == user_id).first()
    assert meal is not None, "Meal entry was not logged!"
    print(f"\nSaved Meal in DB: {meal.original_text} | Calories: {meal.calories} kcal")
    
    assert "Coconut serving of sambar" not in meal.original_text, "Sambar got polluted with coconut!"
    assert "coconut chutney" in meal.normalized_foods.lower(), "Coconut chutney missing!"
    assert "sambar" in meal.normalized_foods.lower(), "Sambar missing!"
    assert "idli" in meal.normalized_foods.lower(), "Idli missing!"
    assert meal.calories == 384, f"Calorie summation wrong! Expected 384, got {meal.calories}"
    
    print("\n[PASS] Multi-turn idli + chutney + sambar logging and calorie calculations are perfect!")
    db.close()

if __name__ == "__main__":
    asyncio.run(main())
