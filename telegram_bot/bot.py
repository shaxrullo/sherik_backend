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

CITY_DISTRICTS = {
    1: [
        (1, "Yunusobod"), (2, "Chilonzor"), (3, "Yakkasaroy"), (4, "Mirzo Ulug'bek"),
        (5, "Shayxontohur"), (6, "Uchtepa"), (7, "Olmazor"), (8, "Bektemir"),
        (9, "Sergeli"), (10, "Yangihayot"), (11, "Mirobod"), (12, "Yashnobod")
    ],
    2: [
        (13, "Samarqand shahri"), (14, "Urgut"), (15, "Bulungur"), (16, "Kattaqo'rg'on"),
        (17, "Narpay"), (18, "Paxtachi"), (19, "Payariq"), (20, "Pastdarg'om")
    ],
    3: [
        (21, "Buxoro shahri"), (22, "G'ijduvon"), (23, "Kogon"), (24, "Qorovulbozor"),
        (25, "Romitan"), (26, "Shofirkon"), (27, "Vobkent")
    ],
    4: [
        (28, "Andijon shahri"), (29, "Asaka"), (30, "Baliqchi"), (31, "Bo'z"),
        (32, "Jalaquduq"), (33, "Marhamat"), (34, "Oltinkul"), (35, "Paxtaobod"),
        (36, "Qo'rg'ontepa"), (37, "Shahrixon"), (38, "Xo'jaobod")
    ],
    5: [
        (39, "Namangan shahri"), (40, "Chortoq"), (41, "Chust"), (42, "Kosonsoy"),
        (43, "Mingbuloq"), (44, "Norin"), (45, "Pop"), (46, "To'raqo'rg'on"),
        (47, "Uchqo'rg'on"), (48, "Uychi"), (49, "Yangiqo'rg'on")
    ],
    6: [
        (50, "Farg'ona shahri"), (51, "Beshariq"), (52, "Bog'dod"), (53, "Buvayda"),
        (54, "Dang'ara"), (55, "Furqat"), (56, "Qo'shtepa"), (57, "Quva"),
        (58, "Rishton"), (59, "So'x"), (60, "Toshloq"), (61, "Uchko'prik"), (62, "Yozyovon")
    ],
    7: [
        (63, "Qarshi"), (64, "Chiroqchi"), (65, "Dehqonobod"), (66, "G'uzor"),
        (67, "Kamashi"), (68, "Kasbi"), (69, "Kitob"), (70, "Koson"),
        (71, "Mirishkor"), (72, "Muborak"), (73, "Nishon"), (74, "Shahrisabz")
    ],
    8: [
        (75, "Termiz"), (76, "Angor"), (77, "Bandixon"), (78, "Boysun"),
        (79, "Denov"), (80, "Jarqo'rg'on"), (81, "Qiziriq"), (82, "Qumqo'rg'on"),
        (83, "Muzrabot"), (84, "Oltinsoy"), (85, "Sariosiyo"), (86, "Sherobod"), (87, "Uzun")
    ],
    9: [
        (88, "Urganch"), (89, "Bog'ot"), (90, "Gurlan"), (91, "Xonqa"),
        (92, "Xiva"), (93, "Hazorasp"), (94, "Shovot"), (95, "Tuproqqal'a"),
        (96, "Yangiariq"), (97, "Yangibozor")
    ],
    10: [
        (98, "Jizzax shahri"), (99, "Arnasoy"), (100, "Baxmal"), (101, "Do'stlik"),
        (102, "Forish"), (103, "G'allaorol"), (104, "Mirzacho'l"), (105, "Paxtakor"),
        (106, "Sharof Rashidov"), (107, "Yangiobod"), (108, "Zafarobod")
    ],
    11: [
        (109, "Guliston"), (110, "Boyovut"), (111, "Mirzaobod"), (112, "Oqoltin"),
        (113, "Sardoba"), (114, "Sayxunobod"), (115, "Shirin"), (116, "Xovos")
    ],
    12: [
        (117, "Navoiy shahri"), (118, "Karmana"), (119, "Konimex"), (120, "Navbahor"),
        (121, "Nurota"), (122, "Tomdi"), (123, "Uchquduq"), (124, "Xatirchi"), (125, "Zarafshon")
    ],
    13: [
        (126, "Nukus"), (127, "Amudaryo"), (128, "Beruniy"), (129, "Chimboy"),
        (130, "Ellikkala"), (131, "Kegeyli"), (132, "Mo'ynoq"), (133, "Nukus tumani"),
        (134, "Qanliko'l"), (135, "Qo'ng'irot"), (136, "Shumanay"), (137, "Taxtako'pir"),
        (138, "To'rtko'l"), (139, "Xo'jayli")
    ]
}

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
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_webapp = types.InlineKeyboardButton(
        text="🚀 Ilovani ochish",
        web_app=types.WebAppInfo(url=MINI_APP_URL)
    )
    btn_new = types.InlineKeyboardButton(
        text="📋 E'lon joylash (Ilovada)",
        web_app=types.WebAppInfo(url=f"{MINI_APP_URL}/listings/new")
    )
    btn_browse = types.InlineKeyboardButton(
        text="🔍 E'lonlar (Ilovada)",
        web_app=types.WebAppInfo(url=MINI_APP_URL)
    )
    btn_my = types.InlineKeyboardButton(
        text="👤 Mening e'lonlarim",
        web_app=types.WebAppInfo(url=f"{MINI_APP_URL}/my/listings")
    )

    markup.add(btn_webapp)
    markup.add(btn_new)
    markup.add(btn_browse)
    markup.add(btn_my)
    return markup


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
    text = (
        f"Assalomu alaykum, <b>{user_name}</b>! 👋\n\n"
        f"<b>Sherik Topish</b> rasmiy botiga xush kelibsiz.\n\n"
        f"Xavfsizlik va qulaylik uchun botga to'g'ridan-to'g'ri xabar yozish o'chirilgan. "
        f"Barcha xizmatlar (e'lon berish, xona qidirish, sherik topish) zamonaviy <b>«📱 Ilova»</b> orqali amalga oshiriladi.\n\n"
        f"Xizmatdan foydalanish uchun pastdagi <b>«🚀 Ilovani ochish»</b> tugmasini bosing:"
    )
    bot.send_message(
        chat_id=message.chat.id,
        text=text,
        reply_markup=get_main_menu_keyboard()
    )


