import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

from bot.db import (
    is_owner,
    has_perm,
    MANAGE_GROUPS,
    get_group_id_by_chat,
    get_subject_by_name,
    get_topic_link,
    insert_subject,
    update_subject_mode,
    upsert_topic,
)
from bot.utils.conv import conv_push, conv_cleanup

logger = logging.getLogger(__name__)

CHOOSING, AWAIT_INPUT, CONFIRM = range(3)

SECTION_ALIASES = {
    "نظري": "theory",
    "مناقشة": "discussion",
    "مناقشه": "discussion",
    "عملي": "lab",
    "theory": "theory",
    "discussion": "discussion",
    "lab": "lab",
}

SECTION_LABELS = {
    "theory": "نظري",
    "discussion": "مناقشة",
    "lab": "عملي",
}


async def insert_sub_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat

    if chat.type != "supergroup":
        await message.reply_text("استخدم هذا الأمر داخل مجموعة خارقة.")
        return ConversationHandler.END
    if message.message_thread_id is None:
        await message.reply_text("استخدم هذا الأمر داخل موضوع ضمن مجموعة.")
        return ConversationHandler.END
    if not (is_owner(user.id) or await has_perm(user.id, MANAGE_GROUPS)):
        await message.reply_text("عذرًا، لا تملك صلاحية هذا الأمر.")
        return ConversationHandler.END

    group_info = await get_group_id_by_chat(chat.id)
    if group_info is None:
        await message.reply_text("المجموعة غير مسجلة. استخدم /insert_group أولًا.")
        return ConversationHandler.END
    group_id, level_id, term_id = group_info
    thread_id = message.message_thread_id

    conv_push(context, message.message_id)
    context.chat_data["insert_sub"] = {
        "group_id": group_id,
        "thread_id": thread_id,
        "level_id": level_id,
        "term_id": term_id,
    }

    existing = await get_topic_link(group_id, thread_id)
    buttons = [
        [InlineKeyboardButton("إدخال يدوي", callback_data="sub_manual"), InlineKeyboardButton("إلغاء", callback_data="sub_cancel")]
    ]
    if existing:
        buttons.insert(0, [InlineKeyboardButton("تعديل الربط", callback_data="sub_manual")])
    sent = await message.reply_text(
        "اربط هذا الـ Topic بالمادة والقسم.\nمثال: دوائر كهربائية (1) - نظري",
        reply_markup=InlineKeyboardMarkup(buttons),
    )
    conv_push(context, sent.message_id)
    return CHOOSING


async def insert_sub_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "sub_manual":
        await query.edit_message_text("أرسل: المادة - القسم")
        return AWAIT_INPUT
    await conv_cleanup(context, context.bot, query.message.chat_id)
    context.chat_data.pop("insert_sub", None)
    return ConversationHandler.END


async def insert_sub_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conv_push(context, update.message.message_id)
    info = context.chat_data.get("insert_sub")
    if not info:
        return ConversationHandler.END

    text = update.message.text.strip()
    parts = [p.strip() for p in text.split("-", 1)]
    subj_name = parts[0]
    sect_label = parts[1] if len(parts) > 1 else None

    row = await get_subject_by_name(subj_name)
    if row is None:
        if sect_label is None:
            sent = await update.message.reply_text("حدد القسم أيضًا (نظري/مناقشة/عملي).")
            conv_push(context, sent.message_id)
            return AWAIT_INPUT
        section = SECTION_ALIASES.get(sect_label.lower())
        if section is None:
            sent = await update.message.reply_text("القسم غير معروف، استخدم: نظري، مناقشة، عملي.")
            conv_push(context, sent.message_id)
            return AWAIT_INPUT
        mode = "theory_only"
        if section == "discussion":
            mode = "theory_discussion"
        elif section == "lab":
            mode = "theory_discussion_lab"
        await insert_subject("AUTO", subj_name, info["level_id"], info["term_id"], sections_mode=mode)
        row = await get_subject_by_name(subj_name)
        subject_id, _ = row
    else:
        subject_id, mode = row
        if mode == "theory_only":
            section = "theory"
            if sect_label and SECTION_ALIASES.get(sect_label.lower()) not in ("theory", None):
                new_mode = (
                    "theory_discussion" if SECTION_ALIASES.get(sect_label.lower()) == "discussion" else "theory_discussion_lab"
                )
                await update_subject_mode(subject_id, new_mode)
        else:
            if sect_label is None:
                sent = await update.message.reply_text("حدد القسم أيضًا (نظري/مناقشة/عملي).")
                conv_push(context, sent.message_id)
                return AWAIT_INPUT
            section = SECTION_ALIASES.get(sect_label.lower())
            if section is None:
                sent = await update.message.reply_text("القسم غير معروف، استخدم: نظري، مناقشة، عملي.")
                conv_push(context, sent.message_id)
                return AWAIT_INPUT
            if mode == "theory_discussion" and section == "lab":
                sent = await update.message.reply_text("هذا المقرر لا يحتوي على قسم عملي.")
                conv_push(context, sent.message_id)
                return AWAIT_INPUT
    sect_label = SECTION_LABELS.get(section, sect_label)

    info.update({"subject_id": subject_id, "subject_name": subj_name, "section": section})

    buttons = [[InlineKeyboardButton("تأكيد", callback_data="sub_confirm"), InlineKeyboardButton("إلغاء", callback_data="sub_cancel")]]
    sent = await update.message.reply_text(
        f"سيتم ربط هذا الـ Topic بـ: {subj_name} - {sect_label}",
        reply_markup=InlineKeyboardMarkup(buttons),
    )
    conv_push(context, sent.message_id)
    return CONFIRM


async def insert_sub_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    info = context.chat_data.get("insert_sub")
    if query.data == "sub_confirm" and info:
        await upsert_topic(info["group_id"], info["thread_id"], info["subject_id"], info["section"])
        await conv_cleanup(context, context.bot, update.effective_chat.id)
        sent = await update.effective_chat.send_message("تم الربط بنجاح.")
        try:
            await asyncio.sleep(5)
            await context.bot.delete_message(update.effective_chat.id, sent.message_id)
        except Exception as e:
            logger.debug("delete failed: %s", e)
    else:
        await conv_cleanup(context, context.bot, update.effective_chat.id)
        sent = await update.effective_chat.send_message("تم الإلغاء.")
        try:
            await asyncio.sleep(5)
            await context.bot.delete_message(update.effective_chat.id, sent.message_id)
        except Exception as e:
            logger.debug("delete failed: %s", e)
    context.chat_data.pop("insert_sub", None)
    return ConversationHandler.END


insert_sub_conv = ConversationHandler(
    entry_points=[CommandHandler("insert_sub", insert_sub_start, filters.ChatType.GROUPS)],
    states={
        CHOOSING: [CallbackQueryHandler(insert_sub_choice, pattern="^sub_")],
        AWAIT_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, insert_sub_received)],
        CONFIRM: [CallbackQueryHandler(insert_sub_confirm, pattern="^sub_")],
    },
    fallbacks=[],
)


async def insert_sub_private(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    if message:
        try:
            await message.delete()
        except Exception as e:
            logger.debug("delete failed: %s", e)
        await update.effective_chat.send_message("هذا أمر خاص بالمجموعات.")


__all__ = ["insert_sub_conv", "insert_sub_private"]
