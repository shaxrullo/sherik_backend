import os
import telebot
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Telegram Bot uchun Render Webhookni o'rnatish"

    def handle(self, *args, **options):
        token = os.environ.get("TELEGRAM_BOT_TOKEN", "9272714946:AAGViuu8BOATFYuMXHAgFn8fjsiMABRC2g0")
        webhook_url = "https://sherik-backend.onrender.com/api/v1/telegram-webhook/"
        
        self.stdout.write(f"Webhook o'rnatilmoqda: {webhook_url}")
        try:
            bot = telebot.TeleBot(token)
            bot.remove_webhook()
            result = bot.set_webhook(url=webhook_url, drop_pending_updates=True)
            if result:
                self.stdout.write(self.style.SUCCESS(f"✅ Webhook muvaffaqiyatli o'rnatildi: {webhook_url}"))
            else:
                self.stdout.write(self.style.ERROR("❌ Webhook o'rnatishda xatolik yuz berdi."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Xatolik: {e}"))
