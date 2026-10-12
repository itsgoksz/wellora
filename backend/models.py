from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    name = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    meals = relationship("MealEntry", back_populates="user")
    wellness_entries = relationship("WellnessEntry", back_populates="user")
    summaries = relationship("DailySummary", back_populates="user")
    habits = relationship("HabitMetrics", back_populates="user")
    preferences = relationship("UserPreferences", back_populates="user", uselist=False)

class UserPreferences(Base):
    __tablename__ = "user_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    dietary_preferences = Column(String) 
    caloric_goal = Column(Integer, default=2000)
    water_goal_ml = Column(Integer, default=2500)
    sleep_goal_hrs = Column(Float, default=8.0)
    
    user = relationship("User", back_populates="preferences")

class MealEntry(Base):
    __tablename__ = "meal_entries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    original_text = Column(String)
    normalized_foods = Column(String) # Comma separated
    meal_type = Column(String) # breakfast, lunch, dinner, snack
    quantity_notes = Column(String)
    
    calories = Column(Integer, nullable=True)
    protein = Column(Float, nullable=True)
    carbs = Column(Float, nullable=True)
    fats = Column(Float, nullable=True)
    fibre = Column(Float, nullable=True)
    
    is_alcohol = Column(Boolean, default=False)
    
    confidence_score = Column(Float, default=1.0)
    needs_followup = Column(Boolean, default=False)
    followup_resolved = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="meals")

class WellnessEntry(Base):
    __tablename__ = "wellness_entries"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    type = Column(String) # sleep, water, activity, mood
    value = Column(Float)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="wellness_entries")

class DailySummary(Base):
    __tablename__ = "daily_summaries"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    date = Column(DateTime(timezone=True), server_default=func.now()) 
    total_calories = Column(Integer, default=0)
    total_protein = Column(Float, default=0)
    water_ml = Column(Integer, default=0)
    wellness_score = Column(Float, default=0.0) 
    insight = Column(Text, nullable=True) 
    
    user = relationship("User", back_populates="summaries")

class HabitMetrics(Base):
    __tablename__ = "habit_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    habit_name = Column(String) 
    streak_days = Column(Integer, default=0)
    last_completed = Column(DateTime(timezone=True))
    
    user = relationship("User", back_populates="habits")

class ConversationHistory(Base):
    __tablename__ = "conversation_history"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    role = Column(String) 
    content = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class SemanticMemory(Base):
    __tablename__ = "semantic_memories"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    fact = Column(String) 
    category = Column(String) # food_preference, routine, emotional_trigger
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User")
