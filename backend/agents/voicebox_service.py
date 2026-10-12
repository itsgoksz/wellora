"""
Wellora Voicebox Service
------------------------
Async TTS generation via Voicebox local REST API.
Handles retries, timeouts, queue management, and graceful fallbacks.

Architecture:
- Non-blocking async generation via httpx
- Audio files saved to static directory for serving
- Voicebox failures never block the conversation
- Designed for future streaming TTS upgrade
"""

import httpx
import asyncio
import uuid
import os
from pathlib import Path
from typing import Optional

# ── Configuration ────────────────────────────────────────────────────────
VOICEBOX_URL = "http://127.0.0.1:17493/generate"
VOICEBOX_PROFILE_ID = "51f51d17-d8a3-4109-b23e-ac8d7c02f8ff"
VOICEBOX_ENGINE = "kokoro"

# Audio output directory — served as static files by FastAPI
AUDIO_DIR = Path(__file__).resolve().parent.parent / "audio_cache"
AUDIO_DIR.mkdir(exist_ok=True)

# Timeouts
GENERATE_TIMEOUT = 15.0   # seconds — TTS generation can be slow
HEALTH_TIMEOUT = 3.0      # seconds — quick health check
MAX_RETRIES = 2


# ── Core Functions ───────────────────────────────────────────────────────

async def generate_voice(text: str, speed: str = "normal") -> Optional[str]:
    """
    Generate speech audio from text via Voicebox API.
    
    Args:
        text: The text to convert to speech
        speed: Pacing hint — "slow", "normal", "fast"
    
    Returns:
        Relative URL path to the generated audio file (e.g., "/audio/abc123.wav")
        Returns None if generation fails (text response is still available)
    """
    if not text or not text.strip():
        return None
    
    # Clean text for TTS — remove emojis and markdown artifacts
    clean_text = _clean_for_tts(text)
    if not clean_text:
        return None
    
    # Generate unique filename
    audio_id = str(uuid.uuid4())[:12]
    audio_filename = f"{audio_id}.wav"
    audio_path = AUDIO_DIR / audio_filename
    
    # Voicebox request payload
    payload = {
        "text": clean_text,
        "profile_id": VOICEBOX_PROFILE_ID,
        "engine": VOICEBOX_ENGINE,
    }
    
    # Add speed modifier if supported
    if speed == "slow":
        payload["speed"] = 0.85
    elif speed == "fast":
        payload["speed"] = 1.15
    
    # Attempt generation with retries
    for attempt in range(MAX_RETRIES + 1):
        try:
            async with httpx.AsyncClient(timeout=GENERATE_TIMEOUT) as client:
                response = await client.post(VOICEBOX_URL, json=payload)
                
                if response.status_code == 200:
                    data = response.json()
                    generation_id = data.get("id")
                    if not generation_id:
                        print("[Voicebox] Generation succeeded but no ID returned in response")
                        return None
                        
                    # Poll generation status until completed
                    print(f"[Voicebox] Initiated generation: {generation_id}. Polling status...")
                    poll_start = asyncio.get_event_loop().time()
                    poll_timeout = 10.0  # max 10 seconds to generate audio
                    completed = False
                    
                    while asyncio.get_event_loop().time() - poll_start < poll_timeout:
                        status_url = f"http://127.0.0.1:17493/history/{generation_id}"
                        status_resp = await client.get(status_url)
                        if status_resp.status_code == 200:
                            status_data = status_resp.json()
                            status = status_data.get("status")
                            if status == "completed":
                                completed = True
                                break
                            elif status == "failed":
                                print(f"[Voicebox] Generation job failed: {status_data.get('error')}")
                                break
                        await asyncio.sleep(0.15)
                        
                    if completed:
                        audio_url = f"http://127.0.0.1:17493/audio/{generation_id}"
                        audio_resp = await client.get(audio_url)
                        if audio_resp.status_code == 200:
                            audio_bytes = audio_resp.content
                            if audio_bytes and len(audio_bytes) > 100:  # Sanity check
                                audio_path.write_bytes(audio_bytes)
                                print(f"[Voicebox] Generated audio: {audio_filename} ({len(audio_bytes)} bytes)")
                                return f"/audio/{audio_filename}"
                            else:
                                print(f"[Voicebox] Empty or too-small audio response ({len(audio_bytes)} bytes)")
                        else:
                            print(f"[Voicebox] Failed to download audio, status: {audio_resp.status_code}")
                    else:
                        print(f"[Voicebox] Generation timed out or failed to complete after {poll_timeout} seconds")
                        return None
                else:
                    print(f"[Voicebox] HTTP {response.status_code} on attempt {attempt + 1}")
                    if attempt < MAX_RETRIES:
                        await asyncio.sleep(0.5 * (attempt + 1))
                        
        except httpx.TimeoutException:
            print(f"[Voicebox] Timeout on attempt {attempt + 1}/{MAX_RETRIES + 1}")
            if attempt < MAX_RETRIES:
                await asyncio.sleep(0.5)
        except httpx.ConnectError:
            print(f"[Voicebox] Connection refused — Voicebox server may not be running")
            return None  # Don't retry connection errors
        except Exception as e:
            print(f"[Voicebox] Unexpected error: {e}")
            return None
    
    print("[Voicebox] All retry attempts exhausted — returning text-only response")
    return None


