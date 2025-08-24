from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes, filters
import logging

from ..config import ARCHIVE_CHANNEL_ID
from ..db import (
    is_admin,
    APPROVE_CONTENT,
    list_pending_ingestions,
    get_ingestion_material,
    update_ingestion_status,
)
from ..db.materials import update_material_storage
from ..utils.telegram import (
    get_file_unique_id_from_message as _get_file_unique_id_from_message,  # noqa: F401
)


logger = logging.getLogger("bot.approvals")

async def list_pending(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not user or not await is_admin(user.id, APPROVE_CONTENT):
        await update.message.reply_text("عذرًا، لا تملك صلاحية هذا الأمر.")
        return
    pending = await list_pending_ingestions()
    if not pending:
        await update.message.reply_text("لا توجد رسائل معلقة.")
        return
    await update.message.reply_text("الرسائل المعلقة:")
    for ingestion_id, chat_id, msg_id, action_type in pending:
        approve_label = "Approve استبدال" if action_type == "replace" else "Approve"
        buttons = [[
            InlineKeyboardButton(approve_label, callback_data=f"appr:{ingestion_id}"),
            InlineKeyboardButton("Reject", callback_data=f"rej:{ingestion_id}"),
        ]]
        await context.bot.copy_message(
            chat_id=update.effective_chat.id,
            from_chat_id=chat_id,
            message_id=msg_id,
            reply_markup=InlineKeyboardMarkup(buttons),
        )


async def handle_decision(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user = update.effective_user
    if not user or not await is_admin(user.id, APPROVE_CONTENT):
        await query.edit_message_reply_markup(reply_markup=None)
        return
    action, ing_id = query.data.split(":")
    ingestion_id = int(ing_id)
    info = await get_ingestion_material(ingestion_id)
    if info is None:
        await query.edit_message_reply_markup(reply_markup=None)
        return
    (
        material_id,
        src_chat_id,
        src_msg_id,
        new_msg_id,
        action_type,
        file_unique_id,
        storage_chat_id,
        storage_msg_id,
    ) = info
    if action == "appr":
        if action_type == "replace":
            copied = await context.bot.copy_message(
                chat_id=ARCHIVE_CHANNEL_ID,
                from_chat_id=src_chat_id,
                message_id=new_msg_id,
            )
            await update_material_storage(
                material_id, ARCHIVE_CHANNEL_ID, copied.message_id, file_unique_id
            )
            if file_unique_id:
                logger.debug(
                    "replace #%s used file_unique_id", ingestion_id
                )
            else:
                logger.debug("replace #%s without file_unique_id", ingestion_id)
            if storage_chat_id and storage_msg_id:
                try:
                    await context.bot.delete_message(
                        storage_chat_id, storage_msg_id
                    )
                except Exception as e:
                    logger.warning("delete old message failed: %s", e)
            await update_ingestion_status(ingestion_id, "approved")
            await context.bot.send_message(
                chat_id=src_chat_id,
                text="تم الاستبدال بنجاح وأُضيفت النسخة الجديدة إلى الأرشيف.",
                reply_to_message_id=new_msg_id,
            )
            logger.info(
                "replace approved #%s by %s", ingestion_id, user.id
            )
        else:
            copied = await context.bot.copy_message(
                chat_id=ARCHIVE_CHANNEL_ID,
                from_chat_id=src_chat_id,
                message_id=src_msg_id,
            )
            await update_material_storage(
                material_id, ARCHIVE_CHANNEL_ID, copied.message_id, file_unique_id
            )
            await update_ingestion_status(ingestion_id, "approved")
            await context.bot.send_message(
                chat_id=src_chat_id,
                text="تمت الموافقة وأُضيف المحتوى إلى الأرشيف.",
                reply_to_message_id=new_msg_id,
            )
            logger.info("approved #%s by %s", ingestion_id, user.id)
    else:
        await update_ingestion_status(ingestion_id, "rejected")
        msg = "تم رفض الاستبدال." if action_type == "replace" else "تم رفض المحتوى."
        await context.bot.send_message(
            chat_id=src_chat_id,
            text=msg,
            reply_to_message_id=new_msg_id,
        )
        logger.info("rejected #%s by %s", ingestion_id, user.id)
    await query.edit_message_reply_markup(reply_markup=None)


approvals_handler = CommandHandler(
    "approvals", list_pending, filters.ChatType.PRIVATE
)
approval_callback = CallbackQueryHandler(handle_decision, pattern="^(appr|rej):")


__all__ = ["approvals_handler", "approval_callback"]

