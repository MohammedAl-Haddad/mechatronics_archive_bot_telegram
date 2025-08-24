from telegram import Update
from telegram.ext import ContextTypes

from ..keyboards.builders import build_main_menu
from ..navigation import NavigationState
from bot.db import is_owner, has_perm, MANAGE_ADMINS


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    NavigationState(context.user_data).back_to_levels()
    user = update.effective_user
    is_admin = False
    if user:
        is_admin = is_owner(user.id) or await has_perm(user.id, MANAGE_ADMINS)
    await update.message.reply_text(
        "👋 مرحبًا بك في بوت أرشيف قسم الميكاترونكس.\nاختر من القائمة:",
        reply_markup=build_main_menu(is_admin),
    )