async def generate_voice_background(text: str, speed: str = "normal") -> asyncio.Task:
    """
    Fire-and-forget voice generation. Returns an asyncio Task that can be
    awaited later or ignored. This allows the text response to be sent
    immediately while audio generates in parallel.
    """
    return asyncio.create_task(generate_voice(text, speed))


async def health_check() -> dict:
    """
    Check if Voicebox server is reachable and responsive.
    
    Returns:
        {"status": "healthy", "latency_ms": 42} or
        {"status": "unavailable", "error": "..."}
    """
    try:
        async with httpx.AsyncClient(timeout=HEALTH_TIMEOUT) as client:
            # Try a minimal generation to verify the service works
            response = await client.get("http://127.0.0.1:17493/health")
            if response.status_code == 200:
                return {"status": "healthy"}
    except httpx.ConnectError:
        return {"status": "unavailable", "error": "Connection refused — server not running"}
    except httpx.TimeoutException:
        return {"status": "unavailable", "error": "Health check timed out"}
    except Exception as e:
        return {"status": "unavailable", "error": str(e)}
    
    return {"status": "unavailable", "error": "Unknown error"}


def get_latest_audio(count: int = 5) -> list[str]:
    """
    Get the most recent audio file URLs for debugging/playback.
    """
    files = sorted(AUDIO_DIR.glob("*.wav"), key=os.path.getmtime, reverse=True)
    return [f"/audio/{f.name}" for f in files[:count]]


def cleanup_old_audio(max_age_hours: int = 24):
    """
    Remove audio files older than max_age_hours to prevent disk bloat.
    Should be called periodically (e.g., on app startup or via background task).
    """
    import time
    cutoff = time.time() - (max_age_hours * 3600)
    removed = 0
    for f in AUDIO_DIR.glob("*.wav"):
        if f.stat().st_mtime < cutoff:
            f.unlink()
            removed += 1
    if removed:
        print(f"[Voicebox] Cleaned up {removed} old audio files")


# ── Text Cleaning for TTS ───────────────────────────────────────────────

def _clean_for_tts(text: str) -> str:
    """
    Remove elements that don't translate well to speech:
    - Emojis
    - Markdown formatting
    - Special characters
    """
    import re
    
    # Remove emoji characters
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs  
        "\U0001F680-\U0001F6FF"  # transport & map
        "\U0001F1E0-\U0001F1FF"  # flags
        "\U00002702-\U000027B0"  # dingbats
        "\U0001f926-\U0001f937"  # supplemental
        "\U0001F900-\U0001F9FF"  # supplemental symbols
        "\u200d"                  # zero width joiner
        "\u2640-\u2642"          # gender symbols
        "\ufe0f"                 # variation selectors
        "]+", flags=re.UNICODE
    )
    text = emoji_pattern.sub("", text)
    
    # Remove markdown bold/italic markers
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    text = re.sub(r'__(.+?)__', r'\1', text)
    
    # Remove markdown headers
    text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)
    
    # Clean up extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text
