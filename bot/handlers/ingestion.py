from telegram import Update
from telegram.ext import ContextTypes

from ..db.ingestions import get_admin_id_by_tg_user, insert_ingestion
from ..db.topics import is_admin


def _extract_hashtags(update: Update) -> list[str]:
    msg = update.message
    if not msg:
        return []
    text = msg.text or msg.caption or ""
    entities = msg.entities or msg.caption_entities or []
    tags = []
    for ent in entities:
        if ent.type == "hashtag":
            tags.append(text[ent.offset : ent.offset + ent.length])
    return tags


async def ingestion_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    tags = _extract_hashtags(update)
    if not tags:
        return

    user = update.effective_user
    if not user or not await is_admin(user.id):
        return

    admin_id = await get_admin_id_by_tg_user(user.id)
    if admin_id is None:
        return

    message = update.effective_message
    ingestion_id = await insert_ingestion(message.message_id, admin_id)
    await message.reply_text(f"✅ {ingestion_id}")


__all__ = ["ingestion_handler"]

