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
    MANAGE_GROUPS,
    get_or_create_level,
    get_or_create_term,
    get_group_info,
    upsert_group,
)

ASK_INPUT, CONFIRM = range(2)


async def insert_group_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat

    if chat.type != "supergroup":
        await message.reply_text("استخدم هذا الأمر داخل مجموعة خارقة.")
        return ConversationHandler.END

    if not await is_admin(user.id, MANAGE_GROUPS):
        await message.reply_text("عذرًا، لا تملك صلاحية هذا الأمر.")
        return ConversationHandler.END

    info = {
        "tg_chat_id": chat.id,
        "chat_id": chat.id,
        "cmd_msg_id": message.message_id,
    }
    context.user_data["insert_group"] = info

    existing = await get_group_info(chat.id)
    if existing:
        level_id, term_id = existing
        info.update({"level_id": level_id, "term_id": term_id})
        buttons = [[
            InlineKeyboardButton("تعديل", callback_data="ingrp_edit"),
            InlineKeyboardButton("إلغاء", callback_data="ingrp_cancel"),
        ]]
        reply = f"المجموعة مرتبطة حاليًا بالمستوى {level_id} - الترم {term_id}"
        sent = await message.reply_text(reply, reply_markup=InlineKeyboardMarkup(buttons))
        info["confirm_msg_id"] = sent.message_id
        return CONFIRM

    await message.reply_text("أرسل المستوى متبوعًا بالترم (مثال: المستوى الأول - الترم الثاني)")
    return ASK_INPUT


async def insert_group_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    info = context.user_data.get("insert_group")
    if not info:
        return ConversationHandler.END

    text = update.message.text.strip()
    parts = [p.strip() for p in text.split("-", 1)]
    level_name = parts[0]
    term_name = parts[1] if len(parts) > 1 else None

    level_id = await get_or_create_level(level_name)

    if term_name is None:
        await update.message.reply_text("حدد الترم أيضًا.")
        return ASK_INPUT

    term_id = await get_or_create_term(term_name)

    info.update(
        {
            "level_id": level_id,
            "term_id": term_id,
            "input_msg_id": update.message.message_id,
            "level_name": level_name,
            "term_name": term_name,
        }
    )

    buttons = [[
        InlineKeyboardButton("تأكيد", callback_data="ingrp_confirm"),
        InlineKeyboardButton("تعديل", callback_data="ingrp_edit"),
        InlineKeyboardButton("إلغاء", callback_data="ingrp_cancel"),
    ]]
    reply = f"المستوى: {level_name}\nالترم: {term_name}\nهل تؤكد؟"
    sent = await update.message.reply_text(reply, reply_markup=InlineKeyboardMarkup(buttons))
    info["confirm_msg_id"] = sent.message_id

    return CONFIRM


async def insert_group_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    info = context.user_data.get("insert_group")
    if not info:
        await query.edit_message_text("انتهت الجلسة.")
        return ConversationHandler.END

    chat_id = info["chat_id"]
    bot = context.bot

    if data == "ingrp_confirm":
        title = update.effective_chat.title or ""
        await upsert_group(info["tg_chat_id"], info["level_id"], info["term_id"], title)
        await query.edit_message_text("تم الحفظ بنجاح.")
        for key in ("cmd_msg_id", "input_msg_id"):
            msg_id = info.get(key)
            if msg_id:
                try:
                    await bot.delete_message(chat_id, msg_id)
                except Exception:
                    pass
        context.user_data.pop("insert_group", None)
        return ConversationHandler.END

    if data == "ingrp_edit":
        msg_id = info.get("input_msg_id")
        if msg_id:
            try:
                await bot.delete_message(chat_id, msg_id)
            except Exception:
                pass
            info.pop("input_msg_id", None)
        await query.edit_message_text("أرسل المستوى والترم مرة أخرى.")
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
    context.user_data.pop("insert_group", None)
    return ConversationHandler.END


insert_group_conv = ConversationHandler(
    entry_points=[CommandHandler("insert_group", insert_group_start, filters.ChatType.GROUPS)],
    states={
        ASK_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, insert_group_received)],
        CONFIRM: [CallbackQueryHandler(insert_group_confirm, pattern="^ingrp_")],
    },
    fallbacks=[],
)

__all__ = ["insert_group_conv"]
