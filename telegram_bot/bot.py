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

                card = (
                    f"<b>{item.get('title')}</b>\n\n"
                    f"📌 <b>Turi:</b> {type_icon}\n"
                    f"📍 <b>Shahar:</b> {city}\n"
                    f"💰 <b>Narxi:</b> ${item.get('price')}\n"
                    f"👥 <b>Kimga:</b> {gender_str}\n\n"
                    f"<i>ID: #{item.get('id')}</i>"
                )

                item_markup = types.InlineKeyboardMarkup()
                item_markup.add(types.InlineKeyboardButton(
                    text="🌐 Saytda ko'rish",
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
            bot.send_message(chat_id, "Ko'proq e'lonlarni saytda ko'rishingiz mumkin:", reply_markup=get_main_menu_keyboard())

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

@bot.callback_query_handler(func=lambda call: call.data == "btn_new_listing")
@bot.message_handler(commands=['new'])
def start_new_listing(update):
    chat_id = update.message.chat.id if isinstance(update, types.CallbackQuery) else update.chat.id
    user_id = update.from_user.id if isinstance(update, types.CallbackQuery) else update.from_user.id

    user_drafts[user_id] = {
        "telegram_id": user_id,
        "first_name": update.from_user.first_name or "",
        "last_name": update.from_user.last_name or "",
        "username": update.from_user.username or "",
    }

    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🏠 Xonam bor (Sherik kerak)", callback_data="type_have_room"),
        types.InlineKeyboardButton("🔍 Xona kerak (Ijara qidiryapman)", callback_data="type_need_room"),
        types.InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel_action")
    )

    text = "📋 <b>E'lon joylash — 1-bosqich:</b>\n\nQanday e'lon bermoqchisiz?"
    if isinstance(update, types.CallbackQuery):
        bot.edit_message_text(chat_id=chat_id, message_id=update.message.message_id, text=text, reply_markup=markup)
    else:
        bot.send_message(chat_id=chat_id, text=text, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data in ["type_have_room", "type_need_room"])
def handle_listing_type(call: types.CallbackQuery):
    user_id = call.from_user.id
    if user_id not in user_drafts:
        user_drafts[user_id] = {}

    listing_type = "have_room" if call.data == "type_have_room" else "need_room"
    user_drafts[user_id]["listing_type"] = listing_type

    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = [types.InlineKeyboardButton(name, callback_data=f"city_{cid}") for cid, name in CITIES]
    markup.add(*buttons)
    markup.add(types.InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel_action"))

    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="📍 <b>2-bosqich:</b> Shaharni tanlang:",
        reply_markup=markup
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith("city_"))
def handle_city_selection(call: types.CallbackQuery):
    user_id = call.from_user.id
    city_id = int(call.data.replace("city_", ""))
    city_name = dict(CITIES).get(city_id, "Toshkent")

    user_drafts[user_id]["city_id"] = city_id
    user_drafts[user_id]["city_name"] = city_name

    msg = bot.send_message(
        call.message.chat.id,
        f"✅ Tanlangan shahar: <b>{city_name}</b>\n\n"
        f"✏️ <b>3-bosqich:</b> E'lon sarlavhasini yozing:\n"
        f"<i>(Masalan: Chilonzorda 2 xonali kvartiraga 1 nafar sherik kerak)</i>"
    )
    bot.register_next_step_handler(msg, process_title_step)


def process_title_step(message: types.Message):
    user_id = message.from_user.id
    if user_id not in user_drafts:
        bot.send_message(message.chat.id, "Boshidan boshlang: /new", reply_markup=get_main_menu_keyboard())
        return

    title = message.text.strip()
    if len(title) < 5:
        msg = bot.send_message(message.chat.id, "❌ Sarlavha juda qisqa. Kamida 5 ta belgi yozing:")
        bot.register_next_step_handler(msg, process_title_step)
        return

    user_drafts[user_id]["title"] = title

    msg = bot.send_message(
        message.chat.id,
        "📝 <b>4-bosqich:</b> E'lon tavsifini yozing:\n"
        "<i>(Qavat, sharoitlar, yaqin metro/mo'ljal, kimlar yashaydi va h.k.)</i>"
    )
    bot.register_next_step_handler(msg, process_description_step)


def process_description_step(message: types.Message):
    user_id = message.from_user.id
    if user_id not in user_drafts:
        bot.send_message(message.chat.id, "Boshidan boshlang: /new", reply_markup=get_main_menu_keyboard())
        return

    desc = message.text.strip()
    if len(desc) < 10:
        msg = bot.send_message(message.chat.id, "❌ Tavsif juda qisqa. Kamida 10 ta belgi yozing:")
        bot.register_next_step_handler(msg, process_description_step)
        return

    user_drafts[user_id]["description"] = desc

    msg = bot.send_message(
        message.chat.id,
        "💰 <b>5-bosqich:</b> Narxni kiriting (USD da):\n"
        "<i>(Faqat raqam yozing, masalan: 50 yoki 150)</i>"
    )
    bot.register_next_step_handler(msg, process_price_step)


def process_price_step(message: types.Message):
    user_id = message.from_user.id
    text = message.text.strip().replace("$", "").replace(" ", "")

    try:
        price = float(text)
        if price <= 0:
            raise ValueError
    except ValueError:
        msg = bot.send_message(message.chat.id, "❌ Noto'g'ri narx. Iltimos, musbat son yozing (masalan: 70):")
        bot.register_next_step_handler(msg, process_price_step)
        return

    user_drafts[user_id]["price"] = price

    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("👨 Faqat erkaklar / yigitlar", callback_data="gender_male"),
        types.InlineKeyboardButton("👩 Faqat ayollar / qizlar", callback_data="gender_female"),
        types.InlineKeyboardButton("🤝 Farqi yo'q", callback_data="gender_any"),
    )

    bot.send_message(
        message.chat.id,
        "👥 <b>6-bosqich:</b> Kim uchun afzallik beriladi?",
        reply_markup=markup
    )


