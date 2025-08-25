import logging
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes, filters

from ..db import is_owner
from ..db.materials import get_years, get_lectures_by_year, get_types_for_lecture
from ..navigation import NavigationState
from ..utils.normalize import normalize_section
from ..db.base import DB_PATH
import aiosqlite

logger = logging.getLogger("bot.diag")

async def diag_subject(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not user or not await is_owner(user.id):
        return
    nav = NavigationState(context.user_data)
    subject_id = nav.data.get("subject_id")
    section_code = normalize_section(nav.data.get("section"))
    if not subject_id or not section_code:
        await update.message.reply_text("حدد مادة وقسم عبر التصفح ثم أعد المحاولة.")
        return
    years = await get_years(subject_id, section_code, only_approved=False)
    lines = [f"subject_id={subject_id}, section={section_code}, years={years}"]
    async with aiosqlite.connect(DB_PATH) as db:
        for year in years:
            lectures = await get_lectures_by_year(subject_id, section_code, year)
            lines.append(f"{year}: {len(lectures)} lectures")
            for lec in lectures:
                types = await get_types_for_lecture(
                    subject_id,
                    section_code,
                    year,
                    lec["lecture_no"],
                    only_approved=False,
                )
                lines.append(f"  lec{lec['lecture_no']}: {list(types.keys())}")
            cur = await db.execute(
                """
                SELECT
                    SUM(CASE WHEN i.status='approved' THEN 1 ELSE 0 END),
                    SUM(CASE WHEN i.status='pending' THEN 1 ELSE 0 END)
                FROM materials m
                JOIN ingestions i ON i.material_id = m.id
                JOIN years y ON y.id = m.year_id
                WHERE m.subject_id=? AND m.section=? AND y.name=?
                """,
                (subject_id, section_code, str(year)),
            )
            row = await cur.fetchone()
            approved, pending = row if row else (0, 0)
            lines.append(f"  counts: approved={approved or 0}, pending={pending or 0}")
    await update.message.reply_text("\n".join(lines))


diag_subject_handler = CommandHandler("diag_subject", diag_subject, filters.ChatType.PRIVATE)

__all__ = ["diag_subject_handler"]
