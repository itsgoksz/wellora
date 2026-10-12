from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date, datetime, timedelta
from database import get_db
import schemas
import models

router = APIRouter()


def _get_time_period():
    """Return the current time period for emotional adaptation."""
    hour = datetime.now().hour
    if 5 <= hour < 12:
        return "morning"
    elif 12 <= hour < 17:
        return "afternoon"
    elif 17 <= hour < 21:
        return "evening"
    else:
        return "night"


def _get_meal_time_label(created_at):
    """Return a human-readable time from a datetime."""
    if created_at:
        return created_at.strftime("%-I:%M %p").lower()
    return ""


def _generate_contextual_tags(meal):
    """Generate intelligent contextual tags for a meal entry."""
    tags = []
    cal = meal.calories or 0
    protein = meal.protein or 0
    carbs = meal.carbs or 0
    fats = meal.fats or 0
    meal_type = (meal.meal_type or "").lower()
    
    if protein > 20:
        tags.append("high protein")
    if carbs > 80:
        tags.append("carb-heavy")
    if fats > 30:
        tags.append("rich meal")
    if cal > 600:
        tags.append("energy dense")
    if cal < 150 and cal > 0:
        tags.append("light bite")
    
    # Time-based tags
    if meal.created_at:
        hour = meal.created_at.hour
        if meal_type == "dinner" and hour >= 21:
            tags.append("late dinner")
        elif meal_type == "breakfast" and hour >= 11:
            tags.append("late breakfast")
        elif meal_type == "breakfast" and hour < 7:
            tags.append("early riser")
    
    return tags[:2]  # Max 2 tags per meal


def _build_daily_rhythm(meals, water_ml, time_period, is_today):
    """Build a narrative daily rhythm from the day's data."""
    rhythm = []
    
    meal_types_logged = set()
    total_cal = 0
    for m in meals:
        mt = (m.meal_type or "snack").lower()
        meal_types_logged.add(mt)
        total_cal += (m.calories or 0)
    
    # Morning context
    if "breakfast" in meal_types_logged:
        breakfast_meals = [m for m in meals if (m.meal_type or "").lower() == "breakfast"]
        bcal = sum(m.calories or 0 for m in breakfast_meals)
        if bcal < 200:
            rhythm.append({"icon": "☀️", "text": "Light breakfast", "tone": "neutral"})
        elif bcal > 500:
            rhythm.append({"icon": "☀️", "text": "Hearty breakfast", "tone": "positive"})
        else:
            rhythm.append({"icon": "☀️", "text": "Balanced breakfast", "tone": "positive"})
    elif is_today and time_period in ["afternoon", "evening", "night"]:
        rhythm.append({"icon": "☀️", "text": "Breakfast not logged", "tone": "gentle"})
    
    # Lunch context
    if "lunch" in meal_types_logged:
        lunch_meals = [m for m in meals if (m.meal_type or "").lower() == "lunch"]
        lcal = sum(m.calories or 0 for m in lunch_meals)
        if lcal > 700:
            rhythm.append({"icon": "🔥", "text": "High-energy lunch", "tone": "neutral"})
        else:
            rhythm.append({"icon": "🍽️", "text": "Lunch logged", "tone": "positive"})
    elif is_today and time_period in ["evening", "night"]:
        rhythm.append({"icon": "🍽️", "text": "Lunch not logged yet", "tone": "gentle"})
    
    # Dinner context
    if "dinner" in meal_types_logged:
        rhythm.append({"icon": "🌙", "text": "Dinner logged", "tone": "positive"})
    elif is_today and time_period == "night":
        rhythm.append({"icon": "🌙", "text": "Dinner not logged yet", "tone": "gentle"})
    
    # Snack context
    if "snack" in meal_types_logged:
        snack_count = len([m for m in meals if (m.meal_type or "").lower() == "snack"])
        if snack_count > 2:
            rhythm.append({"icon": "🍪", "text": f"{snack_count} snacks throughout the day", "tone": "neutral"})
        else:
            rhythm.append({"icon": "🍪", "text": "Snack logged", "tone": "neutral"})
    
    # Hydration
    if water_ml > 2000:
        rhythm.append({"icon": "💧", "text": "Great hydration today", "tone": "positive"})
    elif water_ml > 0 and water_ml < 1000:
        rhythm.append({"icon": "💧", "text": "Hydration below target", "tone": "gentle"})
    elif water_ml == 0 and is_today and len(meals) > 0:
        rhythm.append({"icon": "💧", "text": "No water logged yet", "tone": "gentle"})
        
    # Alcohol
    alcohol_meals = [m for m in meals if getattr(m, 'is_alcohol', False)]
    if alcohol_meals:
        rhythm.append({"icon": "🍷", "text": "Mindful alcohol log", "tone": "neutral"})
    
    # Overall energy
    if total_cal > 1800:
        rhythm.append({"icon": "⚡", "text": "High energy day", "tone": "neutral"})
    elif total_cal > 0 and total_cal < 800 and time_period in ["evening", "night"]:
        rhythm.append({"icon": "🌿", "text": "Light eating day", "tone": "gentle"})
    
    # Day still unfolding
    if is_today and time_period != "night" and len(meals) > 0:
        rhythm.append({"icon": "✨", "text": "Your day is still unfolding", "tone": "calm"})
    
    return rhythm


