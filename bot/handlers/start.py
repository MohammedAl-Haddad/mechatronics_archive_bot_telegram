from telegram import Update
from telegram.ext import ContextTypes

from ..keyboards.builders import generate_main_menu
from ..navigation import NavigationState


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    NavigationState(context.user_data).back_to_levels()
    await update.message.reply_text(
        "👋 مرحبًا بك في بوت أرشيف قسم الميكاترونكس.\nاختر من القائمة:",
        reply_markup=await generate_main_menu(update.effective_user.id),
    )
