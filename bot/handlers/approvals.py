from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes

from ..db import (
    is_admin,
    list_pending_ingestions,
    update_ingestion_status,
)
from ..db.materials import insert_material, ensure_year_id, ensure_lecturer_id
from ..parser.hashtags import parse_hashtags


def _extract_hashtags(message) -> list[str]:
    text = message.text or message.caption or ""
    entities = message.entities or message.caption_entities or []
    tags: list[str] = []
    for ent in entities:
        if ent.type == "hashtag":
            tags.append(text[ent.offset : ent.offset + ent.length])
    return tags


async def list_pending(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not user or not await is_admin(user.id):
        return
    pending = await list_pending_ingestions()
    if not pending:
        await update.message.reply_text("لا توجد رسائل معلقة.")
        return
    for ingestion_id, msg_id, tg_user_id in pending:
        buttons = [[
            InlineKeyboardButton(
                "Approve",
                callback_data=f"appr:{ingestion_id}:{tg_user_id}:{msg_id}",
            ),
            InlineKeyboardButton(
                "Reject",
                callback_data=f"rej:{ingestion_id}:{tg_user_id}:{msg_id}",
            ),
        ]]
        await context.bot.copy_message(
            chat_id=update.effective_chat.id,
            from_chat_id=tg_user_id,
            message_id=msg_id,
            reply_markup=InlineKeyboardMarkup(buttons),
        )


async def handle_decision(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    action, ing_id, tg_user_id, msg_id = query.data.split(":")
    ingestion_id = int(ing_id)
    tg_user_id = int(tg_user_id)
    msg_id = int(msg_id)
    if action == "appr":
        tags = _extract_hashtags(query.message)
        info = parse_hashtags(tags)
        category = info.get("category") or "lecture"
        title = info.get("title") or "بدون عنوان"
        year_id = None
        if info.get("year"):
            year_id = await ensure_year_id(info["year"])
        lecturer_id = None
        if info.get("lecturer"):
            lecturer_id = await ensure_lecturer_id(info["lecturer"])
        try:
            await insert_material(
                0,
                "theory",
                category,
                title,
                year_id=year_id,
                lecturer_id=lecturer_id,
                source_chat_id=tg_user_id,
                source_message_id=msg_id,
            )
        except Exception:
            pass
        await update_ingestion_status(ingestion_id, "approved")
        await query.edit_message_reply_markup(reply_markup=None)
    else:
        await update_ingestion_status(ingestion_id, "rejected")
        await query.edit_message_reply_markup(reply_markup=None)
        try:
            await context.bot.send_message(tg_user_id, "تم رفض رسالتك.")
        except Exception:
            pass


approvals_handler = CommandHandler("approvals", list_pending)
approval_callback = CallbackQueryHandler(handle_decision, pattern="^(appr|rej):")


__all__ = ["approvals_handler", "approval_callback"]

