"""
Sherik Topish — Telegram Bot
Bot: @SheriktopishBot
"""
import io
import os
import threading
import time
import requests
import telebot
from telebot import types, apihelper

apihelper.ENABLE_MIDDLEWARE = True

# Muhit o'zgaruvchilarini yuklash (agar yuklanmagan bo'lsa)
if not os.environ.get("TELEGRAM_BOT_TOKEN"):
    try:
        from pathlib import Path
        import environ
        _base_dir = Path(__file__).resolve().parent.parent
        _env_path = os.path.join(_base_dir, '.env')
        if os.path.exists(_env_path):
            environ.Env.read_env(_env_path)
    except Exception:
        pass

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
if not BOT_TOKEN or ":" not in BOT_TOKEN:
    import logging
    logging.getLogger(__name__).warning("TELEGRAM_BOT_TOKEN muhit o'zgaruvchisi topilmadi yoki yaroqsiz formatda.")
    BOT_TOKEN = "0000000000:dummy_unconfigured_token"

API_BASE_URL = os.environ.get("API_BASE_URL", "https://sherik-backend.onrender.com/api/v1")
MINI_APP_URL = os.environ.get("MINI_APP_URL", "https://sherik-frontend.onrender.com")

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# Shaharlar ro'yxati (ID lar DB ga mos)
CITIES = [
    (1, "Toshkent"), (2, "Samarqand"), (3, "Buxoro"), (4, "Andijon"),
    (5, "Namangan"), (6, "Farg'ona"), (7, "Qashqadaryo"), (8, "Surxondaryo"),
    (9, "Xorazm"), (10, "Jizzax"), (11, "Sirdaryo"), (12, "Navoiy"),
    (13, "Qoraqalpog'iston")
]

# Vaqtinchalik foydalanuvchi ma'lumotlari saqlash (state)
user_drafts = {}


def _keep_alive_loop():
    """Render bepul tarifida sayt va backend uxlab qolmasligi uchun fon rejimida har 5 daqiqada ping yuboradi."""
    time.sleep(3)
    while True:
        for url in [MINI_APP_URL, f"{API_BASE_URL}/listings/"]:
            try:
                requests.get(url, timeout=15)
            except Exception:
                pass
        time.sleep(300) # 5 daqiqa


@bot.middleware_handler(update_types=['callback_query'])
def auto_answer_callback(bot_instance, call):
    """Barcha tugma bosilishlarini darhol tasdiqlash (aylanib qolmasligi uchun)."""
    try:
        bot_instance.answer_callback_query(call.id)
    except Exception:
        pass


def get_main_menu_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_webapp = types.InlineKeyboardButton(
        text="📱 Ilova",
        web_app=types.WebAppInfo(url=MINI_APP_URL)
    )
    btn_new = types.InlineKeyboardButton(text="📋 E'lon joylash", callback_data="btn_new_listing")
    btn_browse = types.InlineKeyboardButton(text="🔍 E'lonlar", callback_data="btn_browse_listings")
    btn_my = types.InlineKeyboardButton(text="👤 Mening e'lonlarim", callback_data="btn_my_listings")
    btn_help = types.InlineKeyboardButton(text="ℹ️ Yordam", callback_data="btn_help")

    markup.add(btn_webapp)
    markup.add(btn_new, btn_browse)
    markup.add(btn_my, btn_help)
    return markup


def check_user_registration(tg_user):
    """Foydalanuvchi bazada telefon raqami bilan ro'yxatdan o'tganligini tekshiradi."""
    try:
        auth_data = {
            "telegram_id": tg_user.id,
            "first_name": tg_user.first_name or "",
            "last_name": tg_user.last_name or "",
            "username": tg_user.username or ""
        }
        resp = requests.post(f"{API_BASE_URL}/auth/telegram/", json=auth_data, timeout=10)
        if resp.status_code == 200:
            user_info = resp.json().get("user", {})
            return user_info.get("phone_number")
    except Exception:
        pass
    return None


@bot.message_handler(commands=['start', 'menu'])
def handle_start(message: types.Message):
    bot.clear_step_handler_by_chat_id(message.chat.id)
    try:
        bot.set_chat_menu_button(
            chat_id=message.chat.id,
            menu_button=types.MenuButtonWebApp(
                type="web_app",
                text="📱 Ilova",
                web_app=types.WebAppInfo(url=MINI_APP_URL)
            )
        )
    except Exception:
        pass

    user_name = message.from_user.first_name or "Foydalanuvchi"
    phone = check_user_registration(message.from_user)

    if not phone:
        # Yangi foydalanuvchi: Ro'yxatdan o'tishni so'raymiz
        reg_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        reg_markup.add(types.KeyboardButton("📱 Telefon raqamimni yuborish", request_contact=True))
        reg_markup.add(types.KeyboardButton("⏭️ Keyinroq kiritish"))

        text = (
            f"Assalomu alaykum, <b>{user_name}</b>! 👋\n\n"
            f"<b>Sherik Topish</b> rasmiy botiga xush kelibsiz!\n\n"
            f"Xizmatdan to'liq foydalanish, e'lonlar joylashtirish va Ilovadan foydalanish uchun, iltimos, <b>ro'yxatdan o'ting</b>.\n\n"
            f"Buning uchun pastdagi <b>«📱 Telefon raqamimni yuborish»</b> tugmasini bosing:"
        )
        msg = bot.send_message(message.chat.id, text, reply_markup=reg_markup)
        bot.register_next_step_handler(msg, process_start_registration)
        return

    # Ro'yxatdan o'tgan foydalanuvchi uchun asosiy menyu
    text = (
        f"Assalomu alaykum, <b>{user_name}</b>! 👋\n\n"
        f"<b>Sherik Topish</b> rasmiy botiga xush kelibsiz.\n"
        f"Hisobingiz: 📱 <b>{phone}</b>\n\n"
        f"Pastdagi tugmalar orqali kerakli bo'limni tanlang:"
    )
    bot.send_message(
        chat_id=message.chat.id,
        text=text,
        reply_markup=get_main_menu_keyboard()
    )


@bot.message_handler(commands=['restart', 'register'])
def handle_restart_registration(message: types.Message):
    bot.clear_step_handler_by_chat_id(message.chat.id)
    try:
        requests.post(
            f"{API_BASE_URL}/auth/telegram/",
            json={"telegram_id": message.from_user.id, "reset_phone": True},
            timeout=10
        )
    except Exception:
        pass

    user_name = message.from_user.first_name or "Foydalanuvchi"
    reg_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    reg_markup.add(types.KeyboardButton("📱 Telefon raqamimni yuborish", request_contact=True))
    reg_markup.add(types.KeyboardButton("⏭️ Keyinroq kiritish"))

    text = (
        f"Assalomu alaykum, <b>{user_name}</b>! 👋\n\n"
        f"<b>Sherik Topish</b> botida ro'yxatdan o'tish:\n\n"
        f"Iltimos, pastdagi <b>«📱 Telefon raqamimni yuborish»</b> tugmasini bosing:"
    )
    msg = bot.send_message(message.chat.id, text, reply_markup=reg_markup)
    bot.register_next_step_handler(msg, process_start_registration)


def process_start_registration(message: types.Message):
    user_name = message.from_user.first_name or "Foydalanuvchi"
    phone = None

    if message.contact:
        phone = message.contact.phone_number
        if not phone.startswith("+"):
            phone = "+" + phone
    elif message.text:
        text = message.text.strip()
        if text in ["⏭️ Keyinroq kiritish", "/skip"]:
            bot.send_message(
                message.chat.id,
                "Tushunarli. Asosiy menyu:",
                reply_markup=types.ReplyKeyboardRemove()
            )
            bot.send_message(
                message.chat.id,
                "Pastdagi tugmalar orqali kerakli bo'limni tanlang:",
                reply_markup=get_main_menu_keyboard()
            )
            return
        # Raqam tekshiruvi
        raw = "".join(c for c in text if c.isdigit() or c == "+")
        if len(raw) >= 9:
            phone = raw if raw.startswith("+") else "+" + raw

    if not phone:
        reg_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        reg_markup.add(types.KeyboardButton("📱 Telefon raqamimni yuborish", request_contact=True))
        reg_markup.add(types.KeyboardButton("⏭️ Keyinroq kiritish"))
        msg = bot.send_message(
            message.chat.id,
            "❌ Iltimos, ro'yxatdan o'tish uchun pastdagi <b>«📱 Telefon raqamimni yuborish»</b> tugmasini bosing yoki raqamingizni to'liq yozing (+998901234567):",
            reply_markup=reg_markup
        )
        bot.register_next_step_handler(msg, process_start_registration)
        return

    # Backend ga telefon raqam bilan ro'yxatdan o'tkazish
    try:
        auth_data = {
            "telegram_id": message.from_user.id,
            "first_name": message.from_user.first_name or "",
            "last_name": message.from_user.last_name or "",
            "username": message.from_user.username or "",
            "phone_number": phone
        }
        requests.post(f"{API_BASE_URL}/auth/telegram/", json=auth_data, timeout=10)
    except Exception:
        pass

    bot.send_message(
        message.chat.id,
        f"✅ <b>Tabriklaymiz, {user_name}!</b>\n"
        f"Telefon raqamingiz tasdiqlandi va siz muvaffaqiyatli ro'yxatdan o'tdingiz! 🎉\n\n"
        f"Endi bemalol e'lonlar joylashtirishingiz va Ilovadan foydalanishingiz mumkin.",
        reply_markup=types.ReplyKeyboardRemove()
    )
    bot.send_message(
        message.chat.id,
        "Pastdagi tugmalar orqali kerakli bo'limni tanlang:",
        reply_markup=get_main_menu_keyboard()
    )


@bot.message_handler(commands=['help'])
def handle_help(message: types.Message):
    text = (
        "ℹ️ <b>Sherik Bot bo'yicha ko'rsatmalar:</b>\n\n"
        "• <b>📱 Ilova</b> — Ilovani to'g'ridan-to'g'ri Telegram ichida ochadi.\n"
        "• <b>📋 E'lon joylash</b> — Bot orqali tezda e'lon joylashtirish.\n"
        "• <b>🔍 E'lonlar</b> — Barcha tasdiqlangan e'lonlarni ko'rish.\n\n"
        "Buyruqlar:\n"
        "/start — Bosh menyu\n"
        "/new — Yangi e'lon berish\n"
        "/listings — E'lonlarni ko'rish\n"
        "/help — Yordam"
    )
    bot.send_message(message.chat.id, text, reply_markup=get_main_menu_keyboard())


def format_price_display(price, currency="USD"):
    """Narx va valyutani chiroyli formatlash."""
    try:
        val = float(price)
        if currency == "USD":
            return f"${int(val) if val.is_integer() else val}"
        else:
            return f"{int(val):,} so'm".replace(",", " ")
    except Exception:
        return f"{price} {currency}"


