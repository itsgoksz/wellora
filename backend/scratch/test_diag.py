import sys
import asyncio
from pathlib import Path
from datetime import datetime, timedelta
sys.path.append(str(Path(__file__).resolve().parent.parent))

from database import SessionLocal
import models
from agents.memory import build_short_term_context

async def diagnose():
    db = SessionLocal()
    db.query(models.ConversationHistory).filter(models.ConversationHistory.user_id == 1).delete()
    db.commit()
    
    # Simulate Turn 1
    t1 = datetime.utcnow() - timedelta(seconds=10)
    msg1 = models.ConversationHistory(user_id=1, role="user", content="I had coconut chutney", created_at=t1)
    db.add(msg1)
    db.commit()
    
    t2 = datetime.utcnow() - timedelta(seconds=5)
    reply1 = models.ConversationHistory(user_id=1, role="assistant", content="Approximately how many servings of chutney did you have? 🌸", created_at=t2)
    db.add(reply1)
    db.commit()
    
    # Simulate Turn 2
    t3 = datetime.utcnow()
    msg2 = models.ConversationHistory(user_id=1, role="user", content="2 servings", created_at=t3)
    db.add(msg2)
    db.commit()
    
    # Fetch history
    history = db.query(models.ConversationHistory).filter(models.ConversationHistory.user_id == 1).order_by(models.ConversationHistory.created_at.desc()).all()
    print("DB HISTORY RECORD COUNT:", len(history))
    for h in history:
        print(f"[{h.created_at}] {h.role}: {h.content}")
        
    context = build_short_term_context(1, db, skip_last=True)
    print("\nBUILD SHORT TERM CONTEXT OUTPUT:")
    print(repr(context))
    db.close()

if __name__ == "__main__":
    asyncio.run(diagnose())
