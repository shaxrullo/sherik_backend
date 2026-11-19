"""
E'lon joylash handler — Bosqichma-bosqich forma (FSM)
"""
import aiohttp
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from ..api_client import api_post, api_get, api_post_multipart
from ..config import API_BASE_URL

router = Router()

# ─── FSM holatlari ───────────────────────────────────────────────
class ListingForm(StatesGroup):
    email          = State()   # 1. Email (login uchun)
    password       = State()   # 2. Parol
    listing_type   = State()   # 3. E'lon turi
    city           = State()   # 4. Shahar tanlash
    title          = State()   # 5. Sarlavha
    description    = State()   # 6. Tavsif
    price          = State()   # 7. Narx
    gender_pref    = State()   # 8. Jins afzalligi
    photo          = State()   # 9. Rasm (ixtiyoriy)
    confirm        = State()   # 10. Tasdiqlash


# ─── Yordamchi funksiyalar ───────────────────────────────────────
def cancel_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_listing")]
    ])


def skip_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏭️ O'tkazib yuborish", callback_data="skip_photo")],
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_listing")]
    ])


# ─── E'lon joylash boshlash ──────────────────────────────────────
@router.callback_query(F.data == "new_listing")
@router.message(Command("new"))
async def start_listing(update, state: FSMContext):
    msg = update.message if isinstance(update, Message) else update.message
    await state.clear()
    await state.set_state(ListingForm.email)
    text = (
        "📋 <b>Yangi e'lon joylash</b>\n\n"
        "Avval tizimga kirishingiz kerak.\n\n"
        "📧 <b>Emailingizni yozing:</b>\n"
        "<i>(Ro'yxatdan o'tmagan bo'lsangiz, avval saytda ro'yxatdan o'ting)</i>"
    )
    if isinstance(update, CallbackQuery):
        await update.message.edit_text(text, parse_mode="HTML", reply_markup=cancel_keyboard())
        await update.answer()
    else:
        await msg.answer(text, parse_mode="HTML", reply_markup=cancel_keyboard())


# ─── 1. Email ────────────────────────────────────────────────────
@router.message(ListingForm.email)
async def get_email(message: Message, state: FSMContext):
    email = message.text.strip()
    if "@" not in email or "." not in email:
        await message.answer("❌ Email noto'g'ri. Qayta yozing:", reply_markup=cancel_keyboard())
        return
    await state.update_data(email=email)
    await state.set_state(ListingForm.password)
    await message.answer(
        "🔑 <b>Parolingizni yozing:</b>\n"
        "<i>(Xabar yuborilgandan so'ng parol o'chiriladi)</i>",
        parse_mode="HTML", reply_markup=cancel_keyboard()
    )


# ─── 2. Parol → Login ────────────────────────────────────────────
@router.message(ListingForm.password)
async def get_password(message: Message, state: FSMContext):
    password = message.text.strip()
    data = await state.get_data()

    # Parol xabarini o'chirish (xavfsizlik uchun)
    try:
        await message.delete()
    except Exception:
        pass

    # API ga login
    wait_msg = await message.answer("⏳ Tekshirilmoqda...")
    result, status = await api_post("/auth/login/", {"email": data["email"], "password": password})
    await wait_msg.delete()

    if status != 200:
        await message.answer(
            "❌ Email yoki parol noto'g'ri.\nQaytadan email yozing:",
            reply_markup=cancel_keyboard()
        )
        await state.set_state(ListingForm.email)
        return

    token = result.get("access")
    await state.update_data(token=token)
    await state.set_state(ListingForm.listing_type)

    await message.answer(
        "✅ Muvaffaqiyatli kirdingiz!\n\n"
        "🏠 <b>E'lon turini tanlang:</b>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏠 Xonam bor — sherik kerak", callback_data="type_have_room")],
            [InlineKeyboardButton(text="🔍 Xona kerak — ijara qidiryapman", callback_data="type_need_room")],
            [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_listing")],
        ])
    )