DEFAULT_AMENITIES = [
    "Wi-Fi", "Konditsioner", "Kir yuvish m.", "Muzlatgich",
    "Televizor", "Gaz plitasi", "Oshxona mebeli", "Krovat / Divan",
    "Issiq suv / Dush", "Isitish tizimi", "Changyutgich", "Balkon"
]

METRO_STATIONS = [
    "Chilonzor", "Novza", "Mirzo Ulug'bek", "Paxtakor",
    "Buyuk Ipak Yo'li", "Oybek", "Beruniy", "Yunusobod",
    "Shahriston", "Bodomzor", "Amir Temur", "Do'stlik"
]

CITY_UNIVERSITIES = {
    1: [  # Toshkent
        "TATU", "O'zMU", "TDTU (Politex)", "TDPU (Nizomiy)",
        "TDIU (Narxoz)", "O'zDJTU (Jahon tillari)", "TMA (Med)", "Inha",
        "Vestminster (WIUT)", "Turin", "O'zJOKU", "Singapur (MDIST)"
    ],
    2: [  # Samarqand
        "SamDU", "SamDTI (Med)", "SamISI (Iqtisod)", "SamDAQI",
        "SamCHTI (Chet tillari)", "Ipak Yo'li Turizm Univ", "TATU Samarqand f."
    ],
    3: [  # Buxoro
        "BuxDU", "BuxMTI", "BuxDTI (Med)", "BuxITMU", "Buxoro Davlat Pedagogika"
    ],
    4: [  # Andijon
        "ADU", "ADTI (Tibbiyot)", "AndMI (Mashinasozlik)", "AndQXAI"
    ],
    5: [  # Namangan
        "NamDU", "NamMQI", "NamMTI", "Namangan Chet Tillari"
    ],
    6: [  # Farg'ona
        "FarDU", "FarPI", "TATU Farg'ona f.", "Qo'qon DPI", "TMA Farg'ona f."
    ],
    7: [  # Qashqadaryo
        "QarDU", "QarMII (Muhandislik)", "TATU Qarshi f.", "Qarshi Pedagogika"
    ],
    8: [  # Surxondaryo
        "TerDU", "TerDPI", "TerMI (Muhandislik)", "Termiz Agrotex"
    ],
    9: [  # Xorazm
        "UrDU", "TATU Urganch f.", "TMA Urganch f."
    ],
    10: [  # Jizzax
        "JizDPU", "JizPI (Politex)", "O'zMU Jizzax f.", "Sambhram Univ"
    ],
    11: [  # Sirdaryo
        "GulDU (Guliston davlat)", "GulDPI", "Toshkent Kimyo Guliston f."
    ],
    12: [  # Navoiy
        "NavDKTU (Konchilik)", "NavDPI"
    ],
    13: [  # Qoraqalpog'iston
        "QDU (Berdaq)", "NMPI (Ajdiniyaz)", "Qoraqalpoq QXAI", "TATU Nukus f.", "TMA Nukus f."
    ]
}

POPULAR_UNIVERSITIES = CITY_UNIVERSITIES[1]


# ==================== E'LONLARNI KO'RISH ====================

@bot.callback_query_handler(func=lambda call: call.data == "btn_browse_listings")
@bot.message_handler(commands=['listings'])
def handle_browse_listings(update):
    chat_id = update.message.chat.id if isinstance(update, types.CallbackQuery) else update.chat.id

    wait_msg = bot.send_message(chat_id, "🔍 E'lonlar yuklanmoqda...")
    try:
        resp = requests.get(f"{API_BASE_URL}/listings/", timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            results = data.get("results", [])
            total = data.get("count", 0)

            if not results:
                bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=wait_msg.message_id,
                    text="📭 Hozircha e'lonlar mavjud emas.\nBirinchi bo'lib e'lon joylang!",
                    reply_markup=get_main_menu_keyboard()
                )
                return

            bot.delete_message(chat_id, wait_msg.message_id)

            bot.send_message(chat_id, f"📋 <b>Jami {total} ta e'lon mavjud. Eng so'nggilari:</b>")

            for item in results[:5]:
                type_icon = "🏠 Xonam bor" if item.get("listing_type") == "have_room" else "🔍 Xona kerak"
                gender_map = {"male": "👨 Faqat erkaklar", "female": "👩 Faqat ayollar", "any": "🤝 Farqi yo'q"}
                gender_str = gender_map.get(item.get("gender_preference"), "Farqi yo'q")
                city = item.get("city_name") or "O'zbekiston"

                price_str = format_price_display(item.get("price", 0), item.get("currency", "USD"))
                metro_str = f"\n🚇 <b>Metro:</b> {item.get('near_subway')}" if item.get('near_subway') else ""
                unis_list = item.get("nearby_universities", [])
                unis_str = f"\n🎓 <b>OTM:</b> {', '.join(unis_list[:3])}" if unis_list else ""
                amenities_list = item.get("amenities", [])
                amenities_text = f"\n🛋 <b>Jihozlar:</b> {', '.join(amenities_list[:4])}" if amenities_list else ""

                card = (
                    f"<b>{item.get('title')}</b>\n\n"
                    f"📌 <b>Turi:</b> {type_icon}\n"
                    f"📍 <b>Shahar:</b> {city}\n"
                    f"💰 <b>Narxi:</b> {price_str}\n"
                    f"👥 <b>Kimga:</b> {gender_str}{metro_str}{unis_str}{amenities_text}\n\n"
                    f"<i>ID: #{item.get('id')}</i>"
                )

                item_markup = types.InlineKeyboardMarkup()
                item_markup.add(types.InlineKeyboardButton(
                    text="📱 Ilovada ko'rish",
                    web_app=types.WebAppInfo(url=f"{MINI_APP_URL}/listings/{item.get('id')}")
                ))

                main_photo = item.get("main_photo")
                if main_photo:
                    try:
                        bot.send_photo(chat_id, photo=main_photo, caption=card, reply_markup=item_markup)
                    except Exception:
                        bot.send_message(chat_id, card, reply_markup=item_markup)
                else:
                    bot.send_message(chat_id, card, reply_markup=item_markup)

            # Tugatish tugmasi
            bot.send_message(chat_id, "Ko'proq e'lonlarni ilovada ko'rishingiz mumkin:", reply_markup=get_main_menu_keyboard())

        else:
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=wait_msg.message_id,
                text="❌ E'lonlarni yuklashda xatolik yuz berdi. Qaytadan urinib ko'ring.",
                reply_markup=get_main_menu_keyboard()
            )
    except Exception as e:
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=wait_msg.message_id,
            text=f"❌ Xatolik: {e}",
            reply_markup=get_main_menu_keyboard()
        )


# ==================== E'LON JOYLASH (WIZARD) ====================

def init_user_draft(user):
    user_id = user.id
    user_drafts[user_id] = {
        "telegram_id": user_id,
        "first_name": user.first_name or "",
        "last_name": user.last_name or "",
        "username": user.username or "",
        "capacity": 1,
        "total_residents": 2,
        "amenities": [],
        "currency": "USD",
        "selected_metros": [],
        "near_subway": "",
        "nearby_universities": [],
        "photo_file_ids": [],
    }
    return user_drafts[user_id]


@bot.callback_query_handler(func=lambda call: call.data == "btn_new_listing")
@bot.message_handler(commands=['new'])
def start_new_listing(update):
    user = update.from_user
    chat_id = update.message.chat.id if isinstance(update, types.CallbackQuery) else update.chat.id
    init_user_draft(user)
    bot.clear_step_handler_by_chat_id(chat_id)
    render_step_1_type(chat_id, message_id=update.message.message_id if isinstance(update, types.CallbackQuery) else None)


def render_step_1_type(chat_id, message_id=None):
    bot.clear_step_handler_by_chat_id(chat_id)
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🏠 Xonam bor (Sherik kerak)", callback_data="wiz_type_have_room"),
        types.InlineKeyboardButton("🔍 Xona kerak (Ijara qidiryapman)", callback_data="wiz_type_need_room"),
        types.InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel_action")
    )
    text = "📋 <b>E'lon joylash — 1-bosqich:</b>\n\nQanday e'lon bermoqchisiz?"
    if message_id:
        try:
            bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=text, reply_markup=markup)
            return
        except Exception:
            pass
    bot.send_message(chat_id=chat_id, text=text, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data in ["wiz_type_have_room", "wiz_type_need_room"])
def handle_listing_type(call: types.CallbackQuery):
    user_id = call.from_user.id
    if user_id not in user_drafts:
        init_user_draft(call.from_user)

    listing_type = "have_room" if call.data == "wiz_type_have_room" else "need_room"
    user_drafts[user_id]["listing_type"] = listing_type
    render_step_2_city(call.message.chat.id, message_id=call.message.message_id)


def render_step_2_city(chat_id, message_id=None):
    bot.clear_step_handler_by_chat_id(chat_id)
    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = [types.InlineKeyboardButton(name, callback_data=f"wiz_city_{cid}") for cid, name in CITIES]
    markup.add(*buttons)
    markup.add(
        types.InlineKeyboardButton("⬅️ Orqaga", callback_data="wiz_back_to_type"),
        types.InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel_action")
    )

    text = "📍 <b>2-bosqich:</b> Shaharni tanlang:"
    if message_id:
        try:
            bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=text, reply_markup=markup)
            return
        except Exception:
            pass
    bot.send_message(chat_id=chat_id, text=text, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == "wiz_back_to_type")
def handle_back_to_type(call: types.CallbackQuery):
    render_step_1_type(call.message.chat.id, message_id=call.message.message_id)


@bot.callback_query_handler(func=lambda call: call.data.startswith("wiz_city_"))
def handle_city_selection(call: types.CallbackQuery):
    user_id = call.from_user.id
    if user_id not in user_drafts:
        init_user_draft(call.from_user)

    city_id = int(call.data.replace("wiz_city_", ""))
    city_name = dict(CITIES).get(city_id, "Toshkent")

    user_drafts[user_id]["city_id"] = city_id
    user_drafts[user_id]["city_name"] = city_name

    render_step_3_title(call.message.chat.id, city_name=city_name)


def render_step_3_title(chat_id, city_name=None):
    bot.clear_step_handler_by_chat_id(chat_id)
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("⬅️ Orqaga", callback_data="wiz_back_to_city"),
        types.InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel_action")
    )

    city_hint = f"✅ Shahar: <b>{city_name}</b>\n\n" if city_name else ""
    msg = bot.send_message(
        chat_id,
        f"{city_hint}✏️ <b>3-bosqich:</b> E'lon sarlavhasini yozing:\n"
        f"<i>(Masalan: Chilonzorda 2 xonali kvartiraga 1 nafar sherik kerak)</i>",
        reply_markup=markup
    )
    bot.register_next_step_handler(msg, process_title_step)


@bot.callback_query_handler(func=lambda call: call.data == "wiz_back_to_city")
def handle_back_to_city(call: types.CallbackQuery):
    bot.clear_step_handler_by_chat_id(call.message.chat.id)
    render_step_2_city(call.message.chat.id, message_id=call.message.message_id)


