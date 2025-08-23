import aiosqlite

from .base import DB_PATH


async def get_group_info(tg_chat_id: int) -> tuple[int, int] | None:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT level_id, term_id FROM groups WHERE tg_chat_id=?",
            (tg_chat_id,),
        )
        row = await cur.fetchone()
        return (row[0], row[1]) if row else None


async def upsert_group(tg_chat_id: int, level_id: int, term_id: int, title: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO groups (tg_chat_id, title, level_id, term_id)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(tg_chat_id) DO UPDATE SET
                title=excluded.title,
                level_id=excluded.level_id,
                term_id=excluded.term_id
            """,
            (tg_chat_id, title, level_id, term_id),
        )
        await db.commit()


__all__ = ["get_group_info", "upsert_group"]
