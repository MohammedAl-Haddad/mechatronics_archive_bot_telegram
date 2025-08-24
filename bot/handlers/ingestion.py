from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler

import logging

from ..config import OWNER_TG_ID
from ..db import (
    UPLOAD_CONTENT,
    get_admin_with_permissions,
    insert_ingestion,
    attach_material,
    get_group_id_by_chat,
    get_binding,
    get_or_create_year,
    get_or_create_lecturer,
    insert_term_resource,
)
from ..db.materials import insert_material, find_exact
from ..parser.hashtags import parse_hashtags
from ..utils.telegram import send_ephemeral, get_file_unique_id_from_message


logger = logging.getLogger(__name__)


async def ingestion_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    file_unique_id = get_file_unique_id_from_message(message)
    text = message.caption or message.text or ""
    info, error = parse_hashtags(text)
    if error:
        await message.reply_text(error)
        return

    year = info.year
    category = info.content_type
    title = info.title or ""
    lecturer_name = info.lecturer

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
    if chat is None:
        logger.warning("Missing chat %s", chat)
        if message:
            await message.reply_text("لا يمكن تحديد المحادثة.")
        return

    group_info = await get_group_id_by_chat(chat.id)
    logger.debug("group_info=%s", group_info)
    if group_info is None:
        logger.warning("Group info not found for chat %s", chat.id)
        await message.reply_text("المجموعة غير معروفة.")
        return
    binding = None
    if category != "attendance":
        if thread_id is None:
            await message.reply_text(
                "هذا النوع يتطلب ربط الـTopic بمادة/قسم عبر /insert_sub."
            )
            return
        binding = await get_binding(chat.id, thread_id)
        logger.debug("binding=%s", binding)
        if binding is None:
            await message.reply_text(
                "هذا النوع يتطلب ربط الـTopic بمادة/قسم عبر /insert_sub."
            )
            return
        subject_id = binding["subject_id"]
        section = binding["section"]
        subject_name = binding["subject_name"]
    else:
        subject_id = section = subject_name = None

    if category is None:
        await message.reply_text("لم يتم التعرف على نوع المحتوى.")
        return

    if category == "attendance":
        term_id = group_info[2]
        await insert_term_resource(term_id, "attendance", chat.id, message.message_id)
        await message.reply_text("✅ تم الاستلام.")
        return

    year_id = await get_or_create_year(str(year)) if year else None
    lecturer_id = (
        await get_or_create_lecturer(lecturer_name) if lecturer_name else None
    )

    existing = await find_exact(
        subject_id,
        section,
        category,
        title,
        year_id=year_id,
        lecturer_id=lecturer_id,
    )
    if existing:
        ctx = context.user_data.setdefault("replace_ctx", {})
        ctx[message.message_id] = {
            "old_material_id": existing[0],
            "chat_id": chat.id,
            "admin_id": admin_id,
            "subject_name": subject_name,
            "section": section,
            "category": category,
            "title": title,
            "year": year,
            "year_id": year_id,
            "lecturer_id": lecturer_id,
            "lecturer_name": lecturer_name,
            "file_unique_id": file_unique_id,
        }
        buttons = [
            [
                InlineKeyboardButton(
                    "استبدال",
                    callback_data=f"dup:rep:{message.message_id}:{existing[0]}",
                ),
                InlineKeyboardButton(
                    "إلغاء", callback_data=f"dup:cancel:{message.message_id}"
                ),
            ]
        ]
        await message.reply_text(
            "هذا الملف مرفوع من قبل لنفس المحاضرة/السنة/المحاضر.",
            reply_markup=InlineKeyboardMarkup(buttons),
        )
        return

    material_id = await insert_material(
        subject_id,
        section,
        category,
        title,
        year_id=year_id,
        lecturer_id=lecturer_id,
        file_unique_id=file_unique_id,
        source_chat_id=chat.id,
        source_topic_id=thread_id,
        source_message_id=message.message_id,
        created_by_admin_id=admin_id,
    )

    ingestion_id = await insert_ingestion(
        message.message_id, admin_id, file_unique_id=file_unique_id
    )
    await attach_material(ingestion_id, material_id, "pending")
    await message.reply_text(
        f"✅ تم الاستلام. رقم العملية: #{ingestion_id}\nسيتم إشعارك بعد المراجعة."
    )
    logger.info(
        "pending #%s subject=%s section=%s year=%s type=%s title=%s",
        ingestion_id,
        subject_name,
        section,
        year,
        category,
        title,
    )

    summary = (
        f"المادة: {subject_name}\nالقسم: {section}\nالسنة: {year or '---'}\nالنوع: {category}\nالعنوان: {title}"
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


async def handle_duplicate_decision(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    query = update.callback_query
    await query.answer()
    _, action, msg_id, *rest = query.data.split(":")
    msg_id = int(msg_id)
    ctx = context.user_data.get("replace_ctx", {})
    data = ctx.get(msg_id)
    if data is None:
        await query.edit_message_text("انتهت صلاحية الطلب.")
        return
    if action == "cancel":
        ctx.pop(msg_id, None)
        await send_ephemeral(context, query.message.chat_id, "تم الإلغاء.")
        return
    old_material_id = data["old_material_id"]
    admin_id = data["admin_id"]
    ingestion_id = await insert_ingestion(
        msg_id, admin_id, action="replace", file_unique_id=data.get("file_unique_id")
    )
    await attach_material(ingestion_id, old_material_id, "pending")
    await context.bot.send_message(
        chat_id=data["chat_id"],
        text=(
            f"✅ تم الاستلام. رقم العملية: #{ingestion_id}\nسيتم إشعارك بعد المراجعة."
        ),
        reply_to_message_id=msg_id,
    )
    summary = (
        "طلب استبدال ملف مرفوع سابقًا\n"
        f"المادة: {data['subject_name']}\nالقسم: {data['section']}\n"
        f"السنة: {data['year'] or '---'}\nالنوع: {data['category']}\nالعنوان: {data['title']}"
    )
    buttons = [
        [
            InlineKeyboardButton(
                "Approve استبدال", callback_data=f"appr:{ingestion_id}"
            ),
            InlineKeyboardButton("Reject", callback_data=f"rej:{ingestion_id}"),
        ]
    ]
    try:
        await context.bot.copy_message(
            chat_id=OWNER_TG_ID,
            from_chat_id=data["chat_id"],
            message_id=msg_id,
            caption=summary,
            reply_markup=InlineKeyboardMarkup(buttons),
        )
    except Exception as e:
        logger.error("Failed to notify approver: %s", e)
    ctx.pop(msg_id, None)


duplicate_callback = CallbackQueryHandler(
    handle_duplicate_decision, pattern=r"^dup:(rep|cancel):"
)


__all__ = ["ingestion_handler", "duplicate_callback"]

