from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import schemas
from agents.orchestrator import process_user_message
import models

router = APIRouter()

@router.post("/", response_model=schemas.ChatResponse)
async def chat_endpoint(request: schemas.ChatRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == request.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Store user message
    user_msg = models.ConversationHistory(user_id=user.id, role="user", content=request.message)
    db.add(user_msg)
    db.commit()
    
    # Process with Agent Orchestrator
    response_text, extracted_data = await process_user_message(request.message, user.id, db)
    
    # Update user message with extracted emotional tone
    if extracted_data.get("emotional_tone"):
        user_msg.emotional_tone = extracted_data["emotional_tone"]
        db.commit()

    # Store assistant response
    assistant_msg = models.ConversationHistory(user_id=user.id, role="assistant", content=response_text)
    db.add(assistant_msg)
    db.commit()
    
    # Extract audio_url from extracted_data (may be None if Voicebox is unavailable)
    audio_url = extracted_data.pop("audio_url", None)
    
    return {
        "reply": response_text, 
        "extracted_data": extracted_data,
        "audio_url": audio_url,
    }
