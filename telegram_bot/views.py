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
        setup = request.GET.get('setup')
        info = None
        setup_result = None
        target_url = "https://sherik-backend.onrender.com/api/v1/telegram-webhook/"

        try:
            wh = bot.get_webhook_info()
            if setup or wh.url != target_url:
                bot.remove_webhook()
                setup_result = bot.set_webhook(url=target_url, drop_pending_updates=False)
                wh = bot.get_webhook_info()
            info = {
                "url": wh.url,
                "has_custom_certificate": wh.has_custom_certificate,
                "pending_update_count": wh.pending_update_count,
                "last_error_date": wh.last_error_date,
                "last_error_message": wh.last_error_message,
            }
        except Exception as e:
            info = f"Error: {e}"

        return JsonResponse({
            "status": "active",
            "bot": "@SheriktopishBot",
            "setup_result": setup_result,
            "webhook_info": info
        })

