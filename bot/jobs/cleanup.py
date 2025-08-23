from telegram.ext import ContextTypes

from ..db.ingestions import delete_old_pending_ingestions


async def purge_temp_archives(context: ContextTypes.DEFAULT_TYPE) -> None:
    await delete_old_pending_ingestions()


__all__ = ["purge_temp_archives"]

