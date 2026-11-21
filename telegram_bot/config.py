"""
Sherik Topish — Telegram Bot
@SheriktopishBot
"""
import os

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")

# Frontend Mini App URL (Render da joylashtirilgandan keyin to'ldiriladi)
MINI_APP_URL = os.environ.get("MINI_APP_URL", "https://sherik-frontend.onrender.com")

# Backend API URL
API_BASE_URL = os.environ.get("API_BASE_URL", "https://sherik-backend.onrender.com/api/v1")

# Admin Telegram ID (bildirishnomalar uchun)
ADMIN_TELEGRAM_ID = os.environ.get("ADMIN_TELEGRAM_ID", None)