@bot.callback_query_handler(func=lambda call: call.data in ["gender_male", "gender_female", "gender_any"])
def handle_gender_step(call: types.CallbackQuery):
    user_id = call.from_user.id
    gender_map = {"gender_male": "male", "gender_female": "female", "gender_any": "any"}
    user_drafts[user_id]["gender_preference"] = gender_map[call.data]

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("⏭️ Rasmsiz davom etish", callback_data="skip_photo"))

    bot.send_message(
        call.message.chat.id,
        "📸 <b>7-bosqich:</b> Xona rasmini yuboring (ixtiyoriy):\n"
        "<i>Yoki pastdagi tugmani bosing:</i>",
        reply_markup=markup
    )
    bot.register_next_step_handler_by_chat_id(call.message.chat.id, process_photo_step)


def process_photo_step(message: types.Message):
    user_id = message.from_user.id
    if user_id not in user_drafts:
        return

    if message.content_type == 'photo':
        photo = message.photo[-1]
        user_drafts[user_id]["photo_file_id"] = photo.file_id
        bot.send_message(message.chat.id, "✅ Rasm qabul qilindi!")
    else:
        user_drafts[user_id]["photo_file_id"] = None

    ask_phone_step(message.chat.id)


@bot.callback_query_handler(func=lambda call: call.data == "skip_photo")
def handle_skip_photo(call: types.CallbackQuery):
    user_id = call.from_user.id
    if user_id in user_drafts:
        user_drafts[user_id]["photo_file_id"] = None
    ask_phone_step(call.message.chat.id)


def ask_phone_step(chat_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(types.KeyboardButton("📱 Telefon raqamimni ulashish", request_contact=True))

    msg = bot.send_message(
        chat_id,
        "📞 <b>8-bosqich:</b> Bog'lanish uchun telefon raqamingizni yuboring:\n"
        "<i>Pastdagi tugmani bosing yoki raqamingizni yozing (+998901234567):</i>",
        reply_markup=markup
    )
    bot.register_next_step_handler(msg, process_phone_and_finish)


def process_phone_and_finish(message: types.Message):
    user_id = message.from_user.id
    if user_id not in user_drafts:
        bot.send_message(message.chat.id, "Sessiya tugadi. Qaytadan boshlang: /new", reply_markup=types.ReplyKeyboardRemove())
        return

    phone = ""
    if message.contact:
        phone = message.contact.phone_number
        if not phone.startswith("+"):
            phone = "+" + phone
    elif message.text:
        phone = message.text.strip()

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
            "telegram_id": draft["telegram_id"],
            "first_name": draft.get("first_name", "Telegram User"),
            "last_name": draft.get("last_name", ""),
            "username": draft.get("username", ""),
            "phone_number": phone
        }
        auth_resp = requests.post(f"{API_BASE_URL}/auth/telegram/", json=auth_data, timeout=15)

        if auth_resp.status_code != 200:
            bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=wait_msg.message_id,
                text=f"❌ Autentifikatsiya xatosi: {auth_resp.text}",
                reply_markup=get_main_menu_keyboard()
            )
            return

        token = auth_resp.json().get("access")
        headers = {"Authorization": f"Bearer {token}"}

        # 2. E'lonni yaratish
        listing_payload = {
            "title": draft["title"],
            "description": draft["description"],
            "listing_type": draft["listing_type"],
            "city_id": draft["city_id"],
            "price": draft["price"],
            "gender_preference": draft["gender_preference"],
        }

        create_resp = requests.post(f"{API_BASE_URL}/listings/", json=listing_payload, headers=headers, timeout=15)

        if create_resp.status_code not in [200, 201]:
            bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=wait_msg.message_id,
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

        success_text = (
            f"🎉 <b>E'loningiz muvaffaqiyatli qabul qilindi!</b>\n\n"
            f"📋 <b>E'lon raqami:</b> #{listing_id}\n"
            f"📌 <b>Holat:</b> ⏳ Moderatsiyada (kutilmoqda)\n\n"
            f"<i>Adminlarimiz tekshirib tasdiqlagach, e'lon saytda va botda hamma uchun ko'rinadi!</i>"
        )

        fin_markup = types.InlineKeyboardMarkup()
        fin_markup.add(types.InlineKeyboardButton(
            text="🌐 Saytda ko'rish",
            web_app=types.WebAppInfo(url=f"{MINI_APP_URL}/listings/{listing_id}")
        ))
        fin_markup.add(types.InlineKeyboardButton(text="🏠 Bosh menyu", callback_data="btn_back_to_menu"))

        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=wait_msg.message_id,
            text=success_text,
            reply_markup=fin_markup
        )

    except Exception as e:
        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=wait_msg.message_id,
            text=f"❌ Tizim xatosi yuz berdi: {e}",
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
                    text += (
                        f"• <b>{l.get('title')}</b>\n"
                        f"   Holat: {status_map.get(l.get('moderation_status'), l.get('moderation_status'))}\n"
                        f"   Narx: ${l.get('price')} | ID: #{l.get('id')}\n\n"
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
    if user_id in user_drafts:
        del user_drafts[user_id]
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
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

