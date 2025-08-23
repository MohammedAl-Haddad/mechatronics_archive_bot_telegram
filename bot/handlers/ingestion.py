from telegram import Update
from telegram.ext import ContextTypes

from ..db.ingestions import (
    UPLOAD_CONTENT,
    get_admin_with_permissions,
    insert_ingestion,
    attach_material,
)
from ..db.materials import (
    ensure_year_id,
    ensure_lecturer_id,
    insert_material,
)
from ..db.topics import (
    get_group_id_by_chat,
    get_topic_link,
)
from ..parser.hashtags import parse_hashtags


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
    if not user:
        return

    admin_info = await get_admin_with_permissions(user.id)
    if admin_info is None:
        return
    admin_id, permissions = admin_info
    if not (permissions & UPLOAD_CONTENT):
        return

    message = update.effective_message
    chat = update.effective_chat
    thread_id = message.message_thread_id
    if chat is None or thread_id is None:
        return

    group_info = await get_group_id_by_chat(chat.id)
    if group_info is None:
        return
    group_id, _, _ = group_info

    topic_link = await get_topic_link(group_id, thread_id)
    if topic_link is None:
        return
    subject_id, _, section = topic_link

    info = parse_hashtags(tags)
    category = info.get("category")
    title = info.get("title")
    if not category or not title:
        return

    year_id = None
    if info.get("year"):
        year_id = await ensure_year_id(info["year"])
    lecturer_id = None
    if info.get("lecturer"):
        lecturer_id = await ensure_lecturer_id(info["lecturer"])

    material_id = await insert_material(
        subject_id,
        section,
        category,
        title,
        year_id=year_id,
        lecturer_id=lecturer_id,
        source_chat_id=chat.id,
        source_topic_id=thread_id,
        source_message_id=message.message_id,
        created_by_admin_id=admin_id,
    )

    ingestion_id = await insert_ingestion(message.message_id, admin_id)
    await attach_material(ingestion_id, material_id, "pending")
    await message.reply_text(f"⏳ {ingestion_id}")


__all__ = ["ingestion_handler"]

