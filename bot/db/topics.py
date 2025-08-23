import aiosqlite

from .base import DB_PATH


async def is_admin(tg_user_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT 1 FROM admins WHERE tg_user_id=? AND is_active=1", (tg_user_id,)
        )
        return (await cur.fetchone()) is not None


async def get_group_id_by_chat(tg_chat_id: int) -> int | None:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT id FROM groups WHERE tg_chat_id=?", (tg_chat_id,)
        )
        row = await cur.fetchone()
        return row[0] if row else None


async def get_subject_by_name(name: str) -> tuple[int, str] | None:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT id, sections_mode FROM subjects WHERE name=?", (name,)
        )
        row = await cur.fetchone()
        return (row[0], row[1]) if row else None


async def upsert_topic(
    group_id: int, tg_topic_id: int, subject_id: int, section: str
) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO topics (group_id, tg_topic_id, subject_id, section)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(group_id, tg_topic_id) DO UPDATE SET
                subject_id=excluded.subject_id,
                section=excluded.section
            """,
            (group_id, tg_topic_id, subject_id, section),
        )
        await db.commit()


__all__ = [
    "is_admin",
    "get_group_id_by_chat",
    "get_subject_by_name",
    "upsert_topic",
]