def process_title_step(message: types.Message):
    user_id = message.from_user.id
    if user_id not in user_drafts:
        bot.send_message(message.chat.id, "Boshidan boshlang: /new", reply_markup=get_main_menu_keyboard())
        return

    text = (message.text or "").strip()
    if text in ["⬅️ Orqaga", "/back"]:
        render_step_2_city(message.chat.id)
        return
    if text in ["❌ Bekor qilish", "/cancel"]:
        handle_cancel_msg(message)
        return

    if len(text) < 5:
        msg = bot.send_message(message.chat.id, "❌ Sarlavha juda qisqa. Kamida 5 ta belgi yozing:")
        bot.register_next_step_handler(msg, process_title_step)
        return

    user_drafts[user_id]["title"] = text
    render_step_4_description(message.chat.id)


def render_step_4_description(chat_id):
    bot.clear_step_handler_by_chat_id(chat_id)
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("⬅️ Orqaga", callback_data="wiz_back_to_title"),
        types.InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel_action")
    )

    msg = bot.send_message(
        chat_id,
        "📝 <b>4-bosqich:</b> E'lon tavsifini yozing:\n"
        "<i>(Qavat, sharoitlar, yaqin metro/mo'ljal, kimlar yashaydi va h.k.)</i>",
        reply_markup=markup
    )
    bot.register_next_step_handler(msg, process_description_step)


@bot.callback_query_handler(func=lambda call: call.data == "wiz_back_to_title")
def handle_back_to_title(call: types.CallbackQuery):
    bot.clear_step_handler_by_chat_id(call.message.chat.id)
    render_step_3_title(call.message.chat.id)


def process_description_step(message: types.Message):
    user_id = message.from_user.id
    if user_id not in user_drafts:
        bot.send_message(message.chat.id, "Boshidan boshlang: /new", reply_markup=get_main_menu_keyboard())
        return

    text = (message.text or "").strip()
    if text in ["⬅️ Orqaga", "/back"]:
        render_step_3_title(message.chat.id)
        return
    if text in ["❌ Bekor qilish", "/cancel"]:
        handle_cancel_msg(message)
        return

    if len(text) < 10:
        msg = bot.send_message(message.chat.id, "❌ Tavsif juda qisqa. Kamida 10 ta belgi yozing:")
        bot.register_next_step_handler(msg, process_description_step)
        return

    user_drafts[user_id]["description"] = text
    render_step_5_currency(message.chat.id)


def render_step_5_currency(chat_id, message_id=None):
    bot.clear_step_handler_by_chat_id(chat_id)
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("💵 Dollar ($)", callback_data="wiz_curr_USD"),
        types.InlineKeyboardButton("🇺🇿 So'm (UZS)", callback_data="wiz_curr_UZS")
    )
    markup.add(
        types.InlineKeyboardButton("⬅️ Orqaga", callback_data="wiz_back_to_desc"),
        types.InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel_action")
    )

    text = (
        "💰 <b>5-bosqich:</b> Valyutani tanlang:\n\n"
        "Oylik to'lov narxini qaysi valyutada kiritmoqchisiz?"
    )
    if message_id:
        try:
            bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=text, reply_markup=markup)
            return
        except Exception:
            pass
    bot.send_message(chat_id=chat_id, text=text, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == "wiz_back_to_desc")
def handle_back_to_desc(call: types.CallbackQuery):
    bot.clear_step_handler_by_chat_id(call.message.chat.id)
    render_step_4_description(call.message.chat.id)


@bot.callback_query_handler(func=lambda call: call.data in ["wiz_curr_USD", "wiz_curr_UZS"])
def handle_currency_selection(call: types.CallbackQuery):
    user_id = call.from_user.id
    if user_id not in user_drafts:
        init_user_draft(call.from_user)

    currency = "USD" if call.data == "wiz_curr_USD" else "UZS"
    user_drafts[user_id]["currency"] = currency
    render_step_5b_price(call.message.chat.id, currency)


def render_step_5b_price(chat_id, currency="USD"):
    bot.clear_step_handler_by_chat_id(chat_id)
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("⬅️ Valyutani o'zgartirish", callback_data="wiz_back_to_curr"),
        types.InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel_action")
    )

    if currency == "USD":
        prompt_text = (
            "💵 <b>Narxni kiriting (AQSH dollarida):</b>\n"
            "<i>(Masalan: 50 yoki 150)</i>"
        )
    else:
        prompt_text = (
            "🇺🇿 <b>Narxni kiriting (O'zbek so'mida):</b>\n"
            "<i>(Masalan: 1 500 000 yoki 2000000)</i>"
        )

    msg = bot.send_message(chat_id, prompt_text, reply_markup=markup)
    bot.register_next_step_handler(msg, process_price_step)


@bot.callback_query_handler(func=lambda call: call.data == "wiz_back_to_curr")
def handle_back_to_curr(call: types.CallbackQuery):
    bot.clear_step_handler_by_chat_id(call.message.chat.id)
    render_step_5_currency(call.message.chat.id, message_id=call.message.message_id)


def process_price_step(message: types.Message):
    user_id = message.from_user.id
    if user_id not in user_drafts:
        bot.send_message(message.chat.id, "Boshidan boshlang: /new", reply_markup=get_main_menu_keyboard())
        return

    text = (message.text or "").strip()
    if text in ["⬅️ Orqaga", "/back"]:
        render_step_5_currency(message.chat.id)
        return
    if text in ["❌ Bekor qilish", "/cancel"]:
        handle_cancel_msg(message)
        return

    # Tozalash
    cleaned = text.replace("$", "").replace(" ", "").replace(",", "").replace("so'm", "").replace("som", "")
    try:
        price = int(round(float(cleaned)))
        if price <= 0:
            raise ValueError
    except ValueError:
        curr = user_drafts[user_id].get("currency", "USD")
        hint = "50 yoki 100" if curr == "USD" else "1500000"
        msg = bot.send_message(message.chat.id, f"❌ Noto'g'ri narx. Iltimos, faqat musbat son yozing (masalan: {hint}):")
        bot.register_next_step_handler(msg, process_price_step)
        return

    user_drafts[user_id]["price"] = price
    render_step_6_gender(message.chat.id, user_id=user_id)


def render_step_6_gender(chat_id, user_id=None, message_id=None):
    bot.clear_step_handler_by_chat_id(chat_id)
    uid = user_id or chat_id
    draft = user_drafts.get(uid, {})
    is_need = draft.get("listing_type") == "need_room"

    markup = types.InlineKeyboardMarkup(row_width=1)
    if is_need:
        markup.add(
            types.InlineKeyboardButton("👨 Yigit kishiman / Erkak", callback_data="wiz_gender_male"),
            types.InlineKeyboardButton("👩 Qiz bolaman / Ayol", callback_data="wiz_gender_female"),
        )
        text = "👤 <b>6-bosqich:</b> O'zingizning jinsingizni tanlang:\n\n<i>(Kvartira egalari va sheriklar sizni to'g'ri topishi uchun o'z jinsingizni ko'rsating)</i>"
    else:
        markup.add(
            types.InlineKeyboardButton("👨 Faqat erkaklar / yigitlar", callback_data="wiz_gender_male"),
            types.InlineKeyboardButton("👩 Faqat ayollar / qizlar", callback_data="wiz_gender_female"),
            types.InlineKeyboardButton("🤝 Farqi yo'q", callback_data="wiz_gender_any"),
        )
        text = "👥 <b>6-bosqich:</b> Kimlar uchun mo'ljallangan (Sherik talabi)?"

    markup.row(
        types.InlineKeyboardButton("⬅️ Orqaga", callback_data="wiz_back_to_price"),
        types.InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel_action")
    )
    if message_id:
        try:
            bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=text, reply_markup=markup)
            return
        except Exception:
            pass
    bot.send_message(chat_id=chat_id, text=text, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == "wiz_back_to_price")
def handle_back_to_price(call: types.CallbackQuery):
    bot.clear_step_handler_by_chat_id(call.message.chat.id)
    user_id = call.from_user.id
    currency = user_drafts.get(user_id, {}).get("currency", "USD")
    render_step_5b_price(call.message.chat.id, currency)


@bot.callback_query_handler(func=lambda call: call.data in ["wiz_gender_male", "wiz_gender_female", "wiz_gender_any"])
def handle_gender_step(call: types.CallbackQuery):
    user_id = call.from_user.id
    if user_id not in user_drafts:
        init_user_draft(call.from_user)

    gender_map = {"wiz_gender_male": "male", "wiz_gender_female": "female", "wiz_gender_any": "any"}
    user_drafts[user_id]["gender_preference"] = gender_map[call.data]

    render_step_6b_capacity(call.message.chat.id, user_id=user_id, message_id=call.message.message_id)


# ==================== 6B-BOSQICH: NECHTA SHERIK KERAK ====================

def render_step_6b_capacity(chat_id, user_id, message_id=None):
    bot.clear_step_handler_by_chat_id(chat_id)
    if user_id not in user_drafts:
        user_drafts[user_id] = {"capacity": 1}

    draft = user_drafts[user_id]
    is_have = draft.get("listing_type") == "have_room"

    markup = types.InlineKeyboardMarkup(row_width=3)
    markup.add(
        types.InlineKeyboardButton("1 nafar", callback_data="wiz_cap_1"),
        types.InlineKeyboardButton("2 nafar", callback_data="wiz_cap_2"),
        types.InlineKeyboardButton("3 nafar", callback_data="wiz_cap_3"),
        types.InlineKeyboardButton("4 nafar", callback_data="wiz_cap_4"),
        types.InlineKeyboardButton("5+ nafar", callback_data="wiz_cap_5"),
        types.InlineKeyboardButton("✏️ Boshqa son", callback_data="wiz_cap_custom")
    )
    markup.row(
        types.InlineKeyboardButton("⬅️ Orqaga", callback_data="wiz_back_to_gender"),
        types.InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel_action")
    )

    if is_have:
        text = "👥 <b>6B-bosqich:</b> Nechta sherik kerak?\n\n<i>Xonaga nechta kishi qabul qilmoqchisiz:</i>"
    else:
        text = "👥 <b>6B-bosqich:</b> Necha kishi bo'lib joy qidiryapsiz?\n\n<i>(O'zingiz bilan birga turadiganlar soni):</i>"

    if message_id:
        try:
            bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=text, reply_markup=markup)
            return
        except Exception:
            pass
    bot.send_message(chat_id=chat_id, text=text, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("wiz_cap_"))
def handle_capacity_choice(call: types.CallbackQuery):
    user_id = call.from_user.id
    if user_id not in user_drafts:
        init_user_draft(call.from_user)

    val_str = call.data.replace("wiz_cap_", "")
    if val_str == "custom":
        msg = bot.send_message(call.message.chat.id, "✏️ <b>Nechta sherik kerakligini raqamda yozing:</b>\n<i>(Masalan: 1, 2, 4...)</i>")
        bot.register_next_step_handler(msg, process_custom_capacity_step)
        return

    try:
        user_drafts[user_id]["capacity"] = int(val_str)
    except Exception:
        user_drafts[user_id]["capacity"] = 1

    render_step_6c_residents(call.message.chat.id, user_id=user_id, message_id=call.message.message_id)


