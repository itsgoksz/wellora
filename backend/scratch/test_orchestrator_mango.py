import sys
import asyncio
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from database import SessionLocal
from agents.orchestrator import process_user_message
import models

async def test_flow():
    print("Testing complete Orchestrator flow for ice cream...")
    db = SessionLocal()
    try:
        # Create user 1 if not exists
        user = db.query(models.User).filter(models.User.id == 1).first()
        if not user:
            user = models.User(id=1, email="test@wellora.app", name="User")
            db.add(user)
            db.commit()
            
        message = "how many calories does a scoop of ice cream have?"
        
        # Add to history
        user_msg = models.ConversationHistory(user_id=1, role="user", content=message)
        db.add(user_msg)
        db.commit()
        
        reply, data = await process_user_message(message, 1, db)
        print("\n=== RESPONSE FROM WELLORA ===")
        print(f"Reply: {reply}")
        print(f"Structured Data: {data}")
        print("=============================")
        
        assert "126" in reply or "126 kcal" in reply or "126 calories" in reply or "125.69" in reply, f"Expected 126 calories in reply, got: '{reply}'"
        print("\n[ORCHESTRATOR FLOW TEST PASSED SUCCESSFULLY!]")
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_flow())