def _generate_smart_insight(meals, water_ml, total_protein, total_carbs, total_fats, total_fibre, total_calories, is_today, time_period):
    """Generate a deeply contextual, behavioral insight."""
    meal_count = len(meals)
    
    if meal_count == 0:
        if is_today:
            if time_period == "morning":
                return "A fresh day ahead. Log your first meal whenever you're ready."
            elif time_period == "afternoon":
                return "Afternoon already — your wellness journal is waiting for you."
            elif time_period == "evening":
                return "The evening is here. A good time to reflect on what you've had today."
            else:
                return "A quiet day in your journal. Tomorrow is a fresh start."
        else:
            return "No meals were logged on this day."
    
    insights = []
    
    # Alcohol analysis
    alcohol_meals = [m for m in meals if getattr(m, 'is_alcohol', False)]
    if alcohol_meals:
        if water_ml < 1500:
            insights.append("You logged some alcohol today with lower hydration. Consider resetting with some extra water to ease recovery")
        else:
            insights.append("Excellent job balancing your alcohol consumption with high hydration today")
            
    # Protein analysis
    if total_protein > 60:
        insights.append("your protein intake is strong today")
    elif total_protein < 20 and meal_count >= 2:
        insights.append("your meals have been light on protein so far")
    
    # Hydration cross-reference (if not already handled by alcohol)
    if not alcohol_meals:
        if water_ml < 1000 and meal_count > 0:
            if insights:
                insights[-1] += ", but hydration is still unusually low"
            else:
                insights.append("You've been eating well, but hydration needs attention")
        elif water_ml > 2000:
            insights.append("excellent hydration today")
    
    # Fibre insight
    if total_fibre > 20:
        insights.append("Good fibre intake — your gut will thank you")
    
    # Carb-heavy day
    if total_carbs > 200 and total_protein < 30:
        insights.append("Today has been carb-heavy with lower protein — consider balancing your next meal")
    
    # Caloric density
    if total_calories > 1500 and meal_count <= 2:
        insights.append("High caloric density across fewer meals — spacing them out could help energy levels")
    
    # Balanced day
    if total_protein > 40 and total_carbs > 100 and total_fats > 30 and water_ml > 1500 and not alcohol_meals:
        return "A beautifully balanced day — strong across all macros with good hydration. Keep this rhythm going."
    
    if insights:
        # Capitalize first letter and join
        result = ". ".join(insights)
        result = result[0].upper() + result[1:]
        if not result.endswith("."):
            result += "."
        return result
    
    # Fallback
    if is_today:
        return f"You've logged {meal_count} meal{'s' if meal_count > 1 else ''} so far — keep tracking at your own pace."
    else:
        return f"You logged {meal_count} meal{'s' if meal_count > 1 else ''} on this day."