def process_custom_capacity_step(message: types.Message):
    user_id = message.from_user.id
    if user_id not in user_drafts:
        return
    text = (message.text or "").strip()
    digits = "".join(c for c in text if c.isdigit())
    val = int(digits) if digits else 1
    user_drafts[user_id]["capacity"] = max(1, min(val, 50))
    render_step_6c_residents(message.chat.id, user_id=user_id)


# ==================== 6C-BOSQICH: JAMI NECHTA ODAM TURADI ====================

def render_step_6c_residents(chat_id, user_id, message_id=None):
    bot.clear_step_handler_by_chat_id(chat_id)
    if user_id not in user_drafts:
        user_drafts[user_id] = {"total_residents": 2}

    markup = types.InlineKeyboardMarkup(row_width=3)
    markup.add(
        types.InlineKeyboardButton("Jami 1 kishi", callback_data="wiz_tot_1"),
        types.InlineKeyboardButton("Jami 2 kishi", callback_data="wiz_tot_2"),
        types.InlineKeyboardButton("Jami 3 kishi", callback_data="wiz_tot_3"),
        types.InlineKeyboardButton("Jami 4 kishi", callback_data="wiz_tot_4"),
        types.InlineKeyboardButton("Jami 5 kishi", callback_data="wiz_tot_5"),
        types.InlineKeyboardButton("Jami 6+ kishi", callback_data="wiz_tot_6"),
        types.InlineKeyboardButton("✏️ Boshqa son", callback_data="wiz_tot_custom")
    )
    markup.row(
        types.InlineKeyboardButton("⬅️ Orqaga", callback_data="wiz_back_to_cap"),
        types.InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel_action")
    )

    text = (
        "🏠 <b>6C-bosqich:</b> Kvartirada umumiy hisobda jami nechta odam turadi?\n\n"
        "<i>(O'zingiz + sheriklar va barcha birga yashovchilar soni):</i>"
    )

    if message_id:
        try:
            bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=text, reply_markup=markup)
            return
        except Exception:
            pass
    bot.send_message(chat_id=chat_id, text=text, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("wiz_tot_"))
def handle_residents_choice(call: types.CallbackQuery):
    user_id = call.from_user.id
    if user_id not in user_drafts:
        init_user_draft(call.from_user)

    val_str = call.data.replace("wiz_tot_", "")
    if val_str == "custom":
        msg = bot.send_message(call.message.chat.id, "✏️ <b>Kvartirada jami yashaydiganlar sonini yozing:</b>\n<i>(Masalan: 3, 5, 8...)</i>")
        bot.register_next_step_handler(msg, process_custom_residents_step)
        return

    try:
        user_drafts[user_id]["total_residents"] = int(val_str)
    except Exception:
        user_drafts[user_id]["total_residents"] = 2

    render_step_7_amenities(call.message.chat.id, user_id=user_id, message_id=call.message.message_id)


def process_custom_residents_step(message: types.Message):
    user_id = message.from_user.id
    if user_id not in user_drafts:
        return
    text = (message.text or "").strip()
    digits = "".join(c for c in text if c.isdigit())
    val = int(digits) if digits else 2
    user_drafts[user_id]["total_residents"] = max(1, min(val, 100))
    render_step_7_amenities(message.chat.id, user_id=user_id)


@bot.callback_query_handler(func=lambda call: call.data == "wiz_back_to_cap")
def handle_back_to_capacity(call: types.CallbackQuery):
    bot.clear_step_handler_by_chat_id(call.message.chat.id)
    render_step_6b_capacity(call.message.chat.id, user_id=call.from_user.id, message_id=call.message.message_id)


# ==================== 7-BOSQICH: JIHOZLAR (AMENITIES) ====================

def render_step_7_amenities(chat_id, user_id, message_id=None):
    bot.clear_step_handler_by_chat_id(chat_id)
    if user_id not in user_drafts:
        user_drafts[user_id] = {"amenities": []}

    selected = user_drafts[user_id].get("amenities", [])

    markup = types.InlineKeyboardMarkup(row_width=2)
    chips = []
    for idx, name in enumerate(DEFAULT_AMENITIES):
        is_sel = name in selected
        label = f"✅ {name}" if is_sel else name
        chips.append(types.InlineKeyboardButton(label, callback_data=f"wiz_am_{idx}"))
    markup.add(*chips)

    markup.row(
        types.InlineKeyboardButton("➕ Boshqa jihoz yozish", callback_data="wiz_custom_amenity")
    )
    markup.row(
        types.InlineKeyboardButton("Davom etish ➡️", callback_data="wiz_amenities_done")
    )
    markup.row(
        types.InlineKeyboardButton("⬅️ Orqaga", callback_data="wiz_back_to_residents"),
        types.InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel_action")
    )

    sel_str = ", ".join(selected) if selected else "<i>Hozircha hech narsa tanlanmadi</i>"
    text = (
        "🛋 <b>7-bosqich:</b> Xonadonda bor jihozlar va qulayliklar:\n\n"
        "<i>Kerakli jihozlarni bosing (bir nechtasini tanlashingiz mumkin):</i>\n\n"
        f"Tanlanganlar:\n<b>{sel_str}</b>"
    )

    if message_id:
        try:
            bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=text, reply_markup=markup)
            return
        except Exception:
            pass
    bot.send_message(chat_id=chat_id, text=text, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("wiz_am_") and call.data != "wiz_amenities_done")
def handle_amenity_toggle(call: types.CallbackQuery):
    user_id = call.from_user.id
    if user_id not in user_drafts:
        init_user_draft(call.from_user)

    idx = int(call.data.replace("wiz_am_", ""))
    if 0 <= idx < len(DEFAULT_AMENITIES):
        item_name = DEFAULT_AMENITIES[idx]
        selected = user_drafts[user_id].setdefault("amenities", [])
        if item_name in selected:
            selected.remove(item_name)
        else:
            selected.append(item_name)

    render_step_7_amenities(call.message.chat.id, user_id=user_id, message_id=call.message.message_id)


@bot.callback_query_handler(func=lambda call: call.data == "wiz_custom_amenity")
def handle_custom_amenity_prompt(call: types.CallbackQuery):
    bot.clear_step_handler_by_chat_id(call.message.chat.id)
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("⬅️ Jihozlar ro'yxatiga qaytish", callback_data="wiz_back_to_amenities"))

    msg = bot.send_message(
        call.message.chat.id,
        "✏️ <b>Qo'shimcha jihoz yoki qulaylik nomini yozing:</b>\n"
        "<i>(Masalan: Mikroto'lqinli pech, Dazmol, Fen, Kofe mashinasi va h.k.)</i>",
        reply_markup=markup
    )
    bot.register_next_step_handler(msg, process_custom_amenity_step)


def process_custom_amenity_step(message: types.Message):
    user_id = message.from_user.id
    if user_id not in user_drafts:
        bot.send_message(message.chat.id, "Boshidan boshlang: /new", reply_markup=get_main_menu_keyboard())
        return

    text = (message.text or "").strip()
    if text in ["⬅️ Orqaga", "/back"]:
        render_step_7_amenities(message.chat.id, user_id=user_id)
        return
    if text in ["❌ Bekor qilish", "/cancel"]:
        handle_cancel_msg(message)
        return

    if len(text) >= 2:
        selected = user_drafts[user_id].setdefault("amenities", [])
        if text not in selected:
            selected.append(text)
        bot.send_message(message.chat.id, f"✅ Qo'shildi: <b>{text}</b>")

    render_step_7_amenities(message.chat.id, user_id=user_id)


@bot.callback_query_handler(func=lambda call: call.data == "wiz_back_to_amenities")
def handle_back_to_amenities(call: types.CallbackQuery):
    bot.clear_step_handler_by_chat_id(call.message.chat.id)
    render_step_7_amenities(call.message.chat.id, user_id=call.from_user.id, message_id=call.message.message_id)


@bot.callback_query_handler(func=lambda call: call.data == "wiz_back_to_residents")
def handle_back_to_residents(call: types.CallbackQuery):
    bot.clear_step_handler_by_chat_id(call.message.chat.id)
    render_step_6c_residents(call.message.chat.id, user_id=call.from_user.id, message_id=call.message.message_id)


@bot.callback_query_handler(func=lambda call: call.data == "wiz_back_to_gender")
def handle_back_to_gender(call: types.CallbackQuery):
    bot.clear_step_handler_by_chat_id(call.message.chat.id)
    render_step_6_gender(call.message.chat.id, user_id=call.from_user.id, message_id=call.message.message_id)


@bot.callback_query_handler(func=lambda call: call.data == "wiz_amenities_done")
def handle_amenities_done(call: types.CallbackQuery):
    user_id = call.from_user.id
    city_id = user_drafts.get(user_id, {}).get("city_id", 1)
    if city_id == 1:
        render_step_8_metro(call.message.chat.id, user_id=user_id, message_id=call.message.message_id)
    else:
        if user_id in user_drafts:
            user_drafts[user_id]["selected_metros"] = []
            user_drafts[user_id]["near_subway"] = ""
        render_step_9_universities(call.message.chat.id, user_id=user_id, message_id=call.message.message_id)


def safe_delete_message(chat_id, message_id):
    try:
        bot.delete_message(chat_id, message_id)
    except Exception:
        pass


# ==================== 8-BOSQICH: METRO ====================

def render_step_8_metro(chat_id, user_id, message_id=None):
    bot.clear_step_handler_by_chat_id(chat_id)
    if user_id not in user_drafts:
        user_drafts[user_id] = {"selected_metros": [], "near_subway": ""}

    selected = user_drafts[user_id].setdefault("selected_metros", [])
    if not selected and user_drafts[user_id].get("near_subway"):
        for m in user_drafts[user_id]["near_subway"].split(","):
            m_s = m.strip()
            if m_s and m_s not in selected:
                selected.append(m_s)

    markup = types.InlineKeyboardMarkup(row_width=2)
    chips = []
    for idx, name in enumerate(METRO_STATIONS):
        is_sel = name in selected
        label = f"✅ {name}" if is_sel else name
        chips.append(types.InlineKeyboardButton(label, callback_data=f"wiz_metro_{idx}"))
    markup.add(*chips)

    markup.row(types.InlineKeyboardButton("➕ Boshqa metro yozish", callback_data="wiz_custom_metro"))
    markup.row(types.InlineKeyboardButton("Davom etish ➡️", callback_data="wiz_metro_done"))
    markup.row(types.InlineKeyboardButton("⏭️ Metroga yaqin emas (O'tkazish)", callback_data="wiz_skip_metro"))
    markup.row(
        types.InlineKeyboardButton("⬅️ Orqaga", callback_data="wiz_back_to_amenities"),
        types.InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel_action")
    )

    sel_str = ", ".join(selected) if selected else "<i>Hozircha tanlanmadi (ixtiyoriy)</i>"
    text = (
        "🚇 <b>8-bosqich:</b> Yaqin metro bekatlari:\n\n"
        "<i>Kvartiraga yaqin metro bekatlarini tanlang (bir nechtasini tanlash mumkin) yoki o'zingiz yozing:</i>\n\n"
        f"Tanlangan metro bekatlari:\n<b>{sel_str}</b>"
    )

    if message_id:
        try:
            bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=text, reply_markup=markup)
            return
        except Exception:
            pass
    bot.send_message(chat_id=chat_id, text=text, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == "wiz_metro_done")
