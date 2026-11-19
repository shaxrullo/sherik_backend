"""
/start va asosiy menyu handleri
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext

from ..config import MINI_APP_URL

router = Router()


def main_menu_keyboard(mini_app_url: str) -> InlineKeyboardMarkup:
    """Asosiy menyu tugmalari"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🏠 Saytni ochish",
                web_app=WebAppInfo(url=mini_app_url)
            )
        ],
        [
            InlineKeyboardButton(text="📋 E'lon joylash", callback_data="new_listing"),
            InlineKeyboardButton(text="🔍 E'lonlarni ko'rish", callback_data="browse_listings"),
        ],
        [
            InlineKeyboardButton(text="👤 Mening e'lonlarim", callback_data="my_listings"),
            InlineKeyboardButton(text="❤️ Sevimlilar", callback_data="favorites"),
        ],
        [
            InlineKeyboardButton(text="ℹ️ Yordam", callback_data="help"),
        ],
    ])


@router.message(CommandStart())
async def start_handler(message: Message, state: FSMContext):
    await state.clear()
    user_name = message.from_user.first_name or "Foydalanuvchi"

    text = (
        f"Salom, <b>{user_name}</b>! 👋\n\n"
        f"<b>Sherik</b> — O'zbekistondagi talabalar va ishlovchilar uchun "
        f"uy-joy va sheriklik platformasi.\n\n"
        f"🏠 Xona qidiryapsizmi yoki sherik kerrakmi?\n"
        f"Quyidagi tugmalardan birini tanlang:"
    )

    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(MINI_APP_URL)
    )


@router.message(Command("menu"))
async def menu_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "📌 Asosiy menyu:",
        reply_markup=main_menu_keyboard(MINI_APP_URL)
    )


@router.callback_query(F.data == "help")
async def help_handler(call: CallbackQuery):
    text = (
        "ℹ️ <b>Sherik Bot haqida</b>\n\n"
        "Bu bot orqali siz:\n"
        "• 🏠 <b>Saytni ochish</b> — to'liq saytni Telegram ichida ko'rishingiz\n"
        "• 📋 <b>E'lon joylash</b> — xona yoki sherik qidiruv e'lonini botdan joylashingiz\n"
        "• 🔍 <b>E'lonlarni ko'rish</b> — mavjud e'lonlarni ko'rishingiz\n"
        "• ❤️ <b>Sevimlilar</b> — saqlangan e'lonlaringizni ko'rishingiz mumkin\n\n"
        "<b>Buyruqlar:</b>\n"
        "/start — Boshlanish\n"
        "/menu — Asosiy menyu\n"
        "/new — Yangi e'lon joylash\n"
        "/mylistings — Mening e'lonlarim\n\n"
        "📞 Muammo bo'lsa: @sherik_support"
    )
    await call.message.edit_text(text, parse_mode="HTML",
                                  reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                      [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="back_to_menu")]
                                  ]))
    await call.answer()


@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text(
        "📌 Asosiy menyu:",
        reply_markup=main_menu_keyboard(MINI_APP_URL)
    )
    await call.answer()

