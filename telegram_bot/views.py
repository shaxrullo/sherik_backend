import json
import logging
import threading
import time
import requests
import telebot
import os
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from telegram_bot.bot import bot

logger = logging.getLogger(__name__)

# Webhook xavfsizlik maxfiy kaliti
TELEGRAM_WEBHOOK_SECRET = os.environ.get("TELEGRAM_WEBHOOK_SECRET", "sherik_secure_bot_token_2026_webhook")

# Render bepul serverini doimo uyg'oq tutish (har 4 daqiqada ping)
_keep_alive_started = False

def _start_keep_alive():
    global _keep_alive_started
    if _keep_alive_started:
        return
    _keep_alive_started = True

    def _loop():
        time.sleep(10)
        urls = [
            "https://sherik-frontend.onrender.com",
            "https://sherik-backend.onrender.com/api/v1/listings/",
        ]
        while True:
            for url in urls:
                try:
                    requests.get(url, timeout=15)
                except Exception:
                    pass
            time.sleep(240)  # Har 4 daqiqada ping

    t = threading.Thread(target=_loop, daemon=True)
    t.start()

_start_keep_alive()


@method_decorator(csrf_exempt, name='dispatch')
class TelegramWebhookView(View):
    """
    Render serverida Telegram Bot Webhook so'rovlarini qabul qilish.
    Telegram to'g'ridan-to'g'ri ushbu endpointga xabar va tugma bosilishlarini yuboradi.
    """
    def post(self, request, *args, **kwargs):
        # Webhook Secret Token tekshiruvi (Telegram yuborgan X-Telegram-Bot-Api-Secret-Token)
        if TELEGRAM_WEBHOOK_SECRET:
            token_header = request.headers.get('X-Telegram-Bot-Api-Secret-Token', '')
            if token_header and token_header != TELEGRAM_WEBHOOK_SECRET:
                logger.warning("Ruxsat berilmagan webhook so'rovi (secret token mos kelmadi)!")
                return HttpResponse("Forbidden", status=403)

        try:
            body = request.body.decode('utf-8')
            if not body:
                return HttpResponse(status=200)
            update = telebot.types.Update.de_json(body)
            if update:
                # Agar buyruq kelsa (/start, /restart, /new), eski qadamlarni tozalash
                if update.message:
                    chat_id = update.message.chat.id
                    if update.message.text and update.message.text.startswith('/'):
                        bot.clear_step_handler_by_chat_id(chat_id)
                elif update.callback_query and update.callback_query.message:
                    chat_id = update.callback_query.message.chat.id
                    # Asosiy menyu yoki bekor qilish bosilganda qadamlarni tozalash
                    if update.callback_query.data in ['cancel_action', 'btn_back_to_menu', 'btn_new_listing', 'btn_browse_listings', 'btn_my_listings', 'btn_help']:
                        bot.clear_step_handler_by_chat_id(chat_id)

                bot.threaded = False
                bot.process_new_updates([update])
        except Exception as e:
            logger.error(f"Telegram webhook xatosi: {e}")
        return HttpResponse(status=200)

    def get(self, request, *args, **kwargs):
        setup = request.GET.get('setup')
        clear_tg = request.GET.get('clear_tg')
        secret_param = request.GET.get('secret', '')

        # Sozlash yoki o'chirish faqat admin yoki secret bilan
        if (setup or clear_tg) and not (request.user.is_authenticated and request.user.is_staff):
            if secret_param != TELEGRAM_WEBHOOK_SECRET:
                return JsonResponse({"error": "Ruxsat berilmadi: maxfiy kalit (secret) talab qilinadi."}, status=403)

        if clear_tg:
            try:
                from users.models import User
                User.objects.filter(email=f"tg_{clear_tg}@sherik.uz").update(phone_number='')
            except Exception:
                pass
        info = None
        setup_result = None
        target_url = "https://sherik-backend.onrender.com/api/v1/telegram-webhook/"

        try:
            wh = bot.get_webhook_info()
            if setup or wh.url != target_url:
                bot.remove_webhook()
                kwargs_wh = {"url": target_url, "drop_pending_updates": False}
                if TELEGRAM_WEBHOOK_SECRET:
                    kwargs_wh["secret_token"] = TELEGRAM_WEBHOOK_SECRET
                setup_result = bot.set_webhook(**kwargs_wh)
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

