from __future__ import annotations

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
    MANAGE_ADMINS,
    list_admins,
    get_admin,
    add_admin,
    update_admin,
    remove_admin,
    PERMISSIONS,
)
from bot.keyboards import build_permissions_keyboard
from bot.utils.conv import conv_push, conv_cleanup
from bot.utils.telegram import send_ephemeral


logger = logging.getLogger("bot.admins")

MENU, ADD_ID, PERMS, REMOVE_CONFIRM = range(4)
PAGE_SIZE = 5


def _perm_summary(mask: int) -> str:
    return "".join("✅" if mask & flag else "❌" for flag in PERMISSIONS)


async def _send_list(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    page: int = 0,
    new: bool = False,
) -> None:
    admins = await list_admins()
    total = len(admins)
    start = page * PAGE_SIZE
    page_rows = admins[start : start + PAGE_SIZE]

    lines = ["إدارة المشرفين:"]
    for tg_id, name, mask, _scope in page_rows:
        lines.append(f"- {name or tg_id} ({tg_id}) {_perm_summary(mask)}")
    if total > PAGE_SIZE:
        lines.append("القائمة طويلة — استخدم الأسهم للتنقل.")
    text = "\n".join(lines)

    keyboard = []
    for tg_id, name, mask, _ in page_rows:
        if is_owner(tg_id):
            keyboard.append([InlineKeyboardButton(f"{name or tg_id}", callback_data="noop")])
        else:
            keyboard.append(
                [
                    InlineKeyboardButton("✏️ تعديل", callback_data=f"adm_edit:{tg_id}"),
                    InlineKeyboardButton("🗑️ إزالة", callback_data=f"adm_del:{tg_id}"),
                ]
            )
    nav = []
    if start > 0:
        nav.append(InlineKeyboardButton("⬅️", callback_data=f"adm_page:{page - 1}"))
    if start + PAGE_SIZE < total:
        nav.append(InlineKeyboardButton("➡️", callback_data=f"adm_page:{page + 1}"))
    if nav:
        keyboard.append(nav)
    keyboard.append(
        [
            InlineKeyboardButton("➕ إضافة", callback_data="adm_add"),
            InlineKeyboardButton("⟳ تحديث", callback_data=f"adm_page:{page}"),
            InlineKeyboardButton("إغلاق", callback_data="adm_close"),
        ]
    )
    markup = InlineKeyboardMarkup(keyboard)

    if new or not update.callback_query:
        await update.effective_chat.send_message(text, reply_markup=markup)
    else:
        try:
            await update.callback_query.edit_message_text(text, reply_markup=markup)
        except Exception as e:  # pragma: no cover - safety
            logger.debug("edit failed: %s", e)
            await update.effective_chat.send_message(text, reply_markup=markup)
    context.user_data["adm_page"] = page


async def admins_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user or not (is_owner(user.id) or await has_perm(user.id, MANAGE_ADMINS)):
        await update.effective_message.reply_text("لا تملك صلاحية إدارة المشرفين.")
        return ConversationHandler.END
    await _send_list(update, context)
    return MENU


async def menu_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data == "adm_add":
        msg = await query.edit_message_text(
            "أرسل رقم Telegram ID للمستخدم المراد منحه صلاحيات."
        )
        conv_push(context, msg.message_id)
        return ADD_ID
    if data.startswith("adm_edit:"):
        tg_id = int(data.split(":", 1)[1])
        if is_owner(tg_id):
            await query.answer("لا يمكن تعديل/إزالة مالك البوت.", show_alert=True)
            return MENU
        row = await get_admin(tg_id)
        mask = row[2] if row else 0
        context.user_data.update({"adm_target": tg_id, "adm_mask": mask, "mode": "edit"})
        msg = await query.edit_message_text(
            "حدّد الصلاحيات:", reply_markup=build_permissions_keyboard(mask)
        )
        conv_push(context, msg.message_id)
        return PERMS
    if data.startswith("adm_del:"):
        tg_id = int(data.split(":", 1)[1])
        if is_owner(tg_id):
            await query.answer("لا يمكن تعديل/إزالة مالك البوت.", show_alert=True)
            return MENU
        context.user_data["adm_target"] = tg_id
        buttons = [[InlineKeyboardButton("نعم", callback_data="rm_yes"), InlineKeyboardButton("لا", callback_data="rm_no")]]
        msg = await query.edit_message_text(
            "تأكيد إزالة هذا المشرف؟", reply_markup=InlineKeyboardMarkup(buttons)
        )
        conv_push(context, msg.message_id)
        return REMOVE_CONFIRM
    if data.startswith("adm_page:"):
        page = int(data.split(":", 1)[1])
        await _send_list(update, context, page)
        return MENU
    if data == "adm_close":
        await query.edit_message_text("تم الإغلاق.")
        return ConversationHandler.END
    return MENU


