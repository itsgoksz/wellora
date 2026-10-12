from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from datetime import date, datetime, timedelta
import models

def build_short_term_context(user_id: int, db: Session, limit: int = 12, skip_last: bool = False) -> str:
    """Retrieves the last N messages to build conversational context, respecting active session boundaries."""
    query = db.query(models.ConversationHistory).filter(
        models.ConversationHistory.user_id == user_id
    ).order_by(models.ConversationHistory.created_at.desc(), models.ConversationHistory.id.desc())
    
    # We query the absolute latest messages (including the one just added) so we can accurately detect the session boundary.
    history = query.limit(limit).all()
    
    # Session boundary detection: If we encounter an assistant response that was a resolved confirmation
    # (does NOT contain '?' or '🌸'), or if there is a gap of > 15 minutes, we slice the context.
    active_session_msgs = []
    
    for i, msg in enumerate(history):
        # Boundary condition 1: We encounter a resolved assistant confirmation in past turns
        if i > 0 and msg.role == "assistant":
            content = msg.content or ""
            has_question = "?" in content or "🌸" in content
            if not has_question:
                break
                
        # Boundary condition 2: Time gap > 15 minutes (900 seconds)
        if i > 0:
            prev_msg = history[i - 1]
            t1 = msg.created_at.replace(tzinfo=None) if msg.created_at and msg.created_at.tzinfo else msg.created_at
            t2 = prev_msg.created_at.replace(tzinfo=None) if prev_msg.created_at and prev_msg.created_at.tzinfo else prev_msg.created_at
            if t1 and t2:
                gap = t2 - t1
                if gap.total_seconds() > 900:
                    break
                    
        active_session_msgs.append(msg)
        
    # Reverse to restore chronological order
    active_session_msgs = list(reversed(active_session_msgs))
        
    # Now, if skip_last is True, slice off the very latest message
    if skip_last and active_session_msgs:
        active_session_msgs.pop()
        
    context_lines = []
    for msg in active_session_msgs:
        role_name = "User" if msg.role == "user" else "Wellora"
        context_lines.append(f"{role_name}: {msg.content}")
        
    return "\n".join(context_lines)


def build_meal_context(user_id: int, db: Session) -> str:
    """Retrieves meals logged today."""
    today = date.today()
    meals = db.query(models.MealEntry).filter(
        models.MealEntry.user_id == user_id,
        func.date(models.MealEntry.created_at) == today
    ).all()
    
    if not meals:
        return "No meals logged yet today."
        
    lines = ["Meals today:"]
    for m in meals:
        lines.append(f"- {m.original_text} (Normalized: {m.normalized_foods})")
    return "\n".join(lines)

def get_long_term_insights(user_id: int, db: Session) -> str:
    """Analyzes the last 7 days of data to find patterns."""
    seven_days_ago = datetime.now() - timedelta(days=7)
    
    # Favorite foods
    meals = db.query(models.MealEntry.normalized_foods).filter(
        models.MealEntry.user_id == user_id,
        models.MealEntry.created_at >= seven_days_ago
    ).all()
    
    food_counts = {}
    for m in meals:
        if m.normalized_foods:
            for food in m.normalized_foods.split(", "):
                food_counts[food] = food_counts.get(food, 0) + 1
    
    favorites = sorted(food_counts.items(), key=lambda x: x[1], reverse=True)[:3]
    fav_str = ", ".join([f[0] for f in favorites]) if favorites else "None yet"
    
    # Average water
    water_entries = db.query(models.WellnessEntry.value).filter(
        models.WellnessEntry.user_id == user_id,
        models.WellnessEntry.type == "water",
        models.WellnessEntry.created_at >= seven_days_ago
    ).all()
    
    avg_water = sum([w.value for w in water_entries]) / 7 if water_entries else 0
    
    return f"User's favorite foods lately: {fav_str}. Average daily water: {int(avg_water)}ml."

def update_habit_streak(user_id: int, habit_name: str, db: Session):
    """Updates the streak for a specific habit."""
    habit = db.query(models.HabitMetrics).filter(
        models.HabitMetrics.user_id == user_id,
        models.HabitMetrics.habit_name == habit_name
    ).first()
    
    today = date.today()
    
    if not habit:
        habit = models.HabitMetrics(
            user_id=user_id, 
            habit_name=habit_name, 
            streak_days=1, 
            last_completed=datetime.now()
        )
        db.add(habit)
    else:
        last_date = habit.last_completed.date()
        if last_date == today:
            pass # Already updated today
        elif last_date == today - timedelta(days=1):
            habit.streak_days += 1
            habit.last_completed = datetime.now()
        else:
            habit.streak_days = 1
            habit.last_completed = datetime.now()
    
    db.commit()

def get_semantic_context(user_id: int, db: Session, category: str = None) -> str:
    """Retrieves long-term semantic facts about the user."""
    query = db.query(models.SemanticMemory).filter(models.SemanticMemory.user_id == user_id)
    if category:
        query = query.filter(models.SemanticMemory.category == category)
        
    memories = query.limit(10).all()
    if not memories:
        return "No specific semantic memory known."
        
    facts = [m.fact for m in memories]
    return "User Facts: " + "; ".join(facts)

