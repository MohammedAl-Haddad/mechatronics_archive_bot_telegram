from __future__ import annotations

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CommandHandler,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from bot.db import (
    is_admin,
    MANAGE_ADMINS,
    list_admins,
    add_admin,
    get_admin,
    update_admin,
    remove_admin,
)
from bot.keyboards import build_permissions_keyboard


MENU, ADD_ID, ADD_NAME, ADD_PERMS, ADD_LEVEL, EDIT_ID, EDIT_NAME, EDIT_PERMS, EDIT_LEVEL, REMOVE_ID = range(10)


async def admins_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user or not await is_admin(user.id, MANAGE_ADMINS):
        await update.message.reply_text("عذرًا، لا تملك صلاحية هذا الأمر.")
        return ConversationHandler.END

    rows = await list_admins()
    lines = ["المشرفون الحاليون:"]
    for tg_id, name, _mask, _scope in rows:
        lines.append(f"- {name or tg_id} ({tg_id})")
    buttons = [
        [InlineKeyboardButton("➕ إضافة", callback_data="adm_add")],
        [InlineKeyboardButton("✏️ تعديل", callback_data="adm_edit")],
        [InlineKeyboardButton("🗑️ إزالة", callback_data="adm_remove")],
    ]
    await update.message.reply_text(
        "\n".join(lines), reply_markup=InlineKeyboardMarkup(buttons)
    )
    return MENU


async def admins_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data == "adm_add":
        await query.edit_message_text("أرسل معرف المستخدم (tg_user_id):")
        return ADD_ID
    if data == "adm_edit":
        await query.edit_message_text("أرسل معرف المستخدم لتعديله:")
        return EDIT_ID
    if data == "adm_remove":
        await query.edit_message_text("أرسل معرف المستخدم لإزالته:")
        return REMOVE_ID
    return ConversationHandler.END


async def add_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        tg_id = int(update.message.text.strip())
    except ValueError:
        await update.message.reply_text("معرف غير صالح، حاول مرة أخرى.")
        return ADD_ID
    context.user_data["new_admin"] = {"tg_user_id": tg_id, "perm_mask": 0}
    await update.message.reply_text("أرسل اسم المشرف:")
    return ADD_NAME


async def add_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    info = context.user_data["new_admin"]
    info["name"] = update.message.text.strip()
    kb = build_permissions_keyboard(info["perm_mask"])
    await update.message.reply_text("اختر الصلاحيات:", reply_markup=kb)
    return ADD_PERMS


async def add_perms(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    info = context.user_data["new_admin"]
    data = query.data
    if data.startswith("perm_"):
        flag = int(data.split("_", 1)[1])
        info["perm_mask"] ^= flag
        await query.edit_message_reply_markup(
            build_permissions_keyboard(info["perm_mask"])
        )
        return ADD_PERMS
    if data == "perm_done":
        await query.edit_message_text("أرسل نطاق المستوى (مثال: all أو رقم المستوى):")
        return ADD_LEVEL
    return ConversationHandler.END


async def add_level(update: Update, context: ContextTypes.DEFAULT_TYPE):
    info = context.user_data["new_admin"]
    info["level_scope"] = update.message.text.strip()
    await add_admin(
        info["tg_user_id"],
        info["name"],
        info["perm_mask"],
        info["level_scope"],
    )
    await update.message.reply_text("تم الحفظ.")
    context.user_data.pop("new_admin", None)
    return ConversationHandler.END


async def edit_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        tg_id = int(update.message.text.strip())
    except ValueError:
        await update.message.reply_text("معرف غير صالح، حاول مرة أخرى.")
        return EDIT_ID
    row = await get_admin(tg_id)
    if row is None:
        await update.message.reply_text("المشرف غير موجود.")
        return ConversationHandler.END
    _tg, name, mask, scope = row
    context.user_data["edit_admin"] = {
        "tg_user_id": tg_id,
        "name": name or "",
        "perm_mask": mask,
        "level_scope": scope,
    }
    await update.message.reply_text(f"الاسم الحالي: {name or ''}\nأرسل الاسم الجديد:")
    return EDIT_NAME


async def edit_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    info = context.user_data["edit_admin"]
    info["name"] = update.message.text.strip()
    kb = build_permissions_keyboard(info["perm_mask"])
    await update.message.reply_text("حدّث الصلاحيات:", reply_markup=kb)
    return EDIT_PERMS


async def edit_perms(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    info = context.user_data["edit_admin"]
    data = query.data
    if data.startswith("perm_"):
        flag = int(data.split("_", 1)[1])
        info["perm_mask"] ^= flag
        await query.edit_message_reply_markup(
            build_permissions_keyboard(info["perm_mask"])
        )
        return EDIT_PERMS
    if data == "perm_done":
        await query.edit_message_text(
            f"النطاق الحالي: {info['level_scope']}\nأرسل النطاق الجديد:"
        )
        return EDIT_LEVEL
    return ConversationHandler.END


async def edit_level(update: Update, context: ContextTypes.DEFAULT_TYPE):
    info = context.user_data["edit_admin"]
    info["level_scope"] = update.message.text.strip()
    await update_admin(
        info["tg_user_id"],
        info["name"],
        info["perm_mask"],
        info["level_scope"],
    )
    await update.message.reply_text("تم التحديث.")
    context.user_data.pop("edit_admin", None)
    return ConversationHandler.END


async def remove_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        tg_id = int(update.message.text.strip())
    except ValueError:
        await update.message.reply_text("معرف غير صالح، حاول مرة أخرى.")
        return REMOVE_ID
    await remove_admin(tg_id)
    await update.message.reply_text("تمت الإزالة.")
    return ConversationHandler.END


admins_conv = ConversationHandler(
    entry_points=[
        CommandHandler("admins", admins_start),
        MessageHandler(filters.Regex("^👤 إدارة المشرفين$"), admins_start),
    ],
    states={
        MENU: [CallbackQueryHandler(admins_menu, pattern="^adm_")],
        ADD_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_id)],
        ADD_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_name)],
        ADD_PERMS: [CallbackQueryHandler(add_perms, pattern="^perm_")],
        ADD_LEVEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_level)],
        EDIT_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_id)],
        EDIT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_name)],
        EDIT_PERMS: [CallbackQueryHandler(edit_perms, pattern="^perm_")],
        EDIT_LEVEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_level)],
        REMOVE_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, remove_id)],
    },
    fallbacks=[],
)


__all__ = ["admins_conv"]

