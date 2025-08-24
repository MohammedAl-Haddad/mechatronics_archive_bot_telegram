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
    get_or_create_level,
    get_or_create_term,
    get_group_info,
    upsert_group,
)
from bot.utils.conv import conv_push, conv_cleanup
from bot.utils.telegram import send_ephemeral

logger = logging.getLogger("bot.binding")

CHOOSING, AWAIT_INPUT, CONFIRM = range(3)


async def insert_group_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat

    if chat.type != "supergroup":
        await message.reply_text("استخدم هذا الأمر داخل مجموعة خارقة.")
        return ConversationHandler.END

    if not (is_owner(user.id) or await has_perm(user.id, MANAGE_GROUPS)):
        await message.reply_text("عذرًا، لا تملك صلاحية هذا الأمر.")
        return ConversationHandler.END

    conv_push(context, message.message_id)

    existing = await get_group_info(chat.id)
    buttons = [
        [
            InlineKeyboardButton("إدخال يدوي", callback_data="grp_manual"),
            InlineKeyboardButton("إلغاء", callback_data="grp_cancel"),
        ]
    ]
    if existing:
        buttons.insert(0, [InlineKeyboardButton("تعديل الربط", callback_data="grp_manual")])

    sent = await message.reply_text(
        "اربط هذه المجموعة بالمستوى والترم.\nمثال: المستوى الأول — الترم الأول",
        reply_markup=InlineKeyboardMarkup(buttons),
    )
    conv_push(context, sent.message_id)
    context.chat_data["insert_group"] = {}
    return CHOOSING


async def insert_group_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "grp_manual":
        await query.edit_message_text("أرسل: المستوى - الترم")
        return AWAIT_INPUT
    await conv_cleanup(context, context.bot, update.effective_chat.id)
    return ConversationHandler.END


async def insert_group_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conv_push(context, update.message.message_id)
    text = update.message.text.strip()
    parts = [p.strip() for p in text.split("-", 1)]
    if len(parts) < 2:
        sent = await update.message.reply_text("أرسل: المستوى - الترم")
        conv_push(context, sent.message_id)
        return AWAIT_INPUT

    level_name, term_name = parts
    level_id = await get_or_create_level(level_name)
    term_id = await get_or_create_term(term_name)

    context.chat_data["insert_group"].update(
        {
            "level_id": level_id,
            "term_id": term_id,
            "level_name": level_name,
            "term_name": term_name,
        }
    )
    buttons = [
        [
            InlineKeyboardButton("تأكيد", callback_data="grp_confirm"),
            InlineKeyboardButton("إلغاء", callback_data="grp_cancel"),
        ]
    ]
    sent = await update.message.reply_text(
        f"سيتم ربط هذه المجموعة بـ: {level_name} - {term_name}",
        reply_markup=InlineKeyboardMarkup(buttons),
    )
    conv_push(context, sent.message_id)
    return CONFIRM


async def insert_group_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    info = context.chat_data.get("insert_group", {})
    if data == "grp_confirm" and info:
        title = update.effective_chat.title or ""
        await upsert_group(update.effective_chat.id, info["level_id"], info["term_id"], title)
        logger.info(
            "group %s linked to level=%s term=%s",
            update.effective_chat.id,
            info["level_id"],
            info["term_id"],
        )
        await conv_cleanup(context, context.bot, update.effective_chat.id)
        await send_ephemeral(context, update.effective_chat.id, "تم الربط بنجاح.")
    else:
        await conv_cleanup(context, context.bot, update.effective_chat.id)
        await send_ephemeral(context, update.effective_chat.id, "تم الإلغاء.")
    context.chat_data.pop("insert_group", None)
    return ConversationHandler.END


insert_group_conv = ConversationHandler(
    entry_points=[CommandHandler("insert_group", insert_group_start, filters.ChatType.GROUPS)],
    states={
        CHOOSING: [CallbackQueryHandler(insert_group_choice, pattern="^grp_")],
        AWAIT_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, insert_group_received)],
        CONFIRM: [CallbackQueryHandler(insert_group_confirm, pattern="^grp_")],
    },
    fallbacks=[],
)


async def insert_group_private(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    if message:
        try:
            await message.delete()
        except Exception as e:
            logger.debug("delete failed: %s", e)
        await update.effective_chat.send_message("هذا أمر خاص بالمجموعات.")


__all__ = ["insert_group_conv", "insert_group_private"]