async def add_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conv_push(context, update.message.message_id)
    try:
        tg_id = int(update.message.text.strip())
    except ValueError:
        sent = await update.message.reply_text("معرف غير صالح، حاول مرة أخرى.")
        conv_push(context, sent.message_id)
        return ADD_ID
    context.user_data.update({"adm_target": tg_id, "adm_mask": 0, "mode": "add"})
    msg = await update.message.reply_text(
        "حدّد الصلاحيات:", reply_markup=build_permissions_keyboard(0)
    )
    conv_push(context, msg.message_id)
    return PERMS


async def perms_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    mask = context.user_data.get("adm_mask", 0)
    if data.startswith("perm_") and data not in ("perm_save", "perm_cancel"):
        flag = int(data.split("_", 1)[1])
        mask ^= flag
        context.user_data["adm_mask"] = mask
        await query.edit_message_reply_markup(build_permissions_keyboard(mask))
        return PERMS
    if data == "perm_save":
        tg_id = context.user_data.get("adm_target")
        mask = context.user_data.get("adm_mask", 0)
        mode = context.user_data.get("mode")
        if mode == "edit":
            row = await get_admin(tg_id)
            name = row[1] if row else ""
            scope = row[3] if row else "all"
            await update_admin(tg_id, name, mask, scope)
        else:
            await add_admin(tg_id, "", mask, "all")
        await conv_cleanup(context, context.bot, update.effective_chat.id)
        await send_ephemeral(context, update.effective_chat.id, "تم الحفظ بنجاح.")
        logger.info("admin %s set perms %s by %s", tg_id, mask, update.effective_user.id)
        await _send_list(update, context, context.user_data.get("adm_page", 0), new=True)
        return MENU
    if data == "perm_cancel":
        await conv_cleanup(context, context.bot, update.effective_chat.id)
        await _send_list(update, context, context.user_data.get("adm_page", 0), new=True)
        return MENU
    return PERMS


async def remove_confirm_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "rm_yes":
        tg_id = context.user_data.get("adm_target")
        if tg_id and not is_owner(tg_id):
            await remove_admin(tg_id)
        await conv_cleanup(context, context.bot, update.effective_chat.id)
        await send_ephemeral(context, update.effective_chat.id, "تمت الإزالة.")
        logger.info("admin %s removed by %s", tg_id, update.effective_user.id)
        await _send_list(update, context, context.user_data.get("adm_page", 0), new=True)
        return MENU
    await conv_cleanup(context, context.bot, update.effective_chat.id)
    await _send_list(update, context, context.user_data.get("adm_page", 0), new=True)
    return MENU


admins_conv = ConversationHandler(
    entry_points=[
        CommandHandler("admins", admins_start, filters.ChatType.PRIVATE),
        MessageHandler(
            filters.ChatType.PRIVATE & filters.Regex("^👤 إدارة المشرفين$"),
            admins_start,
        ),
    ],
    states={
        MENU: [CallbackQueryHandler(menu_cb, pattern="^adm_")],
        ADD_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_id)],
        PERMS: [CallbackQueryHandler(perms_cb, pattern="^perm_")],
        REMOVE_CONFIRM: [CallbackQueryHandler(remove_confirm_cb, pattern="^rm_")],
    },
    fallbacks=[],
)


__all__ = ["admins_conv"]