@bot.message_handler(func=lambda message: True, content_types=['text', 'photo', 'video', 'document', 'audio', 'voice', 'location', 'contact', 'sticker'])
def handle_all_messages_blocked(message: types.Message):
    """Botga yozishni hammaga (shu jumladan adminga ham) o'chirib qo'yish."""
    bot.clear_step_handler_by_chat_id(message.chat.id)

    if message.text and message.text.strip().startswith(('/start', '/menu')):
        handle_start(message)
        return

    text = (
        "🚫 <b>Botga to'g'ridan-to'g'ri xabar yozish o'chirilgan!</b>\n\n"
        "Sherik topish, barcha e'lonlarni ko'rish va yangi e'lon berish faqat <b>«📱 Ilova»</b> orqali amalga oshiriladi.\n\n"
        "Iltimos, pastdagi tugmani bosing:"
    )
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton(
            text="📱 Ilovani ochish",
            web_app=types.WebAppInfo(url=MINI_APP_URL)
        )
    )
    bot.send_message(
        chat_id=message.chat.id,
        text=text,
        reply_markup=markup
    )


@bot.message_handler(commands=['help'])
def handle_help(message: types.Message):
    text = (
        "ℹ️ <b>Sherik Bot bo'yicha ko'rsatmalar:</b>\n\n"
        "Barcha xizmatlar, e'lonlar va qidiruv rasmiy <b>«📱 Ilova»</b> orqali amalga oshiriladi.\n\n"
        "Ilovani ochish uchun pastdagi tugmani bosing:"
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
                markup = types.InlineKeyboardMarkup(row_width=1)
                markup.add(
                    types.InlineKeyboardButton("📍 Tuman bo'yicha filter", callback_data="browse_filter_city"),
                    types.InlineKeyboardButton("📋 Birinchi bo'lib e'lon joylash", callback_data="btn_new_listing"),
                    types.InlineKeyboardButton("🏠 Asosiy menyu", callback_data="btn_back_to_menu")
                )
                bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=wait_msg.message_id,
                    text="📭 Hozircha e'lonlar mavjud emas.\nBirinchi bo'lib e'lon joylang!",
                    reply_markup=markup
                )
                return

            bot.delete_message(chat_id, wait_msg.message_id)

            bot.send_message(chat_id, f"📋 <b>Jami {total} ta e'lon mavjud. Eng so'nggilari:</b>")

            for item in results[:5]:
                type_icon = "🏠 Xonam bor" if item.get("listing_type") == "have_room" else "🔍 Xona kerak"
                gender_map = {"male": "👨 Faqat erkaklar", "female": "👩 Faqat ayollar", "any": "🤝 Farqi yo'q"}
                gender_str = gender_map.get(item.get("gender_preference"), "Farqi yo'q")
                city = item.get("city_name") or "O'zbekiston"
                district = item.get("district_name")
                addr = item.get("address_line")
                loc_parts = [city]
                if district:
                    loc_parts.append(district)
                if addr:
                    loc_parts.append(addr)
                loc_str = " • ".join(loc_parts)

                price_str = format_price_display(item.get("price", 0), item.get("currency", "USD"))
                metro_str = f"\n🚇 <b>Metro:</b> {item.get('near_subway')}" if item.get('near_subway') else ""
                unis_list = item.get("nearby_universities", [])
                unis_str = f"\n🎓 <b>OTM:</b> {', '.join(unis_list[:3])}" if unis_list else ""
                amenities_list = item.get("amenities", [])
                amenities_text = f"\n🛋 <b>Jihozlar:</b> {', '.join(amenities_list[:4])}" if amenities_list else ""

                card = (
                    f"<b>{item.get('title')}</b>\n\n"
                    f"📌 <b>Turi:</b> {type_icon}\n"
                    f"📍 <b>Joylashuv:</b> {loc_str}\n"
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
            end_markup = types.InlineKeyboardMarkup(row_width=2)
            end_markup.add(
                types.InlineKeyboardButton("📍 Tuman bo'yicha filter", callback_data="browse_filter_city"),
                types.InlineKeyboardButton("📋 E'lon joylash", callback_data="btn_new_listing")
            )
            end_markup.add(
                types.InlineKeyboardButton("📱 Ilovada ko'proq ko'rish", web_app=types.WebAppInfo(url=MINI_APP_URL)),
                types.InlineKeyboardButton("🏠 Asosiy menyu", callback_data="btn_back_to_menu")
            )
            bot.send_message(chat_id, "Qidiruvni davom ettirish yoki ilovada to'liq ko'rish:", reply_markup=end_markup)

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


@bot.callback_query_handler(func=lambda call: call.data == "browse_filter_city")
def handle_browse_filter_city(call: types.CallbackQuery):
    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = [types.InlineKeyboardButton(name, callback_data=f"bfilt_city_{cid}") for cid, name in CITIES]
    markup.add(*buttons)
    markup.add(types.InlineKeyboardButton("⬅️ E'lonlarga qaytish", callback_data="btn_browse_listings"))

    text = "📍 <b>Qaysi shahardan e'lon qidiryapsiz?</b>"
    try:
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=text, reply_markup=markup)
    except Exception:
        bot.send_message(call.message.chat.id, text, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("bfilt_city_"))
