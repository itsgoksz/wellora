from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from database import engine, Base
import database
import models
from routers import chat, dashboard, users

# Create DB tables
models.Base.metadata.create_all(bind=engine)

# Ensure is_alcohol exists in meal_entries for sqlite database migration
from sqlalchemy import text
try:
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE meal_entries ADD COLUMN is_alcohol BOOLEAN DEFAULT 0"))
        conn.commit()
except Exception:
    pass

app = FastAPI(
    title="Wellora API",
    description="AI Companion for Wellness and Lifestyle — Voice-Enabled",
    version="2.0.0",
)


@app.on_event("startup")
async def startup():
    # Seed default user
    db = next(database.get_db())
    if not db.query(models.User).filter(models.User.id == 1).first():
        user = models.User(id=1, email="test@wellora.app", name="User")
        db.add(user)
        db.commit()

    # Create audio cache directory
    audio_dir = Path(__file__).parent / "audio_cache"
    audio_dir.mkdir(exist_ok=True)

    # Cleanup old audio files on startup
    from agents.voicebox_service import cleanup_old_audio

    cleanup_old_audio(max_age_hours=24)


# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static audio directory for serving generated speech files
audio_dir = Path(__file__).parent / "audio_cache"
audio_dir.mkdir(exist_ok=True)
app.mount("/audio", StaticFiles(directory=str(audio_dir)), name="audio")

# Include routers
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(users.router, prefix="/api/users", tags=["users"])


@app.get("/")
def read_root():
    return {"message": "Welcome to Wellora API v2 — Voice-Enabled"}


@app.get("/api/voice/health")
async def voicebox_health():
    """Check if the Voicebox TTS server is reachable."""
    from agents.voicebox_service import health_check

    return await health_check()


@app.get("/api/voice/recent")
async def recent_audio():
    """Get the most recently generated audio files (for debugging)."""
    from agents.voicebox_service import get_latest_audio

    return {"audio_files": get_latest_audio(5)}