# ─── 3. E'lon turi ───────────────────────────────────────────────
@router.callback_query(F.data.in_({"type_have_room", "type_need_room"}))
async def get_listing_type(call: CallbackQuery, state: FSMContext):
    listing_type = "have_room" if call.data == "type_have_room" else "need_room"
    await state.update_data(listing_type=listing_type)

    # Shaharlarni olish
    cities_data, _ = await api_get("/auth/cities/")
    cities = cities_data if isinstance(cities_data, list) else []

    if not cities:
        # Fallback - asosiy shaharlar
        cities = [
            {"id": 1, "name": "Toshkent"}, {"id": 2, "name": "Samarqand"},
            {"id": 3, "name": "Buxoro"}, {"id": 4, "name": "Andijon"},
            {"id": 5, "name": "Namangan"}, {"id": 6, "name": "Farg'ona"},
        ]

    buttons = []
    row = []
    for i, city in enumerate(cities[:12]):  # Max 12 ta
        row.append(InlineKeyboardButton(text=city["name"], callback_data=f"city_{city['id']}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_listing")])

    await state.set_state(ListingForm.city)
    await call.message.edit_text(
        "📍 <b>Shaharni tanlang:</b>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await call.answer()


# ─── 4. Shahar ───────────────────────────────────────────────────
@router.callback_query(F.data.startswith("city_"))
async def get_city(call: CallbackQuery, state: FSMContext):
    city_id = int(call.data.split("_")[1])
    await state.update_data(city_id=city_id)
    await state.set_state(ListingForm.title)
    await call.message.edit_text(
        "✏️ <b>E'lon sarlavhasini yozing:</b>\n\n"
        "<i>Misol: «Chilonzorda 2 xonali kvartira — sherik kerak»</i>\n"
        "<i>(min 10, max 100 belgi)</i>",
        parse_mode="HTML", reply_markup=cancel_keyboard()
    )
    await call.answer()


# ─── 5. Sarlavha ─────────────────────────────────────────────────
@router.message(ListingForm.title)
async def get_title(message: Message, state: FSMContext):
    title = message.text.strip()
    if len(title) < 10:
        await message.answer("❌ Sarlavha kamida 10 ta belgi bo'lishi kerak:", reply_markup=cancel_keyboard())
        return
    if len(title) > 100:
        await message.answer("❌ Sarlavha 100 ta belgidan oshmasin:", reply_markup=cancel_keyboard())
        return
    await state.update_data(title=title)
    await state.set_state(ListingForm.description)
    await message.answer(
        "📝 <b>Tavsif yozing:</b>\n\n"
        "<i>Qavat, xona soni, kommunal to'lovlar, yaqin metro/manzil, qo'shimcha ma'lumotlar</i>\n"
        "<i>(min 20 belgi)</i>",
        parse_mode="HTML", reply_markup=cancel_keyboard()
    )


# ─── 6. Tavsif ───────────────────────────────────────────────────
@router.message(ListingForm.description)
async def get_description(message: Message, state: FSMContext):
    desc = message.text.strip()
    if len(desc) < 20:
        await message.answer("❌ Tavsif kamida 20 ta belgi bo'lishi kerak:", reply_markup=cancel_keyboard())
        return
    await state.update_data(description=desc)
    await state.set_state(ListingForm.price)
    await message.answer(
        "💰 <b>Narxni yozing (USD da):</b>\n\n"
        "<i>Misol: 150</i>",
        parse_mode="HTML", reply_markup=cancel_keyboard()
    )


# ─── 7. Narx ─────────────────────────────────────────────────────
@router.message(ListingForm.price)
async def get_price(message: Message, state: FSMContext):
    try:
        price = int(message.text.strip().replace(" ", "").replace(",", ""))
        if price <= 0 or price > 10000:
            raise ValueError
    except ValueError:
        await message.answer("❌ Narxni to'g'ri kiriting (faqat raqam, 1-10000 USD):", reply_markup=cancel_keyboard())
        return
    await state.update_data(price=price)
    await state.set_state(ListingForm.gender_pref)
    await message.answer(
        "👥 <b>Jins afzalligini tanlang:</b>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="👨 Faqat erkaklar", callback_data="gender_male")],
            [InlineKeyboardButton(text="👩 Faqat ayollar", callback_data="gender_female")],
            [InlineKeyboardButton(text="🤝 Farqi yo'q", callback_data="gender_any")],
            [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_listing")],
        ])
    )


# ─── 8. Jins afzalligi ───────────────────────────────────────────
@router.callback_query(F.data.in_({"gender_male", "gender_female", "gender_any"}))
async def get_gender(call: CallbackQuery, state: FSMContext):
    gender_map = {"gender_male": "male", "gender_female": "female", "gender_any": "any"}
    await state.update_data(gender_preference=gender_map[call.data])
    await state.set_state(ListingForm.photo)
    await call.message.edit_text(
        "📸 <b>Rasm yuboring</b> (ixtiyoriy):\n\n"
        "<i>Xona rasmini yuboring yoki o'tkazib yuboring</i>",
        parse_mode="HTML", reply_markup=skip_keyboard()
    )
    await call.answer()


