import logging
from telegram.ext import ContextTypes

CONV_MSGS_KEY = "conv_msgs"


logger = logging.getLogger(__name__)


def conv_push(ctx: ContextTypes.DEFAULT_TYPE, msg_id: int) -> None:
    msgs = ctx.chat_data.setdefault(CONV_MSGS_KEY, [])
    msgs.append(msg_id)


async def conv_cleanup(ctx: ContextTypes.DEFAULT_TYPE, bot, chat_id: int) -> None:
    msgs = ctx.chat_data.pop(CONV_MSGS_KEY, [])
    for mid in msgs:
        try:
            await bot.delete_message(chat_id, mid)
        except Exception as e:
            logger.debug("delete failed: %s", e)


__all__ = ["conv_push", "conv_cleanup"]
