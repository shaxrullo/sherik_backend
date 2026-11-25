import os
import telebot
from django.core.management.base import BaseCommand
from telegram_bot.config import get_bot_token


class Command(BaseCommand):
    help = "Telegram Bot uchun Render Webhookni o'rnatish"

    def handle(self, *args, **options):
        token = get_bot_token()
        secret_token = os.environ.get("TELEGRAM_WEBHOOK_SECRET", "sherik_secure_bot_token_2026_webhook")
        webhook_url = "https://sherik-backend.onrender.com/api/v1/telegram-webhook/"

        if not token:
            self.stdout.write(self.style.ERROR("❌ TELEGRAM_BOT_TOKEN muhit o'zgaruvchisi topilmadi!"))
            return
        
        self.stdout.write(f"Webhook o'rnatilmoqda: {webhook_url}")
        try:
            bot = telebot.TeleBot(token)
            bot.remove_webhook()
            kwargs = {
                "url": webhook_url,
                "drop_pending_updates": True,
            }
            if secret_token:
                kwargs["secret_token"] = secret_token
            result = bot.set_webhook(**kwargs)
            if result:
                self.stdout.write(self.style.SUCCESS(f"✅ Webhook muvaffaqiyatli o'rnatildi: {webhook_url}"))
            else:
                self.stdout.write(self.style.ERROR("❌ Webhook o'rnatishda xatolik yuz berdi."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Xatolik: {e}"))