# ─── 9. Rasm ─────────────────────────────────────────────────────
@router.message(ListingForm.photo, F.photo)
async def get_photo(message: Message, state: FSMContext):
    photo = message.photo[-1]  # eng katta o'lcham
    file_id = photo.file_id
    await state.update_data(photo_file_id=file_id)
    await state.set_state(ListingForm.confirm)
    await show_confirm(message, state)


@router.callback_query(F.data == "skip_photo")
async def skip_photo(call: CallbackQuery, state: FSMContext):
    await state.update_data(photo_file_id=None)
    await state.set_state(ListingForm.confirm)
    await call.answer()
    await show_confirm(call.message, state, edit=True)


# ─── 10. Tasdiqlash ──────────────────────────────────────────────
async def show_confirm(message: Message, state: FSMContext, edit: bool = False):
    data = await state.get_data()
    type_text = "🏠 Xonam bor — sherik kerak" if data.get("listing_type") == "have_room" else "🔍 Xona kerak"
    gender_map = {"male": "👨 Faqat erkaklar", "female": "👩 Faqat ayollar", "any": "🤝 Farqi yo'q"}
    photo_text = "✅ Rasm bor" if data.get("photo_file_id") else "❌ Rasm yo'q"

    text = (
        "📋 <b>E'lon ma'lumotlarini tekshiring:</b>\n\n"
        f"<b>Turi:</b> {type_text}\n"
        f"<b>Sarlavha:</b> {data.get('title')}\n"
        f"<b>Tavsif:</b> {data.get('description')[:100]}{'...' if len(data.get('description',''))>100 else ''}\n"
        f"<b>Narx:</b> ${data.get('price')}\n"
        f"<b>Jins:</b> {gender_map.get(data.get('gender_preference','any'))}\n"
        f"<b>Rasm:</b> {photo_text}\n\n"
        "✅ To'g'rimi?"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Ha, joylash", callback_data="confirm_listing")],
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_listing")],
    ])
    if edit:
        await message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    else:
        await message.answer(text, parse_mode="HTML", reply_markup=kb)


@router.callback_query(F.data == "confirm_listing")
async def confirm_listing(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    token = data.get("token")

    wait_msg = await call.message.edit_text("⏳ E'lon joylanyapti...")

    # E'lon yaratish
    listing_data = {
        "title": data["title"],
        "description": data["description"],
        "listing_type": data["listing_type"],
        "price": data["price"],
        "city_id": data["city_id"],
        "gender_preference": data["gender_preference"],
    }
    result, status = await api_post("/listings/", listing_data, token)

    if status not in (200, 201):
        await wait_msg.edit_text(
            f"❌ Xatolik yuz berdi: {result}\n\n"
            "Qayta urinib ko'ring /new",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔄 Qayta urinish", callback_data="new_listing")]
            ])
        )
        await state.clear()
        await call.answer()
        return

    listing_id = result.get("id")

    # Rasm yuklash
    if data.get("photo_file_id") and listing_id:
        try:
            from aiogram import Bot
            from ..config import BOT_TOKEN
            bot = Bot(token=BOT_TOKEN)
            file = await bot.get_file(data["photo_file_id"])
            file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file.file_path}"

            async with aiohttp.ClientSession() as session:
                async with session.get(file_url) as img_resp:
                    img_bytes = await img_resp.read()

            form = aiohttp.FormData()
            form.add_field("image", img_bytes, filename="photo.jpg", content_type="image/jpeg")
            form.add_field("is_main", "true")
            await api_post_multipart(f"/listings/{listing_id}/photos/", form, token)
        except Exception as e:
            pass  # Rasm yuklashda xato bo'lsa, e'lon baribir joylashadi

    await state.clear()
    await wait_msg.edit_text(
        f"🎉 <b>E'lon muvaffaqiyatli joylandi!</b>\n\n"
        f"📋 E'lon ID: #{listing_id}\n"
        f"⏳ Holat: Moderatsiya kutilmoqda\n\n"
        f"<i>Admin tekshirgandan so'ng e'loningiz chiqadi.</i>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📋 Mening e'lonlarim", callback_data="my_listings")],
            [InlineKeyboardButton(text="🏠 Bosh menyu", callback_data="back_to_menu")],
        ])
    )
    await call.answer()


# ─── Bekor qilish ────────────────────────────────────────────────
@router.callback_query(F.data == "cancel_listing")
async def cancel_listing(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text(
        "❌ E'lon joylash bekor qilindi.\n\n/menu — asosiy menyuga qaytish"
    )
    await call.answer()

