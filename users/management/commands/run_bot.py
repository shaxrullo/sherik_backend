"""
Django management command to run the Sherik Telegram Bot.
Usage: python manage.py run_bot
"""
from django.core.management.base import BaseCommand
from telegram_bot.bot import bot


class Command(BaseCommand):
    help = "Sherik Topish Telegram Botini ishga tushirish (@SheriktopishBot)"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("🤖 @SheriktopishBot muvaffaqiyatli ishga tushdi!"))
        try:
            self.stdout.write("Eski webhooklar tozalanmoqda...")
            bot.delete_webhook(drop_pending_updates=True)
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"Webhook tozalashda ogohlantirish: {e}"))
        try:
            bot.infinity_polling(skip_pending=True)
        except (KeyboardInterrupt, SystemExit):
            self.stdout.write(self.style.WARNING("Bot to'xtatildi."))

