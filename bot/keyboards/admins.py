from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from bot.db.admins import PERMISSIONS


def build_permissions_keyboard(mask: int) -> InlineKeyboardMarkup:
    """Create an inline keyboard to toggle available admin permissions."""
    buttons = []
    for flag, label in PERMISSIONS.items():
        prefix = "✅" if mask & flag else "❌"
        buttons.append([InlineKeyboardButton(f"{prefix} {label}", callback_data=f"perm_{flag}")])
    buttons.append([InlineKeyboardButton("تم", callback_data="perm_done")])
    return InlineKeyboardMarkup(buttons)


__all__ = ["build_permissions_keyboard"]

