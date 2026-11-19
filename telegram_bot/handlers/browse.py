"""
E'lonlarni ko'rish va mening e'lonlarim
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from ..api_client import api_get

router = Router()


def listing_card(listing: dict) -> str:
    """E'lon kartochkasi matni"""
    type_icon = "🏠" if listing.get("listing_type") == "have_room" else "🔍"
    gender_map = {"male": "👨", "female": "👩", "any": "🤝"}
    gender = gender_map.get(listing.get("gender_preference", "any"), "🤝")
    city = listing.get("city_name", "")
    district = listing.get("district_name", "")
    location = f"{city}" + (f", {district}" if district else "")

    return (
        f"{type_icon} <b>{listing.get('title', '')}</b>\n"
        f"💰 ${listing.get('price', 0)}/oy\n"
        f"📍 {location}\n"
        f"👥 {gender} | ID: #{listing.get('id')}\n"
    )


# ─── E'lonlarni ko'rish ───────────────────────────────────────────
@router.callback_query(F.data == "browse_listings")
@router.callback_query(F.data.startswith("browse_page_"))
async def browse_listings(call: CallbackQuery, state: FSMContext):
    page = 1
    if call.data.startswith("browse_page_"):
        page = int(call.data.split("_")[-1])

    wait = await call.message.edit_text("🔍 E'lonlar yuklanmoqda...")

    result, status = await api_get("/listings/", params={"page": page})

    if status != 200:
        await wait.edit_text("❌ E'lonlarni olishda xatolik. Keyinroq urinib ko'ring.")
        await call.answer()
        return

    listings = result.get("results", [])
    total = result.get("count", 0)
    total_pages = (total + 9) // 10

    if not listings:
        await wait.edit_text(
            "😔 Hozircha e'lonlar yo'q.\n\n"
            "Birinchi bo'lib e'lon joylang! /new",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📋 E'lon joylash", callback_data="new_listing")],
                [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="back_to_menu")],
            ])
        )
        await call.answer()
        return

    text = f"📋 <b>E'lonlar</b> ({total} ta, sahifa {page}/{total_pages})\n\n"
    for listing in listings:
        text += listing_card(listing) + "\n"

    # Navigatsiya tugmalari
    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"browse_page_{page-1}"))
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton(text="Keyingi ➡️", callback_data=f"browse_page_{page+1}"))

    kb = InlineKeyboardMarkup(inline_keyboard=[
        nav_buttons if nav_buttons else [],
        [InlineKeyboardButton(text="📋 E'lon joylash", callback_data="new_listing")],
        [InlineKeyboardButton(text="⬅️ Bosh menyu", callback_data="back_to_menu")],
    ])

    await wait.edit_text(text, parse_mode="HTML", reply_markup=kb)
    await call.answer()


# ─── Mening e'lonlarim ────────────────────────────────────────────
@router.callback_query(F.data == "my_listings")
async def my_listings(call: CallbackQuery, state: FSMContext):
    from aiogram.fsm.context import FSMContext
    data = await state.get_data()
    token = data.get("token")

    if not token:
        await call.message.edit_text(
            "🔐 Bu bo'limni ko'rish uchun tizimga kirishingiz kerak.\n"
            "E'lon joylash orqali login qiling:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📋 E'lon joylash / Login", callback_data="new_listing")],
                [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="back_to_menu")],
            ])
        )
        await call.answer()
        return

    result, status = await api_get("/listings/my/", token=token)

    if status == 401:
        await state.update_data(token=None)
        await call.message.edit_text(
            "⏰ Sessiya muddati tugagan. Qayta login qiling:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📋 Qayta kirish", callback_data="new_listing")],
            ])
        )
        await call.answer()
        return

    listings = result.get("results", []) if isinstance(result, dict) else []

    if not listings:
        await call.message.edit_text(
            "📭 Sizda hozircha e'lon yo'q.\n\nBirinchi e'loningizni joylashtiring!",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📋 E'lon joylash", callback_data="new_listing")],
                [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="back_to_menu")],
            ])
        )
        await call.answer()
        return

    text = "📋 <b>Mening e'lonlarim:</b>\n\n"
    status_map = {"active": "✅ Faol", "closed": "🔴 Yopilgan"}
    mod_map = {"pending": "⏳ Moderatsiyada", "approved": "✅ Tasdiqlangan", "rejected": "❌ Rad etilgan"}

    for l in listings:
        text += (
            f"{'🏠' if l.get('listing_type')=='have_room' else '🔍'} <b>{l.get('title','')}</b>\n"
            f"   {status_map.get(l.get('status',''), l.get('status',''))} | "
            f"{mod_map.get(l.get('moderation_status',''), l.get('moderation_status',''))}\n"
            f"   💰 ${l.get('price',0)} | ID: #{l.get('id')}\n\n"
        )

    await call.message.edit_text(
        text, parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📋 Yangi e'lon", callback_data="new_listing")],
            [InlineKeyboardButton(text="⬅️ Bosh menyu", callback_data="back_to_menu")],
        ])
    )
    await call.answer()

