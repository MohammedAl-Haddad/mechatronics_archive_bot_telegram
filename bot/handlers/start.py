from telegram import Update
from telegram.ext import ContextTypes

from ..keyboards.constants import main_menu

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 مرحبًا بك في بوت أرشيف قسم الميكاترونكس.\nاختر من القائمة:",
        reply_markup=main_menu)
