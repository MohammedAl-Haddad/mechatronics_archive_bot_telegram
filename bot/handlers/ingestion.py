from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

import logging
import re

from ..config import OWNER_TG_ID
from ..db import (
    UPLOAD_CONTENT,
    get_admin_with_permissions,
    insert_ingestion,
    attach_material,
    get_group_id_by_chat,
    get_topic_link,
)
from ..db.materials import ensure_year_id, ensure_lecturer_id, insert_material
from ..parser.hashtags import parse_hashtags, extract_hijri_year


logger = logging.getLogger(__name__)

HASHTAG_RE = re.compile(r"#\S+")


def _extract_hashtags(text: str) -> list[str]:
    return HASHTAG_RE.findall(text)


async def ingestion_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    text = message.caption or message.text or ""
    year = extract_hijri_year(text)
    tags = _extract_hashtags(text)
    if year is not None:
        tags = [t for t in tags if extract_hijri_year(t) is None]
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
    category = info["category"]
    title = info["title"]
    lecturer_name = info["lecturer"]
    if category is None or title is None:
        await message.reply_text("الوسوم تفتقد الفئة أو العنوان.")
        return

    year_id = await ensure_year_id(str(year)) if year else None
    lecturer_id = await ensure_lecturer_id(lecturer_name) if lecturer_name else None

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
    await message.reply_text(
        f"✅ تم الاستلام. رقم العملية: #{ingestion_id}\nسيتم إشعارك بعد المراجعة."
    )

    summary = (
        f"المادة: {topic_link[1]}\nالقسم: {section}\nالسنة: {year or '---'}\nالنوع: {category}\nالعنوان: {title}"
    )
    buttons = [
        [
            InlineKeyboardButton("Approve", callback_data=f"appr:{ingestion_id}"),
            InlineKeyboardButton("Reject", callback_data=f"rej:{ingestion_id}"),
        ]
    ]
    try:
        await context.bot.copy_message(
            chat_id=OWNER_TG_ID,
            from_chat_id=chat.id,
            message_id=message.message_id,
            caption=summary,
            reply_markup=InlineKeyboardMarkup(buttons),
        )
    except Exception as e:
        logger.error("Failed to notify approver: %s", e)


__all__ = ["ingestion_handler"]