def handle_browse_filter_district(call: types.CallbackQuery):
    cid = int(call.data.replace("bfilt_city_", ""))
    city_name = dict(CITIES).get(cid, "Toshkent")
    districts = CITY_DISTRICTS.get(cid, [])

    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = [types.InlineKeyboardButton(name, callback_data=f"bfilt_dist_{cid}_{did}") for did, name in districts]
    markup.add(*buttons)
    markup.add(
        types.InlineKeyboardButton(f"🏙 {city_name} barcha e'lonlari", callback_data=f"bfilt_all_{cid}"),
        types.InlineKeyboardButton("⬅️ Shaharlarga qaytish", callback_data="browse_filter_city")
    )

    text = f"📍 <b>{city_name} — Qaysi tumandan sherik / kvartira qidiryapsiz?</b>"
    try:
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=text, reply_markup=markup)
    except Exception:
        bot.send_message(call.message.chat.id, text, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("bfilt_dist_") or call.data.startswith("bfilt_all_"))
def handle_browse_district_results(call: types.CallbackQuery):
    chat_id = call.message.chat.id

    if call.data.startswith("bfilt_all_"):
        cid = int(call.data.replace("bfilt_all_", ""))
        did = None
        city_name = dict(CITIES).get(cid, "Toshkent")
        district_name = None
        params = {"city": cid}
        heading = f"🏙 <b>{city_name}</b> bo'yicha e'lonlar:"
    else:
        parts = call.data.replace("bfilt_dist_", "").split("_")
        cid = int(parts[0])
        did = int(parts[1])
        city_name = dict(CITIES).get(cid, "Toshkent")
        districts_map = dict(CITY_DISTRICTS.get(cid, []))
        district_name = districts_map.get(did, "Tuman")
        params = {"city": cid, "district": did}
        heading = f"📍 <b>{city_name}, {district_name} tumani</b> bo'yicha e'lonlar:"

    wait_msg = bot.send_message(chat_id, "🔍 E'lonlar qidirilmoqda...")
    try:
        resp = requests.get(f"{API_BASE_URL}/listings/", params=params, timeout=15)
        safe_delete_message(chat_id, wait_msg.message_id)

        if resp.status_code == 200:
            data = resp.json()
            results = data.get("results", [])
            total = data.get("count", 0)

            if not results:
                markup = types.InlineKeyboardMarkup(row_width=1)
                markup.add(
                    types.InlineKeyboardButton("📍 Boshqa tuman tanlash", callback_data=f"bfilt_city_{cid}"),
                    types.InlineKeyboardButton("📋 Bu tumanga e'lon joylash", callback_data="btn_new_listing"),
                    types.InlineKeyboardButton("🏠 Barcha e'lonlar", callback_data="btn_browse_listings")
                )
                bot.send_message(
                    chat_id=chat_id,
                    text=f"📭 <b>{district_name or city_name}</b> bo'yicha hozircha e'lonlar topilmadi.\n\nBirinchi bo'lib e'lon joylashingiz yoki boshqa hududni tanlashingiz mumkin:",
                    reply_markup=markup
                )
                return

            bot.send_message(chat_id, f"{heading}\n(Jami {total} ta e'lon topildi)")

            for item in results[:5]:
                type_icon = "🏠 Xonam bor" if item.get("listing_type") == "have_room" else "🔍 Xona kerak"
                gender_map = {"male": "👨 Faqat erkaklar", "female": "👩 Faqat ayollar", "any": "🤝 Farqi yo'q"}
                gender_str = gender_map.get(item.get("gender_preference"), "Farqi yo'q")
                city = item.get("city_name") or city_name
                district = item.get("district_name") or district_name
                addr = item.get("address_line")
                loc_parts = [city]
                if district:
                    loc_parts.append(district)
                if addr:
                    loc_parts.append(addr)
                loc_str = " • ".join(loc_parts)

                price_str = format_price_display(item.get("price", 0), item.get("currency", "USD"))
                metro_str = f"\n🚇 <b>Metro:</b> {item.get('near_subway')}" if item.get('near_subway') else ""
                unis_list = item.get("nearby_universities", [])
                unis_str = f"\n🎓 <b>OTM:</b> {', '.join(unis_list[:3])}" if unis_list else ""
                amenities_list = item.get("amenities", [])
                amenities_text = f"\n🛋 <b>Jihozlar:</b> {', '.join(amenities_list[:4])}" if amenities_list else ""

                card = (
                    f"<b>{item.get('title')}</b>\n\n"
                    f"📌 <b>Turi:</b> {type_icon}\n"
                    f"📍 <b>Joylashuv:</b> {loc_str}\n"
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

            end_markup = types.InlineKeyboardMarkup(row_width=2)
            end_markup.add(
                types.InlineKeyboardButton("📍 Boshqa tuman tanlash", callback_data=f"bfilt_city_{cid}"),
                types.InlineKeyboardButton("🏠 Barcha e'lonlar", callback_data="btn_browse_listings")
            )
            bot.send_message(chat_id, "Boshqa hududlarni qidirish:", reply_markup=end_markup)

        else:
            bot.send_message(chat_id, "❌ E'lonlarni yuklashda xatolik yuz berdi.", reply_markup=get_main_menu_keyboard())
    except Exception as e:
        safe_delete_message(chat_id, wait_msg.message_id)
        bot.send_message(chat_id, f"❌ Xatolik: {e}", reply_markup=get_main_menu_keyboard())


# ==================== E'LON JOYLASH (WIZARD) ====================

def init_user_draft(user):
    user_id = user.id
    user_drafts[user_id] = {
        "telegram_id": user_id,
        "first_name": user.first_name or "",
        "last_name": user.last_name or "",
        "username": user.username or "",
        "city_id": 1,
        "city_name": "Toshkent",
        "district_id": None,
        "district_name": "",
        "address_line": "",
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
    user_drafts[user_id]["district_id"] = None
    user_drafts[user_id]["district_name"] = ""
    user_drafts[user_id]["address_line"] = ""

    render_step_2b_district(call.message.chat.id, city_id=city_id, city_name=city_name, message_id=call.message.message_id)


def render_step_2b_district(chat_id, city_id, city_name, message_id=None):
    bot.clear_step_handler_by_chat_id(chat_id)
    districts = CITY_DISTRICTS.get(city_id, [])
    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = [types.InlineKeyboardButton(name, callback_data=f"wiz_dist_{did}") for did, name in districts]
    markup.add(*buttons)
    markup.row(types.InlineKeyboardButton("⏭️ Tumanni ko'rsatmaslik", callback_data="wiz_dist_skip"))
    markup.row(
        types.InlineKeyboardButton("⬅️ Shaharga qaytish", callback_data="wiz_back_to_city"),
        types.InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel_action")
    )

    text = (
        f"📍 <b>2B-bosqich:</b> Tumanni tanlang ({city_name}):\n\n"
        f"<i>Kvartira yoki sherik qidirilayotgan tumanni tanlang:</i>"
    )
    if message_id:
        try:
            bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=text, reply_markup=markup)
            return
        except Exception:
            pass
    bot.send_message(chat_id=chat_id, text=text, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("wiz_dist_"))
def handle_district_selection(call: types.CallbackQuery):
    user_id = call.from_user.id
    if user_id not in user_drafts:
        init_user_draft(call.from_user)

    data = call.data.replace("wiz_dist_", "")
    city_id = user_drafts[user_id].get("city_id", 1)
    districts_map = dict(CITY_DISTRICTS.get(city_id, []))

    if data == "skip":
        user_drafts[user_id]["district_id"] = None
        user_drafts[user_id]["district_name"] = ""
    else:
        try:
            did = int(data)
            user_drafts[user_id]["district_id"] = did
            user_drafts[user_id]["district_name"] = districts_map.get(did, "")
        except ValueError:
            user_drafts[user_id]["district_id"] = None
            user_drafts[user_id]["district_name"] = ""

    render_step_2c_address(call.message.chat.id, user_id=user_id)


def render_step_2c_address(chat_id, user_id=None):
    bot.clear_step_handler_by_chat_id(chat_id)
    uid = user_id or chat_id
    draft = user_drafts.get(uid, {})
    city_name = draft.get("city_name") or "Toshkent"
    district_name = draft.get("district_name") or ""
    loc_header = f"{city_name}, {district_name}" if district_name else city_name

    loc_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    loc_markup.add(types.KeyboardButton("📍 Lokatsiyamni yuborish (GPS)", request_location=True))
    loc_markup.add(types.KeyboardButton("⏭️ O'tkazib yuborish"), types.KeyboardButton("⬅️ Orqaga"))

    text = (
        f"📍 <b>2C-bosqich:</b> Aniq manzil yoki lokatsiya ({loc_header}):\n\n"
        f"<i>Kvartiraning aniq manzilini yozing (masalan: Chilonzor 9-mavze, 12-uy, mo'ljal: Rayhon) "
        f"yoki pastdagi <b>«📍 Lokatsiyamni yuborish (GPS)»</b> tugmasini bosing:</i>\n\n"
        f"<i>Agar aniq manzilni ko'rsatishni istamasangiz, <b>«⏭️ O'tkazib yuborish»</b> tugmasini bosing.</i>"
    )
    msg = bot.send_message(chat_id, text, reply_markup=loc_markup)
    bot.register_next_step_handler(msg, process_address_step)


def process_address_step(message: types.Message):
    user_id = message.from_user.id
    if user_id not in user_drafts:
        bot.send_message(message.chat.id, "Boshidan boshlang: /new", reply_markup=get_main_menu_keyboard())
        return

    draft = user_drafts[user_id]
    city_id = draft.get("city_id", 1)
    city_name = draft.get("city_name") or dict(CITIES).get(city_id, "Toshkent")

    if message.location:
        lat = message.location.latitude
        lon = message.location.longitude
        addr_line = f"GPS: {lat:.5f}, {lon:.5f}"
        try:
            resp = requests.get(
                f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}&zoom=18&addressdetails=1",
                headers={"User-Agent": "SherikBot/1.0"},
                timeout=5
            )
            if resp.status_code == 200:
                geo_data = resp.json()
                road = geo_data.get("address", {}).get("road")
                suburb = geo_data.get("address", {}).get("suburb") or geo_data.get("address", {}).get("residential")
                if road and suburb:
                    addr_line = f"{suburb}, {road}"
                elif geo_data.get("display_name"):
                    addr_line = ", ".join(geo_data["display_name"].split(",")[:2]).strip()
        except Exception:
            pass

        draft["address_line"] = addr_line
        bot.send_message(message.chat.id, f"✅ Lokatsiya qabul qilindi: <b>{addr_line}</b>", reply_markup=types.ReplyKeyboardRemove())
        render_step_3_title(message.chat.id, user_id=user_id)
        return

    text = (message.text or "").strip()
    if text in ["⬅️ Orqaga", "/back"]:
        bot.send_message(message.chat.id, "Orqaga qaytildi.", reply_markup=types.ReplyKeyboardRemove())
        render_step_2b_district(message.chat.id, city_id=city_id, city_name=city_name)
        return

    if text in ["❌ Bekor qilish", "/cancel"]:
        bot.send_message(message.chat.id, "Bekor qilindi.", reply_markup=types.ReplyKeyboardRemove())
        handle_cancel_msg(message)
        return

    if text in ["⏭️ O'tkazib yuborish", "/skip"]:
        draft["address_line"] = ""
        bot.send_message(message.chat.id, "Manzil o'tkazib yuborildi.", reply_markup=types.ReplyKeyboardRemove())
        render_step_3_title(message.chat.id, user_id=user_id)
        return

    if len(text) < 3:
        msg = bot.send_message(
            message.chat.id,
            "❌ Manzil juda qisqa. Kamida 3 ta belgi yozing yoki «⏭️ O'tkazib yuborish» tugmasini bosing:"
        )
        bot.register_next_step_handler(msg, process_address_step)
        return

    draft["address_line"] = text
    bot.send_message(message.chat.id, f"✅ Manzil qabul qilindi: <b>{text}</b>", reply_markup=types.ReplyKeyboardRemove())
    render_step_3_title(message.chat.id, user_id=user_id)


