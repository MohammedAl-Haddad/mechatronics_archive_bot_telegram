import logging
from telegram import Update
from telegram.ext import ContextTypes


logger = logging.getLogger(__name__)


async def moderation_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Delete messages from users without posting rights.

    If a user who is not permitted to send messages posts in a group, the
    message is removed and a private explanation is sent to the user.
    """
    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    if not message or not chat or not user:
        return

    if chat.type not in ("group", "supergroup"):
        return

    try:
        member = await context.bot.get_chat_member(chat.id, user.id)
    except Exception:
        return

    if getattr(member, "can_send_messages", True):
        return

    try:
        await message.delete()
    except Exception as e:
        logger.debug("delete failed: %s", e)

    try:
        await context.bot.send_message(
            chat_id=user.id,
            text="عذرًا، لا تملك صلاحية النشر في هذه المجموعة.",
        )
    except Exception as e:
        logger.debug("notify failed: %s", e)


__all__ = ["moderation_handler"]