def handle_metro_done(call: types.CallbackQuery):
    user_id = call.from_user.id
    if user_id in user_drafts:
        selected = user_drafts[user_id].get("selected_metros", [])
        user_drafts[user_id]["near_subway"] = ", ".join(selected)
    render_step_9_universities(call.message.chat.id, user_id=user_id, message_id=call.message.message_id)


@bot.callback_query_handler(func=lambda call: call.data.startswith("wiz_metro_") and call.data != "wiz_metro_done")
def handle_metro_toggle(call: types.CallbackQuery):
    user_id = call.from_user.id
    if user_id not in user_drafts:
        init_user_draft(call.from_user)

    idx = int(call.data.replace("wiz_metro_", ""))
    if 0 <= idx < len(METRO_STATIONS):
        item_name = METRO_STATIONS[idx]
        selected = user_drafts[user_id].setdefault("selected_metros", [])
        if item_name in selected:
            selected.remove(item_name)
        else:
            selected.append(item_name)
        user_drafts[user_id]["near_subway"] = ", ".join(selected)

    render_step_8_metro(call.message.chat.id, user_id=user_id, message_id=call.message.message_id)


@bot.callback_query_handler(func=lambda call: call.data == "wiz_skip_metro")
def handle_skip_metro(call: types.CallbackQuery):
    user_id = call.from_user.id
    if user_id in user_drafts:
        user_drafts[user_id]["selected_metros"] = []
        user_drafts[user_id]["near_subway"] = ""
    render_step_9_universities(call.message.chat.id, user_id=user_id, message_id=call.message.message_id)


@bot.callback_query_handler(func=lambda call: call.data == "wiz_custom_metro")
def handle_custom_metro_prompt(call: types.CallbackQuery):
    bot.clear_step_handler_by_chat_id(call.message.chat.id)
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("⬅️ Metro ro'yxatiga qaytish", callback_data="wiz_back_to_metro"))

    msg = bot.send_message(
        call.message.chat.id,
        "✏️ <b>Yaqin metro bekati nomini yozing:</b>\n<i>(Masalan: Chilonzor, Alisher Navoiy, Turkiston...)</i>",
        reply_markup=markup
    )
    bot.register_next_step_handler(msg, process_custom_metro_step)


def process_custom_metro_step(message: types.Message):
    user_id = message.from_user.id
    if user_id not in user_drafts:
        bot.send_message(message.chat.id, "Boshidan boshlang: /new", reply_markup=get_main_menu_keyboard())
        return

    text = (message.text or "").strip()
    if text in ["⬅️ Orqaga", "/back"]:
        render_step_8_metro(message.chat.id, user_id=user_id)
        return
    if text in ["❌ Bekor qilish", "/cancel"]:
        handle_cancel_msg(message)
        return

    if len(text) >= 2:
        selected = user_drafts[user_id].setdefault("selected_metros", [])
        if text not in selected:
            selected.append(text)
        user_drafts[user_id]["near_subway"] = ", ".join(selected)
        bot.send_message(message.chat.id, f"✅ Qo'shildi: <b>{text}</b>")

    render_step_8_metro(message.chat.id, user_id=user_id)


@bot.callback_query_handler(func=lambda call: call.data == "wiz_back_to_metro")
def handle_back_to_metro(call: types.CallbackQuery):
    bot.clear_step_handler_by_chat_id(call.message.chat.id)
    render_step_8_metro(call.message.chat.id, user_id=call.from_user.id, message_id=call.message.message_id)


# ==================== 9-BOSQICH: O'QISH JOYLARI (OTM) ====================

def render_step_9_universities(chat_id, user_id, message_id=None):
    bot.clear_step_handler_by_chat_id(chat_id)
    if user_id not in user_drafts:
        user_drafts[user_id] = {"nearby_universities": []}

    selected = user_drafts[user_id].get("nearby_universities", [])
    city_id = user_drafts[user_id].get("city_id", 1)
    city_name = user_drafts[user_id].get("city_name") or dict(CITIES).get(city_id, "Toshkent")
    uni_list = CITY_UNIVERSITIES.get(city_id, CITY_UNIVERSITIES[1])

    markup = types.InlineKeyboardMarkup(row_width=2)
    chips = []
    for idx, name in enumerate(uni_list):
        is_sel = name in selected
        label = f"✅ {name}" if is_sel else name
        chips.append(types.InlineKeyboardButton(label, callback_data=f"wiz_uni_{idx}"))
    markup.add(*chips)

    markup.row(types.InlineKeyboardButton("➕ Boshqa OTM yozish", callback_data="wiz_custom_uni"))
    markup.row(types.InlineKeyboardButton("Davom etish ➡️", callback_data="wiz_unis_done"))
    
    back_cb = "wiz_back_to_metro" if city_id == 1 else "wiz_back_to_amenities"
    markup.row(
        types.InlineKeyboardButton("⬅️ Orqaga", callback_data=back_cb),
        types.InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel_action")
    )

    sel_str = ", ".join(selected) if selected else "<i>Hozircha tanlanmadi (ixtiyoriy)</i>"
    text = (
        f"🎓 <b>9-bosqich:</b> Yaqin o'qish joylari ({city_name}):\n\n"
        f"<i>Talabalar uchun qulay bo'lishi uchun yaqin oliygohlarni tanlang:</i>\n\n"
        f"Tanlangan OTMlar:\n<b>{sel_str}</b>"
    )

    if message_id:
        try:
            bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=text, reply_markup=markup)
            return
        except Exception:
            pass
    bot.send_message(chat_id=chat_id, text=text, reply_markup=markup)



@bot.callback_query_handler(func=lambda call: call.data == "wiz_unis_done")
def handle_unis_done(call: types.CallbackQuery):
    render_step_10_photo(call.message.chat.id, user_id=call.from_user.id, message_id=call.message.message_id)


@bot.callback_query_handler(func=lambda call: call.data.startswith("wiz_uni_") and call.data != "wiz_unis_done")
def handle_uni_toggle(call: types.CallbackQuery):
    user_id = call.from_user.id
    if user_id not in user_drafts:
        init_user_draft(call.from_user)

    city_id = user_drafts[user_id].get("city_id", 1)
    uni_list = CITY_UNIVERSITIES.get(city_id, CITY_UNIVERSITIES[1])

    idx = int(call.data.replace("wiz_uni_", ""))
    if 0 <= idx < len(uni_list):
        item_name = uni_list[idx]
        selected = user_drafts[user_id].setdefault("nearby_universities", [])
        if item_name in selected:
            selected.remove(item_name)
        else:
            selected.append(item_name)

    render_step_9_universities(call.message.chat.id, user_id=user_id, message_id=call.message.message_id)


@bot.callback_query_handler(func=lambda call: call.data == "wiz_custom_uni")
def handle_custom_uni_prompt(call: types.CallbackQuery):
    bot.clear_step_handler_by_chat_id(call.message.chat.id)
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("⬅️ OTMlar ro'yxatiga qaytish", callback_data="wiz_back_to_unis"))

    msg = bot.send_message(
        call.message.chat.id,
        "✏️ <b>Qo'shimcha OTM yoki o'quv markazi nomini yozing:</b>\n<i>(Masalan: Toshkent davlat yuridik universiteti, Singapur, Webster...)</i>",
        reply_markup=markup
    )
    bot.register_next_step_handler(msg, process_custom_uni_step)


def process_custom_uni_step(message: types.Message):
    user_id = message.from_user.id
    if user_id not in user_drafts:
        bot.send_message(message.chat.id, "Boshidan boshlang: /new", reply_markup=get_main_menu_keyboard())
        return

    text = (message.text or "").strip()
    if text in ["⬅️ Orqaga", "/back"]:
        render_step_9_universities(message.chat.id, user_id=user_id)
        return
    if text in ["❌ Bekor qilish", "/cancel"]:
        handle_cancel_msg(message)
        return

    if len(text) >= 2:
        selected = user_drafts[user_id].setdefault("nearby_universities", [])
        if text not in selected:
            selected.append(text)
        bot.send_message(message.chat.id, f"✅ Qo'shildi: <b>{text}</b>")

    render_step_9_universities(message.chat.id, user_id=user_id)


@bot.callback_query_handler(func=lambda call: call.data == "wiz_back_to_unis")
def handle_back_to_unis(call: types.CallbackQuery):
    bot.clear_step_handler_by_chat_id(call.message.chat.id)
    render_step_9_universities(call.message.chat.id, user_id=call.from_user.id, message_id=call.message.message_id)



# ==================== 10-BOSQICH: RASMLAR ====================

def render_step_10_photo(chat_id, user_id=None, message_id=None):
    bot.clear_step_handler_by_chat_id(chat_id)
    photo_count = 0
    if user_id and user_id in user_drafts:
        photo_count = len(user_drafts[user_id].get("photo_file_ids", []))

    markup = types.InlineKeyboardMarkup()
    if photo_count > 0:
        markup.add(types.InlineKeyboardButton(f"➡️ Davom etish ({photo_count} ta rasm)", callback_data="wiz_photos_done"))
        markup.add(types.InlineKeyboardButton("🗑 Rasmlarni tozalash", callback_data="wiz_clear_photos"))
    else:
        markup.add(types.InlineKeyboardButton("⏭️ Rasmsiz davom etish", callback_data="wiz_skip_photo"))

    markup.row(
        types.InlineKeyboardButton("⬅️ Orqaga", callback_data="wiz_back_to_unis"),
        types.InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel_action")
    )

    if photo_count > 0:
        text = (
            f"📸 <b>10-bosqich:</b> Yuklangan rasmlar: <b>{photo_count} ta</b>\n\n"
            f"<i>Yana boshqa rasmlar yuborishingiz mumkin. Barcha rasmlarni yuborib bo'lgach, pastdagi <b>«➡️ Davom etish»</b> tugmasini bosing:</i>"
        )
    else:
        text = (
            "📸 <b>10-bosqich:</b> Xona rasmlarini yuboring (bir yoki bir nechta):\n\n"
            "<i>Rasmlarni bittalab yoki bir nechta qilib yuborishingiz mumkin. Rasm bo'lmasa, pastdagi 'Rasmsiz davom etish' tugmasini bosing:</i>"
        )

    if message_id:
        try:
            bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=text, reply_markup=markup)
        except Exception:
            bot.send_message(chat_id=chat_id, text=text, reply_markup=markup)
    else:
        bot.send_message(chat_id=chat_id, text=text, reply_markup=markup)

    bot.register_next_step_handler_by_chat_id(chat_id, process_photo_step)


