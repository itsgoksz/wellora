from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    name: str

class UserCreate(UserBase):
    pass

class UserResponse(UserBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class ChatRequest(BaseModel):
    message: str
    user_id: int

class ChatResponse(BaseModel):
    reply: str
    extracted_data: Optional[dict] = None
    audio_url: Optional[str] = None

class DashboardSummary(BaseModel):
    total_calories: int
    total_protein: float
    total_carbs: float
    total_fats: float
    total_fibre: float
    water_ml: int
    wellness_score: float
    recent_meals: List[dict]
    insight_text: str
    streaks: dict
    # New contextual fields
    time_period: Optional[str] = "afternoon"
    daily_rhythm: Optional[List[dict]] = []
    wellness_modules: Optional[List[dict]] = []
    recovery_alert: Optional[dict] = None
    recovery_suggestions: Optional[List[dict]] = []