def _compute_wellness_modules(total_calories, total_protein, total_carbs, total_fats, total_fibre, water_ml, meal_count):
    """Compute adaptive wellness module scores with contextual explanations."""
    modules = []
    
    # Energy Balance
    energy_score = min(100, int((total_calories / 2000) * 100))
    if total_calories == 0:
        energy_reason = "No meals logged yet"
    elif total_calories < 800:
        energy_reason = "Light intake — consider eating more"
    elif total_calories > 2200:
        energy_reason = "Above typical daily target"
    else:
        energy_reason = "On track for the day"
    modules.append({
        "key": "energy",
        "title": "Energy",
        "value": total_calories,
        "unit": "kcal",
        "score": energy_score,
        "reason": energy_reason,
        "color": "orange"
    })
    
    # Protein quality
    protein_score = min(100, int((total_protein / 60) * 100))
    if total_protein == 0:
        protein_reason = "No protein logged"
    elif total_protein < 20:
        protein_reason = "Below recommended intake"
    elif total_protein > 50:
        protein_reason = "Strong protein day"
    else:
        protein_reason = "Moderate — aim higher if active"
    modules.append({
        "key": "protein",
        "title": "Protein",
        "value": round(total_protein, 1),
        "unit": "g",
        "score": protein_score,
        "reason": protein_reason,
        "color": "emerald"
    })
    
    # Hydration
    hydration_score = min(100, int((water_ml / 2500) * 100))
    if water_ml == 0:
        hydration_reason = "No hydration logged"
    elif water_ml < 1000:
        hydration_reason = "Below target — drink more water"
    elif water_ml > 2000:
        hydration_reason = "Well hydrated today"
    else:
        hydration_reason = "Getting there — keep sipping"
    modules.append({
        "key": "hydration",
        "title": "Hydration",
        "value": water_ml,
        "unit": "ml",
        "score": hydration_score,
        "reason": hydration_reason,
        "color": "blue"
    })
    
    # Nutrition quality (balance of macros)
    if total_calories > 0:
        p_pct = (total_protein * 4) / total_calories * 100 if total_calories else 0
        c_pct = (total_carbs * 4) / total_calories * 100 if total_calories else 0
        f_pct = (total_fats * 9) / total_calories * 100 if total_calories else 0
        
        # Ideal: ~25% protein, ~45% carbs, ~30% fats
        balance = 100 - abs(p_pct - 25) - abs(c_pct - 45) * 0.5 - abs(f_pct - 30) * 0.5
        balance_score = max(0, min(100, int(balance)))
        
        if balance_score > 75:
            balance_reason = "Well-balanced macro distribution"
        elif p_pct < 15:
            balance_reason = "Low protein ratio"
        elif f_pct > 45:
            balance_reason = "Fat-heavy macro split"
        else:
            balance_reason = "Moderate balance"
    else:
        balance_score = 0
        balance_reason = "No data yet"
    
    modules.append({
        "key": "balance",
        "title": "Balance",
        "value": balance_score,
        "unit": "/100",
        "score": balance_score,
        "reason": balance_reason,
        "color": "purple"
    })
    
    return modules


