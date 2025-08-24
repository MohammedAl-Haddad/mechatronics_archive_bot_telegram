from telegram import Update
from telegram.ext import CommandHandler, ContextTypes, filters

from bot.db import (
    is_owner,
    has_perm,
    MANAGE_GROUPS,
    UPLOAD_CONTENT,
    APPROVE_CONTENT,
    MANAGE_ADMINS,
)
from bot.config import VERSION, START_TIME


async def me(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not user:
        return
    lines = [f"معرفك: {user.id}"]
    if is_owner(user.id):
        lines.append("أنت الـOwner.")
    lines.append("الصلاحيات:")
    perms = [
        (MANAGE_GROUPS, "إدارة المجموعات"),
        (UPLOAD_CONTENT, "رفع المحتوى"),
        (APPROVE_CONTENT, "مصادقة المحتوى"),
        (MANAGE_ADMINS, "إدارة المشرفين"),
    ]
    for flag, label in perms:
        allowed = await has_perm(user.id, flag)
        lines.append(f"- {label}: {'✅' if allowed else '❌'}")
    await update.message.reply_text("\n".join(lines))


async def version(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        f"الإصدار: {VERSION}\n"
        f"وقت الإقلاع: {START_TIME.strftime('%Y-%m-%d %H:%M:%S')}\n"
        "تأكد أن التوثيق محدث."
    )
    await update.message.reply_text(text)


me_handler = CommandHandler("me", me, filters.ChatType.PRIVATE)
version_handler = CommandHandler("version", version, filters.ChatType.PRIVATE)

__all__ = ["me_handler", "version_handler"]
