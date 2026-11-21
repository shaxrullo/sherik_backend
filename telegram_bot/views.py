import json
import logging
import telebot
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from telegram_bot.bot import bot

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class TelegramWebhookView(View):
    """
    Render serverida Telegram Bot Webhook so'rovlarini qabul qilish.
    Telegram to'g'ridan-to'g'ri ushbu endpointga xabar va tugma bosilishlarini yuboradi.
    """
    def post(self, request, *args, **kwargs):
        try:
            body = request.body.decode('utf-8')
            if not body:
                return HttpResponse(status=200)
            update = telebot.types.Update.de_json(body)
            if update:
                bot.process_new_updates([update])
        except Exception as e:
            logger.error(f"Telegram webhook xatosi: {e}")
        return HttpResponse(status=200)

    def get(self, request, *args, **kwargs):
        return JsonResponse({
            "status": "active",
            "bot": "@SheriktopishBot",
            "message": "Telegram webhook jonli ishlamoqda"
        })