def process_photo_step(message: types.Message):
    user_id = message.from_user.id
    if user_id not in user_drafts:
        return

    text = (message.text or "").strip()
    if text in ["⬅️ Orqaga", "/back"]:
        render_step_9_universities(message.chat.id, user_id=user_id)
        return
    if text in ["❌ Bekor qilish", "/cancel"]:
        handle_cancel_msg(message)
        return
    if text in ["➡️ Davom etish", "Davom etish", "/next", "/done"]:
        render_step_11_phone(message.chat.id, user_id=user_id)
        return

    if message.content_type == 'photo':
        photo = message.photo[-1]
        photo_ids = user_drafts[user_id].setdefault("photo_file_ids", [])
        photo_ids.append(photo.file_id)
        user_drafts[user_id]["photo_file_id"] = photo_ids[0]

        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(f"➡️ Davom etish ({len(photo_ids)} ta rasm)", callback_data="wiz_photos_done"))
        markup.row(
            types.InlineKeyboardButton("⬅️ Orqaga", callback_data="wiz_back_to_unis"),
            types.InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel_action")
        )

        bot.send_message(
            message.chat.id,
            f"✅ Rasm qabul qilindi! Jami: <b>{len(photo_ids)} ta rasm</b>.\n\n"
            f"<i>Yana rasm yuborishingiz mumkin yoki davom etish uchun pastdagi <b>«➡️ Davom etish»</b> tugmasini bosing:</i>",
            reply_markup=markup
        )
        bot.register_next_step_handler_by_chat_id(message.chat.id, process_photo_step)
        return

    bot.send_message(
        message.chat.id,
        "Iltimos, rasm yuboring yoki pastdagi tugmalardan foydalaning."
    )
    render_step_10_photo(message.chat.id, user_id=user_id)


@bot.callback_query_handler(func=lambda call: call.data == "wiz_photos_done")
def handle_photos_done(call: types.CallbackQuery):
    bot.clear_step_handler_by_chat_id(call.message.chat.id)
    render_step_11_phone(call.message.chat.id, user_id=call.from_user.id)


@bot.callback_query_handler(func=lambda call: call.data == "wiz_clear_photos")
def handle_clear_photos(call: types.CallbackQuery):
    user_id = call.from_user.id
    if user_id in user_drafts:
        user_drafts[user_id]["photo_file_ids"] = []
        user_drafts[user_id]["photo_file_id"] = None
    render_step_10_photo(call.message.chat.id, user_id=user_id, message_id=call.message.message_id)


@bot.callback_query_handler(func=lambda call: call.data == "wiz_skip_photo")
def handle_skip_photo(call: types.CallbackQuery):
    bot.clear_step_handler_by_chat_id(call.message.chat.id)
    user_id = call.from_user.id
    if user_id in user_drafts:
        user_drafts[user_id]["photo_file_ids"] = []
        user_drafts[user_id]["photo_file_id"] = None
    render_step_11_phone(call.message.chat.id, user_id=user_id)


# ==================== 11-BOSQICH: TELEFON RAQAM ====================

def render_step_11_phone(chat_id, user_id=None):
    bot.clear_step_handler_by_chat_id(chat_id)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(types.KeyboardButton("📱 Telefon raqamimni ulashish", request_contact=True))
    markup.row(types.KeyboardButton("⬅️ Orqaga"), types.KeyboardButton("❌ Bekor qilish"))

    msg = bot.send_message(
        chat_id,
        "📞 <b>11-bosqich:</b> Bog'lanish uchun telefon raqamingizni yuboring:\n"
        "<i>Pastdagi «📱 Telefon raqamimni ulashish» tugmasini bosing yoki raqamingizni yozing (+998901234567):</i>",
        reply_markup=markup
    )
    bot.register_next_step_handler(msg, process_phone_step)


def process_phone_step(message: types.Message):
    user_id = message.from_user.id
    if user_id not in user_drafts:
        bot.send_message(message.chat.id, "Sessiya tugadi. Qaytadan boshlang: /new", reply_markup=types.ReplyKeyboardRemove())
        return

    text = (message.text or "").strip()
    if text in ["⬅️ Orqaga", "/back"]:
        bot.send_message(message.chat.id, "Orqaga qaytildi.", reply_markup=types.ReplyKeyboardRemove())
        render_step_10_photo(message.chat.id, user_id=user_id)
        return
    if text in ["❌ Bekor qilish", "/cancel"]:
        bot.send_message(message.chat.id, "E'lon bekor qilindi.", reply_markup=types.ReplyKeyboardRemove())
        handle_cancel_msg(message)
        return

    phone = ""
    if message.contact:
        phone = message.contact.phone_number
        if not phone.startswith("+"):
            phone = "+" + phone
    elif message.text:
        raw = message.text.strip()
        phone = "".join(c for c in raw if c.isdigit() or c == "+")
        if not phone.startswith("+") and phone:
            phone = "+" + phone

    if len(phone) < 9:
        msg = bot.send_message(
            message.chat.id,
            "❌ Noto'g'ri telefon raqami. Iltimos, tugma orqali yuboring yoki to'liq yozing (+998901234567):"
        )
        bot.register_next_step_handler(msg, process_phone_step)
        return

    user_drafts[user_id]["phone_number"] = phone
    bot.send_message(message.chat.id, "✅ Telefon raqamingiz qabul qilindi.", reply_markup=types.ReplyKeyboardRemove())

    # 12-bosqich: To'liq ko'rib chiqish va tasdiqlash
    render_step_12_confirm(message.chat.id, user_id=user_id)


# ==================== 12-BOSQICH: TASDIQLASH VA SAQLASH ====================

def render_step_12_confirm(chat_id, user_id, message_id=None):
    bot.clear_step_handler_by_chat_id(chat_id)
    if user_id not in user_drafts:
        bot.send_message(chat_id, "Sessiya tugadi. Qaytadan boshlang: /new", reply_markup=get_main_menu_keyboard())
        return

    draft = user_drafts[user_id]

    type_name = "🏠 Xonam bor (Sherik kerak)" if draft.get("listing_type") == "have_room" else "🔍 Xona kerak (Ijara qidiryapman)"
    city_name = draft.get("city_name") or dict(CITIES).get(draft.get("city_id", 1), "Toshkent")
    price_disp = format_price_display(draft.get("price", 0), draft.get("currency", "USD"))

    is_have = draft.get("listing_type") == "have_room"
    if is_have:
        gender_map = {
            "male": "👨 Faqat o'g'il bolalar / erkaklar",
            "female": "👩 Faqat qizlar / ayollar",
            "any": "🤝 Farqi yo'q"
        }
        gender_disp = gender_map.get(draft.get("gender_preference"), "Farqi yo'q")
        gender_line = f"👥 <b>Kim uchun:</b> {gender_disp}"
    else:
        gender_disp = "👨 Yigit kishi" if draft.get("gender_preference") == "male" else ("👩 Qiz bola" if draft.get("gender_preference") == "female" else "Kiritilmagan")
        gender_line = f"👤 <b>Qidiruvchining jinsi:</b> {gender_disp}"

    amenities = draft.get("amenities", [])
    amenities_disp = ", ".join(amenities) if amenities else "Kiritilmadi"

    metros = draft.get("selected_metros", [])
    if not metros and draft.get("near_subway"):
        metros = [m.strip() for m in draft.get("near_subway", "").split(",") if m.strip()]
    metro_disp = ", ".join(metros) if metros else "Metroga yaqin emas"

    unis = draft.get("nearby_universities", [])
    unis_disp = ", ".join(unis) if unis else "Kiritilmadi"

    photos = draft.get("photo_file_ids", [])
    photos_count = len(photos)

    summary_card = (
        "📋 <b>E'LONNI TASDIQLASH (12-bosqich)</b>\n\n"
        "<i>E'lon ma'lumotlarini diqqat bilan tekshiring:</i>\n\n"
        f"🏷 <b>Sarlavha:</b> {draft.get('title', '')}\n"
        f"📝 <b>Tavsif:</b> {draft.get('description', '')}\n"
        f"📌 <b>E'lon turi:</b> {type_name}\n"
        f"📍 <b>Shahar:</b> {city_name}\n"
        f"💰 <b>Narxi:</b> {price_disp}\n"
        f"{gender_line}\n"
        f"👥 <b>Talab qilinadigan sherik:</b> {draft.get('capacity', 1)} nafar\n"
        f"🏠 <b>Kvartirada jami yashovchilar:</b> {draft.get('total_residents', 2)} kishi\n"
        f"🚇 <b>Yaqin metro:</b> {metro_disp}\n"
        f"🎓 <b>Yaqin OTMlar:</b> {unis_disp}\n"
        f"🛋 <b>Qulayliklar:</b> {amenities_disp}\n"
        f"📸 <b>Rasmlar:</b> {photos_count} ta rasm\n"
        f"📞 <b>Bog'lanish:</b> {draft.get('phone_number', '')}\n\n"
        "Hammasi to'g'ri bo'lsa, pastdagi <b>«✅ E'lonni saqlash»</b> tugmasini bosing:"
    )

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ E'lonni saqlash", callback_data="wiz_confirm_save"))
    markup.row(
        types.InlineKeyboardButton("⬅️ Telefonni o'zgartirish", callback_data="wiz_back_to_phone"),
        types.InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel_action")
    )

    if photos:
        try:
            bot.send_photo(
                chat_id=chat_id,
                photo=photos[0],
                caption=summary_card,
                reply_markup=markup
            )
            return
        except Exception:
            pass

    if message_id:
        try:
            bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=summary_card, reply_markup=markup)
            return
        except Exception:
            pass
    bot.send_message(chat_id=chat_id, text=summary_card, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == "wiz_back_to_phone")
def handle_back_to_phone(call: types.CallbackQuery):
    bot.clear_step_handler_by_chat_id(call.message.chat.id)
    render_step_11_phone(call.message.chat.id, user_id=call.from_user.id)


