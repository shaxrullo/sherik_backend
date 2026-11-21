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
from telebot import types

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "9272714946:AAGViuu8BOATFYuMXHAgFn8fjsiMABRC2g0")
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


threading.Thread(target=_keep_alive_loop, daemon=True).start()



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


@bot.message_handler(commands=['start', 'menu'])
def handle_start(message: types.Message):
    user_name = message.from_user.first_name or "Foydalanuvchi"
    text = (
        f"Assalomu alaykum, <b>{user_name}</b>! 👋\n\n"
        f"<b>Sherik Topish</b> rasmiy botiga xush kelibsiz.\n"
        f"Bu yerda siz o'zingizga mos xona yoki ijarada birga turish uchun ishonchli sherik topishingiz mumkin.\n\n"
        f"Pastdagi tugmalar orqali kerakli bo'limni tanlang:"
    )
    bot.send_message(
        chat_id=message.chat.id,
        text=text,
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
                amenities_list = item.get("amenities", [])
                amenities_text = f"\n🛋 <b>Jihozlar:</b> {', '.join(amenities_list[:4])}" if amenities_list else ""

                card = (
                    f"<b>{item.get('title')}</b>\n\n"
                    f"📌 <b>Turi:</b> {type_icon}\n"
                    f"📍 <b>Shahar:</b> {city}\n"
                    f"💰 <b>Narxi:</b> {price_str}\n"
                    f"👥 <b>Kimga:</b> {gender_str}{amenities_text}\n\n"
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
        "amenities": [],
        "currency": "USD",
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
        price = float(cleaned)
        if price <= 0:
            raise ValueError
    except ValueError:
        curr = user_drafts[user_id].get("currency", "USD")
        hint = "50 yoki 100" if curr == "USD" else "1500000"
        msg = bot.send_message(message.chat.id, f"❌ Noto'g'ri narx. Iltimos, faqat musbat son yozing (masalan: {hint}):")
        bot.register_next_step_handler(msg, process_price_step)
        return

    user_drafts[user_id]["price"] = price
    render_step_6_gender(message.chat.id)


def render_step_6_gender(chat_id, message_id=None):
    bot.clear_step_handler_by_chat_id(chat_id)
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("👨 Faqat erkaklar / yigitlar", callback_data="wiz_gender_male"),
        types.InlineKeyboardButton("👩 Faqat ayollar / qizlar", callback_data="wiz_gender_female"),
        types.InlineKeyboardButton("🤝 Farqi yo'q", callback_data="wiz_gender_any"),
    )
    markup.row(
        types.InlineKeyboardButton("⬅️ Orqaga", callback_data="wiz_back_to_price"),
        types.InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel_action")
    )

    text = "👥 <b>6-bosqich:</b> Kim uchun afzallik beriladi?"
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

    render_step_7_amenities(call.message.chat.id, user_id=user_id, message_id=call.message.message_id)


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
        types.InlineKeyboardButton("⬅️ Orqaga", callback_data="wiz_back_to_gender"),
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


@bot.callback_query_handler(func=lambda call: call.data.startswith("wiz_am_"))
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


@bot.callback_query_handler(func=lambda call: call.data == "wiz_back_to_gender")
def handle_back_to_gender(call: types.CallbackQuery):
    bot.clear_step_handler_by_chat_id(call.message.chat.id)
    render_step_6_gender(call.message.chat.id, message_id=call.message.message_id)


@bot.callback_query_handler(func=lambda call: call.data == "wiz_amenities_done")
def handle_amenities_done(call: types.CallbackQuery):
    render_step_8_photo(call.message.chat.id, message_id=call.message.message_id)


# ==================== 8-BOSQICH: RASM ====================

def render_step_8_photo(chat_id, message_id=None):
    bot.clear_step_handler_by_chat_id(chat_id)
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("⏭️ Rasmsiz davom etish", callback_data="wiz_skip_photo"))
    markup.row(
        types.InlineKeyboardButton("⬅️ Orqaga", callback_data="wiz_back_to_amenities"),
        types.InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel_action")
    )

    text = (
        "📸 <b>8-bosqich:</b> Xona rasmini yuboring (ixtiyoriy):\n"
        "<i>Rasm bo'lmasa, pastdagi 'Rasmsiz davom etish' tugmasini bosing:</i>"
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
        render_step_7_amenities(message.chat.id, user_id=user_id)
        return
    if text in ["❌ Bekor qilish", "/cancel"]:
        handle_cancel_msg(message)
        return

    if message.content_type == 'photo':
        photo = message.photo[-1]
        user_drafts[user_id]["photo_file_id"] = photo.file_id
        bot.send_message(message.chat.id, "✅ Rasm qabul qilindi!")
    else:
        user_drafts[user_id]["photo_file_id"] = None

    render_step_9_phone(message.chat.id)


@bot.callback_query_handler(func=lambda call: call.data == "wiz_skip_photo")
def handle_skip_photo(call: types.CallbackQuery):
    bot.clear_step_handler_by_chat_id(call.message.chat.id)
    user_id = call.from_user.id
    if user_id in user_drafts:
        user_drafts[user_id]["photo_file_id"] = None
    render_step_9_phone(call.message.chat.id)


# ==================== 9-BOSQICH: TELEFON VA SAQLASH ====================

def render_step_9_phone(chat_id):
    bot.clear_step_handler_by_chat_id(chat_id)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(types.KeyboardButton("📱 Telefon raqamimni ulashish", request_contact=True))
    markup.row(types.KeyboardButton("⬅️ Orqaga"), types.KeyboardButton("❌ Bekor qilish"))

    msg = bot.send_message(
        chat_id,
        "📞 <b>9-bosqich:</b> Bog'lanish uchun telefon raqamingizni yuboring:\n"
        "<i>Pastdagi tugmani bosing yoki raqamingizni yozing (+998901234567):</i>",
        reply_markup=markup
    )
    bot.register_next_step_handler(msg, process_phone_and_finish)


def process_phone_and_finish(message: types.Message):
    user_id = message.from_user.id
    if user_id not in user_drafts:
        bot.send_message(message.chat.id, "Sessiya tugadi. Qaytadan boshlang: /new", reply_markup=types.ReplyKeyboardRemove())
        return

    text = (message.text or "").strip()
    if text in ["⬅️ Orqaga", "/back"]:
        bot.send_message(message.chat.id, "Orqaga qaytildi.", reply_markup=types.ReplyKeyboardRemove())
        render_step_8_photo(message.chat.id)
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

    user_drafts[user_id]["phone_number"] = phone

    # Reply keyboardni tozalaymiz
    wait_msg = bot.send_message(
        message.chat.id,
        "⏳ E'lon saqlanmoqda, kuting...",
        reply_markup=types.ReplyKeyboardRemove()
    )

    draft = user_drafts[user_id]

    try:
        # 1. Telegram user orqali backend'dan JWT token olish
        auth_data = {
            "telegram_id": draft.get("telegram_id", user_id),
            "first_name": draft.get("first_name", message.from_user.first_name or "Telegram User"),
            "last_name": draft.get("last_name", message.from_user.last_name or ""),
            "username": draft.get("username", message.from_user.username or ""),
            "phone_number": phone
        }
        auth_resp = requests.post(f"{API_BASE_URL}/auth/telegram/", json=auth_data, timeout=15)

        if auth_resp.status_code != 200:
            safe_delete_message(message.chat.id, wait_msg.message_id)
            bot.send_message(
                chat_id=message.chat.id,
                text=f"❌ Autentifikatsiya xatosi: {auth_resp.text}",
                reply_markup=get_main_menu_keyboard()
            )
            return

        token = auth_resp.json().get("access")
        headers = {"Authorization": f"Bearer {token}"}

        # 2. E'lonni yaratish (amenities va currency bilan)
        listing_payload = {
            "title": draft.get("title", "Sherik kerak"),
            "description": draft.get("description", "Kvartiraga sherik kerak"),
            "listing_type": draft.get("listing_type", "have_room"),
            "city_id": draft.get("city_id", 1),
            "price": draft.get("price", 100),
            "currency": draft.get("currency", "USD"),
            "gender_preference": draft.get("gender_preference", "any"),
            "amenities": draft.get("amenities", []),
        }

        create_resp = requests.post(f"{API_BASE_URL}/listings/", json=listing_payload, headers=headers, timeout=15)

        if create_resp.status_code not in [200, 201]:
            safe_delete_message(message.chat.id, wait_msg.message_id)
            bot.send_message(
                chat_id=message.chat.id,
                text=f"❌ E'lon yaratishda xato: {create_resp.text}",
                reply_markup=get_main_menu_keyboard()
            )
            return

        listing_id = create_resp.json().get("id")

        # 3. Rasm bo'lsa yuklaymiz
        photo_id = draft.get("photo_file_id")
        if photo_id and listing_id:
            try:
                file_info = bot.get_file(photo_id)
                downloaded_file = bot.download_file(file_info.file_path)

                files = {
                    "image": ("photo.jpg", io.BytesIO(downloaded_file), "image/jpeg")
                }
                data = {"is_main": "true"}
                requests.post(
                    f"{API_BASE_URL}/listings/{listing_id}/photos/",
                    headers=headers,
                    files=files,
                    data=data,
                    timeout=30
                )
            except Exception as pe:
                print(f"Rasm yuklash xatosi: {pe}")

        # Tugatish
        del user_drafts[user_id]

        price_disp = format_price_display(listing_payload["price"], listing_payload["currency"])
        amenities_disp = ", ".join(listing_payload["amenities"]) if listing_payload["amenities"] else "Yo'q"

        success_text = (
            f"🎉 <b>E'loningiz muvaffaqiyatli qabul qilindi!</b>\n\n"
            f"📋 <b>E'lon raqami:</b> #{listing_id}\n"
            f"💰 <b>Narx:</b> {price_disp}\n"
            f"🛋 <b>Jihozlar:</b> {amenities_disp}\n"
            f"📌 <b>Holat:</b> ⏳ Moderatsiyada (kutilmoqda)\n\n"
            f"<i>Adminlarimiz tekshirib tasdiqlagach, e'lon ilovada va botda hamma uchun ko'rinadi!</i>"
        )

        fin_markup = types.InlineKeyboardMarkup()
        fin_markup.add(types.InlineKeyboardButton(
            text="📱 Ilovada ko'rish",
            web_app=types.WebAppInfo(url=f"{MINI_APP_URL}/listings/{listing_id}")
        ))
        fin_markup.add(types.InlineKeyboardButton(text="🏠 Bosh menyu", callback_data="btn_back_to_menu"))

        safe_delete_message(message.chat.id, wait_msg.message_id)
        bot.send_message(
            chat_id=message.chat.id,
            text=success_text,
            reply_markup=fin_markup
        )

    except Exception as e:
        safe_delete_message(message.chat.id, wait_msg.message_id)
        bot.send_message(
            chat_id=message.chat.id,
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
    wait_msg = bot.send_message(call.message.chat.id, "Yuklanmoqda...")

    try:
        auth_data = {
            "telegram_id": user_id,
            "first_name": call.from_user.first_name or "",
            "username": call.from_user.username or "",
        }
        auth_resp = requests.post(f"{API_BASE_URL}/auth/telegram/", json=auth_data, timeout=15)
        if auth_resp.status_code == 200:
            token = auth_resp.json().get("access")
            headers = {"Authorization": f"Bearer {token}"}
            my_resp = requests.get(f"{API_BASE_URL}/listings/my/", headers=headers, timeout=15)
            if my_resp.status_code == 200:
                results = my_resp.json().get("results", [])
                if not results:
                    bot.edit_message_text(
                        chat_id=call.message.chat.id,
                        message_id=wait_msg.message_id,
                        text="📭 Siz hali e'lon joylashtirmagansiz.\n\nE'lon joylash uchun /new buyrug'ini bosing.",
                        reply_markup=get_main_menu_keyboard()
                    )
                    return

                text = f"👤 <b>Sizning e'lonlaringiz ({len(results)} ta):</b>\n\n"
                status_map = {"pending": "⏳ Moderatsiyada", "approved": "✅ Tasdiqlangan", "rejected": "❌ Rad etilgan"}
                for l in results:
                    price_display = format_price_display(l.get('price', 0), l.get('currency', 'USD'))
                    text += (
                        f"• <b>{l.get('title')}</b>\n"
                        f"   Holat: {status_map.get(l.get('moderation_status'), l.get('moderation_status'))}\n"
                        f"   Narx: {price_display} | ID: #{l.get('id')}\n\n"
                    )
                bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=wait_msg.message_id,
                    text=text,
                    reply_markup=get_main_menu_keyboard()
                )
                return
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=wait_msg.message_id,
            text="❌ Ma'lumotlarni olishda xatolik yuz berdi.",
            reply_markup=get_main_menu_keyboard()
        )
    except Exception as e:
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=wait_msg.message_id,
            text=f"Xatolik: {e}",
            reply_markup=get_main_menu_keyboard()
        )


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
    print("🤖 @SheriktopishBot ishga tushmoqda...")
    bot.infinity_polling(skip_pending=True)