def render_step_3_title(chat_id, user_id=None, city_name=None):
    bot.clear_step_handler_by_chat_id(chat_id)
    uid = user_id or chat_id
    draft = user_drafts.get(uid, {})
    c_name = draft.get("city_name") or city_name or "Toshkent"
    d_name = draft.get("district_name") or ""
    loc_header = f"{c_name}, {d_name}" if d_name else c_name
    addr = draft.get("address_line")
    if addr:
        loc_header += f" ({addr})"

    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("⬅️ Orqaga", callback_data="wiz_back_to_address"),
        types.InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel_action")
    )

    msg = bot.send_message(
        chat_id,
        f"📍 Joylashuv: <b>{loc_header}</b>\n\n"
        f"✏️ <b>3-bosqich:</b> E'lon sarlavhasini yozing:\n"
        f"<i>(Masalan: Chilonzorda 2 xonali kvartiraga 1 nafar sherik kerak)</i>",
        reply_markup=markup
    )
    bot.register_next_step_handler(msg, process_title_step)


@bot.callback_query_handler(func=lambda call: call.data == "wiz_back_to_address")
def handle_back_to_address(call: types.CallbackQuery):
    bot.clear_step_handler_by_chat_id(call.message.chat.id)
    render_step_2c_address(call.message.chat.id, user_id=call.from_user.id)


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
        render_step_2c_address(message.chat.id, user_id=user_id)
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
    render_step_3_title(call.message.chat.id, user_id=call.from_user.id)


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
    district_name = draft.get("district_name") or ""
    address_line = draft.get("address_line") or ""

    loc_parts = [city_name]
    if district_name:
        loc_parts.append(district_name)
    if address_line:
        loc_parts.append(address_line)
    loc_disp = " • ".join(loc_parts)

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
        f"📍 <b>Joylashuv:</b> {loc_disp}\n"
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
            "district_id": draft.get("district_id"),
            "address_line": draft.get("address_line", ""),
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

        loc_parts = [draft.get("city_name") or "Toshkent"]
        if draft.get("district_name"):
            loc_parts.append(draft["district_name"])
        if draft.get("address_line"):
            loc_parts.append(draft["address_line"])
        loc_disp = " • ".join(loc_parts)

        price_disp = format_price_display(listing_payload["price"], listing_payload["currency"])
        amenities_disp = ", ".join(listing_payload["amenities"]) if listing_payload["amenities"] else "Yo'q"
        metro_disp = listing_payload["near_subway"] if listing_payload["near_subway"] else "Yo'q"
        unis_disp = ", ".join(listing_payload["nearby_universities"]) if listing_payload["nearby_universities"] else "Yo'q"

        success_text = (
            f"🎉 <b>E'loningiz muvaffaqiyatli saqlandi!</b>\n\n"
            f"📋 <b>E'lon raqami:</b> #{listing_id}\n"
            f"📍 <b>Joylashuv:</b> {loc_disp}\n"
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
            district_name = l.get("district_name")
            addr_line = l.get("address_line")
            loc_parts = [city_name]
            if district_name:
                loc_parts.append(district_name)
            if addr_line:
                loc_parts.append(addr_line)
            loc_disp = " • ".join(loc_parts)

            metro_line = f"\n🚇 <b>Metro:</b> {l.get('near_subway')}" if l.get('near_subway') else ""
            unis = l.get("nearby_universities", [])
            unis_line = f"\n🎓 <b>OTM:</b> {', '.join(unis)}" if unis else ""
            cap = l.get("capacity", 1)
            tot = l.get("total_residents", 2)
            rej_line = f"\n⚠️ <b>Rad etish sababi:</b> {l.get('rejection_reason')}" if l.get('rejection_reason') else ""

            card_text = (
                f"<b>{l.get('title')}</b>\n\n"
                f"📌 <b>Turi:</b> {type_icon}\n"
                f"📍 <b>Joylashuv:</b> {loc_disp}\n"
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
    try:
        bot.delete_webhook(drop_pending_updates=True)
    except Exception as _e:
        print(f"Webhook tozalashda ogohlantirish: {_e}")
    bot.infinity_polling(skip_pending=True)