@bot.callback_query_handler(func=lambda call: call.data == "wiz_confirm_save")
def handle_confirm_save(call: types.CallbackQuery):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    bot.clear_step_handler_by_chat_id(chat_id)

    if user_id not in user_drafts:
        bot.send_message(chat_id, "Sessiya tugadi. Qaytadan boshlang: /new", reply_markup=get_main_menu_keyboard())
        return

    wait_msg = bot.send_message(chat_id, "⏳ E'lon saqlanmoqda, kuting...")

    draft = user_drafts[user_id]

    try:
        # 1. Telegram user orqali backend'dan JWT token olish
        auth_data = {
            "telegram_id": draft.get("telegram_id", user_id),
            "first_name": draft.get("first_name", call.from_user.first_name or "Telegram User"),
            "last_name": draft.get("last_name", call.from_user.last_name or ""),
            "username": draft.get("username", call.from_user.username or ""),
            "phone_number": draft.get("phone_number", "")
        }
        auth_resp = requests.post(f"{API_BASE_URL}/auth/telegram/", json=auth_data, timeout=15)

        if auth_resp.status_code != 200:
            safe_delete_message(chat_id, wait_msg.message_id)
            bot.send_message(
                chat_id=chat_id,
                text=f"❌ Autentifikatsiya xatosi: {auth_resp.text}",
                reply_markup=get_main_menu_keyboard()
            )
            return

        token = auth_resp.json().get("access")
        headers = {"Authorization": f"Bearer {token}"}

        # 2. E'lonni yaratish
        near_subway = draft.get("near_subway", "")
        if not near_subway and draft.get("selected_metros"):
            near_subway = ", ".join(draft.get("selected_metros"))

        listing_payload = {
            "title": draft.get("title", "Sherik kerak"),
            "description": draft.get("description", "Kvartiraga sherik kerak"),
            "listing_type": draft.get("listing_type", "have_room"),
            "city_id": draft.get("city_id", 1),
            "price": int(round(float(draft.get("price", 100)))),
            "currency": draft.get("currency", "USD"),
            "capacity": draft.get("capacity", 1),
            "total_residents": draft.get("total_residents", 2),
            "gender_preference": draft.get("gender_preference", "any"),
            "amenities": draft.get("amenities", []),
            "near_subway": near_subway,
            "nearby_universities": draft.get("nearby_universities", []),
        }

        create_resp = requests.post(f"{API_BASE_URL}/listings/", json=listing_payload, headers=headers, timeout=15)

        if create_resp.status_code not in [200, 201]:
            safe_delete_message(chat_id, wait_msg.message_id)
            bot.send_message(
                chat_id=chat_id,
                text=f"❌ E'lon yaratishda xato: {create_resp.text}",
                reply_markup=get_main_menu_keyboard()
            )
            return

        listing_id = create_resp.json().get("id")

        # 3. Rasmlarni yuklash (barcha yuklangan rasmlar)
        photo_ids = draft.get("photo_file_ids", [])
        if not photo_ids and draft.get("photo_file_id"):
            photo_ids = [draft["photo_file_id"]]

        for idx, photo_id in enumerate(photo_ids):
            try:
                file_info = bot.get_file(photo_id)
                downloaded_file = bot.download_file(file_info.file_path)

                files = {
                    "image": (f"photo_{idx}.jpg", io.BytesIO(downloaded_file), "image/jpeg")
                }
                data = {"is_main": "true" if idx == 0 else "false"}
                requests.post(
                    f"{API_BASE_URL}/listings/{listing_id}/photos/",
                    headers=headers,
                    files=files,
                    data=data,
                    timeout=30
                )
            except Exception as pe:
                print(f"Rasm #{idx} yuklash xatosi: {pe}")

        # Tugatish va tozalash
        if user_id in user_drafts:
            del user_drafts[user_id]

        price_disp = format_price_display(listing_payload["price"], listing_payload["currency"])
        amenities_disp = ", ".join(listing_payload["amenities"]) if listing_payload["amenities"] else "Yo'q"
        metro_disp = listing_payload["near_subway"] if listing_payload["near_subway"] else "Yo'q"
        unis_disp = ", ".join(listing_payload["nearby_universities"]) if listing_payload["nearby_universities"] else "Yo'q"

        success_text = (
            f"🎉 <b>E'loningiz muvaffaqiyatli saqlandi!</b>\n\n"
            f"📋 <b>E'lon raqami:</b> #{listing_id}\n"
            f"💰 <b>Narx:</b> {price_disp}\n"
            f"🚇 <b>Yaqin metro:</b> {metro_disp}\n"
            f"🎓 <b>Yaqin OTMlar:</b> {unis_disp}\n"
            f"🛋 <b>Jihozlar:</b> {amenities_disp}\n"
            f"📸 <b>Yuklangan rasmlar:</b> {len(photo_ids)} ta\n"
            f"📌 <b>Holat:</b> ⏳ Moderatsiyada (kutilmoqda)\n\n"
            f"<i>Adminlarimiz tekshirib tasdiqlagach, e'lon ilovada va botda hamma uchun ko'rinadi!</i>"
        )

        fin_markup = types.InlineKeyboardMarkup()
        fin_markup.add(types.InlineKeyboardButton(
            text="📱 Ilovada ko'rish",
            web_app=types.WebAppInfo(url=f"{MINI_APP_URL}/listings/{listing_id}")
        ))
        fin_markup.add(types.InlineKeyboardButton(text="🏠 Bosh menyu", callback_data="btn_back_to_menu"))

        safe_delete_message(chat_id, wait_msg.message_id)
        bot.send_message(
            chat_id=chat_id,
            text=success_text,
            reply_markup=fin_markup
        )

    except Exception as e:
        safe_delete_message(chat_id, wait_msg.message_id)
        bot.send_message(
            chat_id=chat_id,
            text=f"❌ Tizim xatosi yuz berdi: {e}",
            reply_markup=get_main_menu_keyboard()
        )


def handle_cancel_msg(message: types.Message):
    """Xabar orqali bekor qilish."""
    user_id = message.from_user.id
    bot.clear_step_handler_by_chat_id(message.chat.id)
    if user_id in user_drafts:
        del user_drafts[user_id]
    bot.send_message(
        chat_id=message.chat.id,
        text="❌ E'lon berish bekor qilindi.\n\n📌 Asosiy menyu:",
        reply_markup=get_main_menu_keyboard()
    )


@bot.callback_query_handler(func=lambda call: call.data == "btn_my_listings")
def handle_my_listings(call: types.CallbackQuery):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    bot.clear_step_handler_by_chat_id(chat_id)

    wait_msg = bot.send_message(chat_id, "⏳ E'lonlaringiz yuklanmoqda...")

    try:
        auth_data = {
            "telegram_id": user_id,
            "first_name": call.from_user.first_name or "",
            "username": call.from_user.username or "",
        }
        auth_resp = requests.post(f"{API_BASE_URL}/auth/telegram/", json=auth_data, timeout=15)
        if auth_resp.status_code != 200:
            safe_delete_message(chat_id, wait_msg.message_id)
            bot.send_message(chat_id, "❌ Tizimga ulanishda xatolik yuz berdi.", reply_markup=get_main_menu_keyboard())
            return

        token = auth_resp.json().get("access")
        headers = {"Authorization": f"Bearer {token}"}
        my_resp = requests.get(f"{API_BASE_URL}/listings/my/", headers=headers, timeout=15)

        safe_delete_message(chat_id, wait_msg.message_id)

        if my_resp.status_code != 200:
            bot.send_message(chat_id, "❌ E'lonlarni olishda xatolik yuz berdi.", reply_markup=get_main_menu_keyboard())
            return

        results = my_resp.json().get("results", [])
        if not results:
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("📋 Yangi e'lon berish", callback_data="btn_new_listing"))
            markup.add(types.InlineKeyboardButton("🏠 Bosh menyu", callback_data="btn_back_to_menu"))
            bot.send_message(
                chat_id=chat_id,
                text="📭 <b>Sizda hali e'lonlar mavjud emas.</b>\n\nBirinchi e'loningizni joylashtirish uchun pastdagi tugmani bosing:",
                reply_markup=markup
            )
            return

        bot.send_message(
            chat_id=chat_id,
            text=f"👤 <b>Sizning e'lonlaringiz (jami {len(results)} ta):</b>\n\n<i>Har bir e'lonni tahrirlashingiz, o'chirishingiz yoki ilovada ko'rishingiz mumkin:</i>"
        )

        status_map = {
            "pending": "⏳ Moderatsiyada (kutilmoqda)",
            "approved": "✅ Faol va tasdiqlangan",
            "rejected": "❌ Rad etilgan",
            "closed": "🔒 Yopilgan / Arxivda"
        }

        for l in results:
            lid = l.get("id")
            type_icon = "🏠 Xonam bor (Sherik kerak)" if l.get("listing_type") == "have_room" else "🔍 Xona kerak (Ijara qidiryapman)"
            price_disp = format_price_display(l.get('price', 0), l.get('currency', 'USD'))
            st_text = status_map.get(l.get("moderation_status"), l.get("moderation_status"))

            city_name = l.get("city_name") or "O'zbekiston"
            metro_line = f"\n🚇 <b>Metro:</b> {l.get('near_subway')}" if l.get('near_subway') else ""
            unis = l.get("nearby_universities", [])
            unis_line = f"\n🎓 <b>OTM:</b> {', '.join(unis)}" if unis else ""
            cap = l.get("capacity", 1)
            tot = l.get("total_residents", 2)
            rej_line = f"\n⚠️ <b>Rad etish sababi:</b> {l.get('rejection_reason')}" if l.get('rejection_reason') else ""

            card_text = (
                f"<b>{l.get('title')}</b>\n\n"
                f"📌 <b>Turi:</b> {type_icon}\n"
                f"📍 <b>Shahar:</b> {city_name}\n"
                f"💰 <b>Narxi:</b> {price_disp}\n"
                f"👥 <b>Talab:</b> {cap} nafar sherik | Jami yashovchilar: {tot} kishi\n"
                f"📊 <b>Holat:</b> {st_text}{rej_line}"
                f"{metro_line}{unis_line}\n\n"
                f"🆔 <b>ID:</b> #{lid}"
            )

            item_markup = types.InlineKeyboardMarkup()
            item_markup.row(
                types.InlineKeyboardButton("✏️ Tahrirlash", callback_data=f"my_edit_{lid}"),
                types.InlineKeyboardButton("🗑 O'chirish", callback_data=f"my_del_{lid}")
            )
            item_markup.row(
                types.InlineKeyboardButton("📱 Ilovada ko'rish", web_app=types.WebAppInfo(url=f"{MINI_APP_URL}/listings/{lid}"))
            )

            main_photo = l.get("main_photo")
            if main_photo:
                try:
                    bot.send_photo(chat_id, photo=main_photo, caption=card_text, reply_markup=item_markup)
                except Exception:
                    bot.send_message(chat_id, card_text, reply_markup=item_markup)
            else:
                bot.send_message(chat_id, card_text, reply_markup=item_markup)

        # Navigatsiya
        fin_markup = types.InlineKeyboardMarkup(row_width=2)
        fin_markup.add(
            types.InlineKeyboardButton("➕ Yangi e'lon", callback_data="btn_new_listing"),
            types.InlineKeyboardButton("🏠 Bosh menyu", callback_data="btn_back_to_menu")
        )
        bot.send_message(chat_id, "📌 Amallar:", reply_markup=fin_markup)

    except Exception as e:
        safe_delete_message(chat_id, wait_msg.message_id)
        bot.send_message(chat_id, f"❌ Xatolik yuz berdi: {e}", reply_markup=get_main_menu_keyboard())


