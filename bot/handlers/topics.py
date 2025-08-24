import logging
import re
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
    get_binding,
    bind,
    set_theory_only,
    get_or_create_subject,
)
from bot.utils.conv import conv_push, conv_cleanup
from bot.utils.telegram import send_ephemeral

logger = logging.getLogger("bot.binding")

START, AWAIT_INPUT, ASK_THEORY_ONLY, CONFIRM = range(4)

SECTION_ALIASES = {
    "نظري": "theory",
    "مناقشة": "discussion",
    "مناقشه": "discussion",
    "عملي": "lab",
}

SECTION_LABELS = {
    "theory": "نظري",
    "discussion": "مناقشة",
    "lab": "عملي",
}

FULL_RE = re.compile(r"^(?P<subject>[^-]+?)\s*-\s*(?P<section>نظري|عملي|مناقشة)\s*$")
NAME_RE = re.compile(r"^(?P<subject>.+?)\s*$")


async def insert_sub_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat

    if message.message_thread_id is None:
        await message.reply_text("نفّذ الأمر داخل Topic في المجموعة.")
        return ConversationHandler.END
    if not (is_owner(user.id) or await has_perm(user.id, MANAGE_GROUPS)):
        await message.reply_text("عذرًا، لا تملك صلاحية ربط المواضيع.")
        return ConversationHandler.END

    conv_push(context, message.message_id)
    thread_id = message.message_thread_id
    context.chat_data["insert_sub"] = {"thread_id": thread_id}

    existing = await get_binding(chat.id, thread_id)
    if existing:
        msg = f"هذا الـTopic مربوط حاليًا بـ: {existing['subject_name']} — {SECTION_LABELS.get(existing['section'], existing['section'])}."
        buttons = [[
            InlineKeyboardButton("تعديل الربط", callback_data="sub_manual"),
            InlineKeyboardButton("إلغاء", callback_data="sub_cancel"),
        ]]
    else:
        msg = (
            "اربط هذا الـTopic بمادة/قسم.\nأرسل: «اسم المادة - القسم» أو «اسم المادة» فقط.\nأمثلة:\n"
            "• دوائر كهربائية (1) - نظري\n• لغة عربية (1)"
        )
        buttons = [[
            InlineKeyboardButton("إدخال يدوي", callback_data="sub_manual"),
            InlineKeyboardButton("إلغاء", callback_data="sub_cancel"),
        ]]
    sent = await message.reply_text(msg, reply_markup=InlineKeyboardMarkup(buttons))
    conv_push(context, sent.message_id)

    return START


async def insert_sub_start_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "sub_manual":
        await query.edit_message_text(
            "أرسل: «اسم المادة - القسم» أو «اسم المادة» فقط."
        )
        return AWAIT_INPUT
    await conv_cleanup(context, context.bot, update.effective_chat.id)
    context.chat_data.pop("insert_sub", None)
    return ConversationHandler.END


async def insert_sub_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conv_push(context, update.message.message_id)
    info = context.chat_data.get("insert_sub")
    if not info:
        return ConversationHandler.END

    text = update.message.text.strip()
    m_full = FULL_RE.match(text)
    if m_full:
        subject = m_full.group("subject").strip()
        sect_label = m_full.group("section")
        section = SECTION_ALIASES[sect_label]
        info.update({
            "subject_name": subject,
            "section": section,
            "theory_only": False,
        })
        theory_label = "لا"
        buttons = [[
            InlineKeyboardButton("تأكيد", callback_data="sub_confirm"),
            InlineKeyboardButton("إلغاء", callback_data="sub_cancel"),
        ]]
        sent = await update.message.reply_text(
            f"سيتم ربط هذا الـTopic بـ:\nالمادة: {subject}\nالقسم: {sect_label}\nنظري فقط: {theory_label}",
            reply_markup=InlineKeyboardMarkup(buttons),
        )
        conv_push(context, sent.message_id)
        return CONFIRM

    m_name = NAME_RE.match(text)
    if m_name:
        subject = m_name.group("subject").strip()
        info.update({"subject_name": subject})
        buttons = [[
            InlineKeyboardButton("نعم نظري فقط", callback_data="sub_t_yes"),
            InlineKeyboardButton("لا", callback_data="sub_t_no"),
        ]]
        sent = await update.message.reply_text(
            "هذه المادة بدون تحديد قسم. هل هي **نظري فقط**؟",
            reply_markup=InlineKeyboardMarkup(buttons),
        )
        conv_push(context, sent.message_id)
        return ASK_THEORY_ONLY

    sent = await update.message.reply_text("صيغة غير صحيحة.")
    conv_push(context, sent.message_id)
    return AWAIT_INPUT


async def insert_sub_theory_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    info = context.chat_data.get("insert_sub")
    if not info:
        return ConversationHandler.END
    theory_only = query.data == "sub_t_yes"
    info.update({"theory_only": theory_only, "section": "theory"})
    theory_label = "نعم" if theory_only else "لا"
    subject = info.get("subject_name", "")
    buttons = [[
        InlineKeyboardButton("تأكيد", callback_data="sub_confirm"),
        InlineKeyboardButton("إلغاء", callback_data="sub_cancel"),
    ]]
    await query.edit_message_text(
        f"سيتم ربط هذا الـTopic بـ:\nالمادة: {subject}\nالقسم: نظري\nنظري فقط: {theory_label}",
        reply_markup=InlineKeyboardMarkup(buttons),
    )
    return CONFIRM


async def insert_sub_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat = update.effective_chat
    info = context.chat_data.get("insert_sub")
    if query.data == "sub_confirm" and info:
        group_info = await get_group_id_by_chat(chat.id)
        if not group_info:
            await query.message.reply_text("اربط المجموعة أولًا عبر /insert_group")
            await conv_cleanup(context, context.bot, chat.id)
            context.chat_data.pop("insert_sub", None)
            return ConversationHandler.END
        _, level_id, term_id = group_info
        subject = await get_or_create_subject(term_id, info["subject_name"], level_id=level_id)
        await set_theory_only(subject.id, info.get("theory_only", False))
        await bind(chat.id, info["thread_id"], subject.id, info["section"])
        logger.info(
            "topic %s in %s bound to subject=%s section=%s",
            info["thread_id"],
            chat.id,
            subject.id,
            info["section"],
        )
        await conv_cleanup(context, context.bot, chat.id)
        await send_ephemeral(context, chat.id, "تم الربط بنجاح.")
    else:
        await conv_cleanup(context, context.bot, chat.id)
        await send_ephemeral(context, chat.id, "تم الإلغاء.")
    context.chat_data.pop("insert_sub", None)
    return ConversationHandler.END


insert_sub_conv = ConversationHandler(
    entry_points=[CommandHandler("insert_sub", insert_sub_start, filters.ChatType.GROUPS)],
    states={
        START: [CallbackQueryHandler(insert_sub_start_choice, pattern="^sub_")],
        AWAIT_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, insert_sub_received)],
        ASK_THEORY_ONLY: [CallbackQueryHandler(insert_sub_theory_choice, pattern="^sub_t_")],
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