@router.get("/{user_id}", response_model=schemas.DashboardSummary)
def get_dashboard_summary(user_id: int, date: str = None, db: Session = Depends(get_db)):
    # Parse target date timezone-safely
    if date:
        try:
            target_date = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            target_date = datetime.now().date()
    else:
        target_date = datetime.now().date()
        
    today = datetime.now().date()
    is_today = target_date == today
    time_period = _get_time_period() if is_today else "evening"
    
    # Aggregate Meals for target date
    meals_today = db.query(models.MealEntry).filter(
        models.MealEntry.user_id == user_id,
        func.date(models.MealEntry.created_at) == target_date
    ).order_by(models.MealEntry.created_at.asc()).all()
    
    total_calories = sum((m.calories or 0) for m in meals_today)
    total_protein = sum((m.protein or 0.0) for m in meals_today)
    total_carbs = sum((m.carbs or 0.0) for m in meals_today)
    total_fats = sum((m.fats or 0.0) for m in meals_today)
    total_fibre = sum((m.fibre or 0.0) for m in meals_today)
    
    # Build rich meal entries with time and contextual tags
    recent_meals = []
    for m in meals_today:
        tags = _generate_contextual_tags(m)
        recent_meals.append({
            "id": m.id,
            "description": m.original_text, 
            "normalized": m.normalized_foods,
            "calories": m.calories, 
            "protein": m.protein,
            "carbs": m.carbs,
            "fats": m.fats,
            "fibre": m.fibre,
            "meal_type": m.meal_type,
            "is_alcohol": getattr(m, "is_alcohol", False),
            "time": _get_meal_time_label(m.created_at),
            "tags": tags,
        })
    
    # Aggregate Water
    wellness_today = db.query(models.WellnessEntry).filter(
        models.WellnessEntry.user_id == user_id,
        func.date(models.WellnessEntry.created_at) == target_date,
        models.WellnessEntry.type == "water"
    ).all()
    
    water_ml = sum((w.value or 0) for w in wellness_today)
    
    # Get emotional tones from today's conversations
    conversations = db.query(models.ConversationHistory).filter(
        models.ConversationHistory.user_id == user_id,
        func.date(models.ConversationHistory.created_at) == target_date
    ).all()
    
    # Generate smart insight
    insight = _generate_smart_insight(
        meals_today, water_ml, total_protein, total_carbs, total_fats, total_fibre, total_calories, is_today, time_period
    )
    
    # Wellness score heuristic
    meal_count = len(meals_today)
    score = 50.0
    score += min(meal_count * 10, 20)
    score += min(total_protein / 5, 15)
    score += min(water_ml / 500, 15)
    
    # Alcohol penalties
    alcohol_today = any(getattr(m, 'is_alcohol', False) for m in meals_today)
    if alcohol_today:
        score -= 15.0 # Direct deduction for drinking today
        
    # Check frequency over the last 7 days
    seven_days_ago = datetime.now() - timedelta(days=7)
    recent_alcohol_days = db.query(func.date(models.MealEntry.created_at)).filter(
        models.MealEntry.user_id == user_id,
        models.MealEntry.created_at >= seven_days_ago,
        models.MealEntry.is_alcohol == True
    ).distinct().count()
    
    if recent_alcohol_days >= 3:
        score -= 15.0
    elif recent_alcohol_days >= 1:
        score -= 5.0
        
    score = max(0.0, min(score, 100.0))
    
    # Alcohol Recovery Suggestions
    recovery_alert = None
    recovery_suggestions = []
    
    if alcohol_today:
        if water_ml < 1500:
            recovery_alert = {
                "title": "Recovery Focus Needed",
                "message": "Alcohol was logged alongside low hydration. Sip some extra water to ease recovery and maintain sleep quality.",
                "severity": "warning"
            }
            recovery_suggestions = [
                {"text": "Drink 500ml Water", "action": "drink_water"},
                {"text": "Add Electrolytes", "action": "add_electrolytes"},
                {"text": "Herbal Tea Routine", "action": "herbal_tea"}
            ]
        else:
            recovery_alert = {
                "title": "Balanced Habit Logged",
                "message": "Excellent mindful drinking practice. Your hydration levels are perfectly aligned to support alcohol processing.",
                "severity": "success"
            }
            recovery_suggestions = [
                {"text": "Keep Hydrated", "action": "sip_water"},
                {"text": "Magnesium Support", "action": "magnesium"}
            ]
            
    # Fetch Streaks
    habits = db.query(models.HabitMetrics).filter(models.HabitMetrics.user_id == user_id).all()
    streaks = {h.habit_name: h.streak_days for h in habits}
    
    # Build daily rhythm
    daily_rhythm = _build_daily_rhythm(meals_today, water_ml, time_period, is_today)
    
    # Compute wellness modules
    wellness_modules = _compute_wellness_modules(
        total_calories, total_protein, total_carbs, total_fats, total_fibre, int(water_ml), meal_count
    )
    
    return {
        "total_calories": total_calories,
        "total_protein": total_protein,
        "total_carbs": total_carbs,
        "total_fats": total_fats,
        "total_fibre": total_fibre,
        "water_ml": int(water_ml),
        "wellness_score": round(score, 1),
        "recent_meals": recent_meals,
        "insight_text": insight,
        "streaks": streaks,
        "time_period": time_period,
        "daily_rhythm": daily_rhythm,
        "wellness_modules": wellness_modules,
        "recovery_alert": recovery_alert,
        "recovery_suggestions": recovery_suggestions,
    }

@router.delete("/meal/{meal_id}")
def delete_meal(meal_id: int, db: Session = Depends(get_db)):
    meal = db.query(models.MealEntry).filter(models.MealEntry.id == meal_id).first()
    if meal:
        db.delete(meal)
        db.commit()
    return {"status": "success"}

@router.post("/quick-log/water/{user_id}/{ml}")
def quick_log_water(user_id: int, ml: float, db: Session = Depends(get_db)):
    wellness = models.WellnessEntry(
        user_id=user_id,
        type="water",
        value=ml,
        notes="Quick log from dashboard suggestions"
    )
    db.add(wellness)
    db.commit()
    return {"status": "success", "water_ml": ml}
