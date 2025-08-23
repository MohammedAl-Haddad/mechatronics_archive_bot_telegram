from __future__ import annotations

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

from bot.db import (
    is_admin,
    get_group_id_by_chat,
    get_subject_by_name,
    upsert_topic,
)

ASK_INPUT, CONFIRM = range(2)

SECTION_ALIASES = {
    "نظري": "theory",
    "مناقشة": "discussion",
    "مناقشه": "discussion",
    "عملي": "lab",
    "theory": "theory",
    "discussion": "discussion",
    "lab": "lab",
}


async def insert_sub_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat

    if not message or message.message_thread_id is None:
        await message.reply_text("استخدم هذا الأمر داخل موضوع ضمن مجموعة.")
        return ConversationHandler.END

    if not await is_admin(user.id):
        await message.reply_text("عذرًا، لا تملك صلاحية هذا الأمر.")
        return ConversationHandler.END

    group_id = await get_group_id_by_chat(chat.id)
    if group_id is None:
        await message.reply_text("المجموعة غير مسجلة. استخدم /insert_group أولًا.")
        return ConversationHandler.END

    context.user_data["insert_sub"] = {
        "group_id": group_id,
        "thread_id": message.message_thread_id,
        "cmd_msg_id": message.message_id,
        "chat_id": chat.id,
    }

    await message.reply_text("أرسل اسم المادة متبوعًا بالقسم (مثال: فيزياء - نظري)")
    return ASK_INPUT


async def insert_sub_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    info = context.user_data.get("insert_sub")
    if not info:
        return ConversationHandler.END

    text = update.message.text.strip()
    parts = [p.strip() for p in text.split("-", 1)]
    subj_name = parts[0]
    sect_label = parts[1] if len(parts) > 1 else None

    row = await get_subject_by_name(subj_name)
    if row is None:
        await update.message.reply_text("المادة غير موجودة، حاول مرة أخرى.")
        return ASK_INPUT

    subject_id, mode = row
    section = "theory"
    if mode == "theory_only":
        sect_label = "نظري"
    else:
        if sect_label is None:
            await update.message.reply_text("حدد القسم أيضًا (نظري/مناقشة/عملي).")
            return ASK_INPUT
        section = SECTION_ALIASES.get(sect_label.lower())
        if section is None:
            await update.message.reply_text("القسم غير معروف، استخدم: نظري، مناقشة، عملي.")
            return ASK_INPUT
        if mode == "theory_discussion" and section == "lab":
            await update.message.reply_text("هذا المقرر لا يحتوي على قسم عملي.")
            return ASK_INPUT

    info.update(
        {
            "subject_id": subject_id,
            "subject_name": subj_name,
            "section": section,
            "input_msg_id": update.message.message_id,
        }
    )

    buttons = [
        [
            InlineKeyboardButton("تأكيد", callback_data="insub_confirm"),
            InlineKeyboardButton("تعديل", callback_data="insub_edit"),
            InlineKeyboardButton("إلغاء", callback_data="insub_cancel"),
        ]
    ]
    reply = f"المادة: {subj_name}\nالقسم: {sect_label or 'نظري'}\nهل تؤكد؟"
    sent = await update.message.reply_text(
        reply, reply_markup=InlineKeyboardMarkup(buttons)
    )
    info["confirm_msg_id"] = sent.message_id

    return CONFIRM


async def insert_sub_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    info = context.user_data.get("insert_sub")
    if not info:
        await query.edit_message_text("انتهت الجلسة.")
        return ConversationHandler.END

    chat_id = info["chat_id"]
    bot = context.bot

    if data == "insub_confirm":
        await upsert_topic(
            info["group_id"], info["thread_id"], info["subject_id"], info["section"]
        )
        await query.edit_message_text("تم الحفظ بنجاح.")
        for key in ("cmd_msg_id", "input_msg_id"):
            msg_id = info.get(key)
            if msg_id:
                try:
                    await bot.delete_message(chat_id, msg_id)
                except Exception:
                    pass
        context.user_data.pop("insert_sub", None)
        return ConversationHandler.END

    if data == "insub_edit":
        msg_id = info.get("input_msg_id")
        if msg_id:
            try:
                await bot.delete_message(chat_id, msg_id)
            except Exception:
                pass
            info.pop("input_msg_id", None)
        await query.edit_message_text("أرسل اسم المادة والقسم مرة أخرى.")
        return ASK_INPUT

    # cancel
    await query.edit_message_text("تم الإلغاء.")
    for key in ("cmd_msg_id", "input_msg_id"):
        msg_id = info.get(key)
        if msg_id:
            try:
                await bot.delete_message(chat_id, msg_id)
            except Exception:
                pass
    context.user_data.pop("insert_sub", None)
    return ConversationHandler.END


insert_sub_conv = ConversationHandler(
    entry_points=[CommandHandler("insert_sub", insert_sub_start)],
    states={
        ASK_INPUT: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, insert_sub_received)
        ],
        CONFIRM: [CallbackQueryHandler(insert_sub_confirm, pattern="^insub_")],
    },
    fallbacks=[],
)

__all__ = ["insert_sub_conv"]
