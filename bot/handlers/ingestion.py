from telegram import Update
from telegram.ext import ContextTypes

from ..db import (
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
from ..db import (
    get_group_id_by_chat,
    get_topic_link,
)
from ..parser.hashtags import parse_hashtags
import logging


logger = logging.getLogger(__name__)


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
    message = update.effective_message
    tags = _extract_hashtags(update)
    if not tags:
        logger.warning("No hashtags found")
        if message:
            await message.reply_text("لم يتم العثور على وسوم.")
        return

    user = update.effective_user
    if not user:
        logger.warning("No effective user on update")
        if message:
            await message.reply_text("لا يمكن تحديد المستخدم.")
        return

    admin_info = await get_admin_with_permissions(user.id)
    if admin_info is None:
        logger.warning("User %s is not an admin", user.id)
        if message:
            await message.reply_text("المستخدم ليس مشرفًا.")
        return
    admin_id, permissions = admin_info
    if not (permissions & UPLOAD_CONTENT):
        logger.warning("User %s lacks upload permission", user.id)
        await message.reply_text("لا تملك صلاحية رفع المحتوى.")
        return

    chat = update.effective_chat
    thread_id = message.message_thread_id if message else None
    if chat is None or thread_id is None:
        logger.warning("Missing chat %s or thread %s", chat, thread_id)
        if message:
            await message.reply_text("لا يمكن تحديد المحادثة أو الموضوع.")
        return

    group_info = await get_group_id_by_chat(chat.id)
    logger.debug("group_info=%s", group_info)
    if group_info is None:
        logger.warning("Group info not found for chat %s", chat.id)
        await message.reply_text("المجموعة غير معروفة.")
        return
    group_id, _, _ = group_info

    topic_link = await get_topic_link(group_id, thread_id)
    logger.debug("topic_link=%s", topic_link)
    if topic_link is None:
        logger.warning(
            "Topic link not found for group %s thread %s", group_id, thread_id
        )
        await message.reply_text("لم يتم العثور على رابط الموضوع.")
        return
    subject_id, _, section = topic_link

    info = parse_hashtags(tags)
    logger.debug("category=%s title=%s", info["category"], info["title"])
    category = info["category"]
    title = info["title"]
    lecturer_name = info["lecturer"]

    # ``board_images`` is one of the supported categories and relies on the
    # extracted title (either from ``category:title`` syntax or remaining
    # hashtags) to identify the lecture it belongs to.
    if category is None or title is None:
        logger.warning("Missing category or title in hashtags")
        await message.reply_text("الوسوم تفتقد الفئة أو العنوان.")
        return

    year_id = None
    if info["year"]:
        year_id = await ensure_year_id(info["year"])
    lecturer_id = None
    if lecturer_name:
        lecturer_id = await ensure_lecturer_id(lecturer_name)

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
    await message.reply_text(f"تم تسجيل العملية برقم {ingestion_id}")


__all__ = ["ingestion_handler"]