# ==================== E'LONNI TAHRIRLASH VA O'CHIRISH ====================

@bot.callback_query_handler(func=lambda call: call.data.startswith("my_edit_"))
def handle_my_listing_edit_menu(call: types.CallbackQuery):
    bot.clear_step_handler_by_chat_id(call.message.chat.id)
    lid = int(call.data.replace("my_edit_", ""))

    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("💰 Narxni o'zgartirish", callback_data=f"medt_p_{lid}"),
        types.InlineKeyboardButton("🏷 Sarlavhani o'zgartirish", callback_data=f"medt_t_{lid}"),
        types.InlineKeyboardButton("📝 Tavsifni o'zgartirish", callback_data=f"medt_d_{lid}"),
        types.InlineKeyboardButton("👥 Sheriklar sonini o'zgartirish", callback_data=f"medt_c_{lid}"),
        types.InlineKeyboardButton("⬅️ E'lonlarimga qaytish", callback_data="btn_my_listings")
    )
    bot.send_message(
        call.message.chat.id,
        f"✏️ <b>#{lid} — E'lonni tahrirlash:</b>\n\nNimani o'zgartirmoqchisiz?",
        reply_markup=markup
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith("medt_p_"))
def handle_edit_price_prompt(call: types.CallbackQuery):
    bot.clear_step_handler_by_chat_id(call.message.chat.id)
    lid = int(call.data.replace("medt_p_", ""))
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("⬅️ Orqaga", callback_data=f"my_edit_{lid}"))
    msg = bot.send_message(
        call.message.chat.id,
        f"💰 <b>#{lid} — Yangi narxni kiriting:</b>\n<i>(Masalan: 120 yoki 1500000)</i>",
        reply_markup=markup
    )
    bot.register_next_step_handler(msg, process_edit_price, lid)


def process_edit_price(message: types.Message, listing_id: int):
    text = (message.text or "").strip()
    digits = "".join(c for c in text if c.isdigit())
    if not digits:
        msg = bot.send_message(message.chat.id, "❌ Iltimos, narxni faqat raqamlarda kiriting:")
        bot.register_next_step_handler(msg, process_edit_price, listing_id)
        return

    new_price = int(digits)
    _patch_listing(message.chat.id, message.from_user, listing_id, {"price": new_price})


@bot.callback_query_handler(func=lambda call: call.data.startswith("medt_t_"))
def handle_edit_title_prompt(call: types.CallbackQuery):
    bot.clear_step_handler_by_chat_id(call.message.chat.id)
    lid = int(call.data.replace("medt_t_", ""))
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("⬅️ Orqaga", callback_data=f"my_edit_{lid}"))
    msg = bot.send_message(
        call.message.chat.id,
        f"🏷 <b>#{lid} — Yangi sarlavhani yozing:</b>\n<i>(Kamida 5 ta belgi)</i>",
        reply_markup=markup
    )
    bot.register_next_step_handler(msg, process_edit_title, lid)


def process_edit_title(message: types.Message, listing_id: int):
    title = (message.text or "").strip()
    if len(title) < 5:
        msg = bot.send_message(message.chat.id, "❌ Sarlavha juda qisqa. Kamida 5 ta belgi yozing:")
        bot.register_next_step_handler(msg, process_edit_title, listing_id)
        return

    _patch_listing(message.chat.id, message.from_user, listing_id, {"title": title})


@bot.callback_query_handler(func=lambda call: call.data.startswith("medt_d_"))
def handle_edit_desc_prompt(call: types.CallbackQuery):
    bot.clear_step_handler_by_chat_id(call.message.chat.id)
    lid = int(call.data.replace("medt_d_", ""))
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("⬅️ Orqaga", callback_data=f"my_edit_{lid}"))
    msg = bot.send_message(
        call.message.chat.id,
        f"📝 <b>#{lid} — Yangi tavsifni yozing:</b>\n<i>(Kamida 10 ta belgi)</i>",
        reply_markup=markup
    )
    bot.register_next_step_handler(msg, process_edit_desc, lid)


def process_edit_desc(message: types.Message, listing_id: int):
    desc = (message.text or "").strip()
    if len(desc) < 10:
        msg = bot.send_message(message.chat.id, "❌ Tavsif juda qisqa. Kamida 10 ta belgi yozing:")
        bot.register_next_step_handler(msg, process_edit_desc, listing_id)
        return

    _patch_listing(message.chat.id, message.from_user, listing_id, {"description": desc})


@bot.callback_query_handler(func=lambda call: call.data.startswith("medt_c_"))
def handle_edit_cap_menu(call: types.CallbackQuery):
    bot.clear_step_handler_by_chat_id(call.message.chat.id)
    lid = int(call.data.replace("medt_c_", ""))
    markup = types.InlineKeyboardMarkup(row_width=3)
    markup.add(
        types.InlineKeyboardButton("1 nafar", callback_data=f"mset_c_{lid}_1"),
        types.InlineKeyboardButton("2 nafar", callback_data=f"mset_c_{lid}_2"),
        types.InlineKeyboardButton("3 nafar", callback_data=f"mset_c_{lid}_3"),
        types.InlineKeyboardButton("4 nafar", callback_data=f"mset_c_{lid}_4"),
        types.InlineKeyboardButton("5+ nafar", callback_data=f"mset_c_{lid}_5"),
        types.InlineKeyboardButton("⬅️ Orqaga", callback_data=f"my_edit_{lid}")
    )
    bot.send_message(
        call.message.chat.id,
        f"👥 <b>#{lid} — Nechta sherik kerakligini tanlang:</b>",
        reply_markup=markup
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith("mset_c_"))
def handle_set_cap(call: types.CallbackQuery):
    parts = call.data.split("_")
    lid = int(parts[2])
    cap = int(parts[3])
    _patch_listing(call.message.chat.id, call.from_user, lid, {"capacity": cap})


def _patch_listing(chat_id, user, listing_id, patch_data):
    try:
        auth_data = {
            "telegram_id": user.id,
            "first_name": user.first_name or "",
            "username": user.username or "",
        }
        auth_resp = requests.post(f"{API_BASE_URL}/auth/telegram/", json=auth_data, timeout=15)
        if auth_resp.status_code == 200:
            token = auth_resp.json().get("access")
            headers = {"Authorization": f"Bearer {token}"}
            resp = requests.patch(f"{API_BASE_URL}/listings/{listing_id}/", json=patch_data, headers=headers, timeout=15)
            if resp.status_code in [200, 204]:
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton("👤 Mening e'lonlarim", callback_data="btn_my_listings"))
                markup.add(types.InlineKeyboardButton("🏠 Bosh menyu", callback_data="btn_back_to_menu"))
                bot.send_message(
                    chat_id,
                    f"✅ <b>#{listing_id} raqamli e'lon muvaffaqiyatli tahrirlandi!</b>",
                    reply_markup=markup
                )
                return
            else:
                bot.send_message(chat_id, f"❌ Tahrirlashda xato: {resp.text}")
                return
        bot.send_message(chat_id, "❌ Autentifikatsiya xatosi yuz berdi.")
    except Exception as e:
        bot.send_message(chat_id, f"❌ Xatolik: {e}")


@bot.callback_query_handler(func=lambda call: call.data.startswith("my_del_") and not call.data.startswith("my_del_confirm_"))
def handle_del_prompt(call: types.CallbackQuery):
    lid = int(call.data.replace("my_del_", ""))
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🗑 Ha, o'chirish", callback_data=f"my_del_confirm_{lid}"),
        types.InlineKeyboardButton("❌ Yo'q, bekor qilish", callback_data="btn_my_listings")
    )
    bot.send_message(
        call.message.chat.id,
        f"⚠️ <b>#{lid} raqamli e'lonni rostdan ham o'chirmoqchimisiz?</b>\n\nBu amalni ortga qaytarib bo'lmaydi.",
        reply_markup=markup
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith("my_del_confirm_"))
def handle_del_confirm(call: types.CallbackQuery):
    lid = int(call.data.replace("my_del_confirm_", ""))
    chat_id = call.message.chat.id
    try:
        auth_data = {
            "telegram_id": call.from_user.id,
            "first_name": call.from_user.first_name or "",
            "username": call.from_user.username or "",
        }
        auth_resp = requests.post(f"{API_BASE_URL}/auth/telegram/", json=auth_data, timeout=15)
        if auth_resp.status_code == 200:
            token = auth_resp.json().get("access")
            headers = {"Authorization": f"Bearer {token}"}
            del_resp = requests.delete(f"{API_BASE_URL}/listings/{lid}/", headers=headers, timeout=15)
            if del_resp.status_code in [200, 204]:
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton("👤 E'lonlarimga qaytish", callback_data="btn_my_listings"))
                bot.send_message(
                    chat_id,
                    f"🗑 <b>#{lid} raqamli e'lon muvaffaqiyatli o'chirildi!</b>",
                    reply_markup=markup
                )
                return
            else:
                bot.send_message(chat_id, f"❌ O'chirishda xatolik: {del_resp.text}")
                return
        bot.send_message(chat_id, "❌ Autentifikatsiya xatosi.")
    except Exception as e:
        bot.send_message(chat_id, f"❌ Xatolik: {e}")


@bot.callback_query_handler(func=lambda call: call.data in ["cancel_action", "btn_back_to_menu"])
def handle_cancel(call: types.CallbackQuery):
    user_id = call.from_user.id
    bot.clear_step_handler_by_chat_id(call.message.chat.id)
    if user_id in user_drafts:
        del user_drafts[user_id]
    try:
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="📌 Asosiy menyu:",
            reply_markup=get_main_menu_keyboard()
        )
    except Exception:
        bot.send_message(
            chat_id=call.message.chat.id,
            text="📌 Asosiy menyu:",
            reply_markup=get_main_menu_keyboard()
        )


@bot.callback_query_handler(func=lambda call: call.data == "btn_help")
def handle_help_callback(call: types.CallbackQuery):
    text = (
        "ℹ️ <b>Sherik Bot bo'yicha ko'rsatmalar:</b>\n\n"
        "• <b>📱 Ilova</b> — Ilovani to'liq holda Telegram ichida ochadi.\n"
        "• <b>📋 E'lon joylash</b> — Saytga kirmasdan bot orqali e'lon joylaysiz.\n"
        "• <b>🔍 E'lonlar</b> — Barcha tasdiqlangan e'lonlarni ko'rish.\n\n"
        "Savol va takliflar bo'yicha: @sherik_support"
    )
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("⬅️ Bosh menyuga qaytish", callback_data="btn_back_to_menu"))
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=text, reply_markup=markup)


if __name__ == "__main__":
    threading.Thread(target=_keep_alive_loop, daemon=True).start()
    print("🤖 @SheriktopishBot ishga tushmoqda...")
    bot.infinity_polling(skip_pending=True)

