"""
Sherik Topish — Telegram Bot
@SheriktopishBot
"""
import os
from pathlib import Path


def get_bot_token() -> str:
    """Muhit o'zgaruvchilaridan bot tokenini tozalab o'qish."""
    if not os.environ.get("TELEGRAM_BOT_TOKEN") and not os.environ.get("BOT_TOKEN"):
        try:
            import environ
            base_dir = Path(__file__).resolve().parent.parent
            env_path = base_dir / ".env"
            if env_path.exists():
                environ.Env.read_env(str(env_path))
        except Exception:
            pass

    raw = os.environ.get("TELEGRAM_BOT_TOKEN") or os.environ.get("BOT_TOKEN") or ""
    return raw.strip().strip('"').strip("'").strip()


BOT_TOKEN = get_bot_token()

# Frontend Mini App URL (Render da joylashtirilgandan keyin to'ldiriladi)
MINI_APP_URL = os.environ.get("MINI_APP_URL", "https://sherik-frontend.onrender.com")

# Backend API URL
API_BASE_URL = os.environ.get("API_BASE_URL", "https://sherik-backend.onrender.com/api/v1")

# Admin Telegram ID (bildirishnomalar uchun)
ADMIN_TELEGRAM_ID = os.environ.get("ADMIN_TELEGRAM_ID", None)

