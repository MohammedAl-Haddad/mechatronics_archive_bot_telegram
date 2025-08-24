import aiosqlite

from .base import DB_PATH


async def get_group_id_by_chat(tg_chat_id: int) -> tuple[int, int, int] | None:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT id, level_id, term_id FROM groups WHERE tg_chat_id=?",
            (tg_chat_id,),
        )
        row = await cur.fetchone()
        return (row[0], row[1], row[2]) if row else None


async def get_binding(tg_chat_id: int, tg_topic_id: int) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            """
            SELECT t.subject_id, s.name, t.section
            FROM topics t
            JOIN groups g ON g.id = t.group_id
            JOIN subjects s ON s.id = t.subject_id
            WHERE g.tg_chat_id=? AND t.tg_topic_id=?
            """,
            (tg_chat_id, tg_topic_id),
        )
        row = await cur.fetchone()
        if row:
            return {"subject_id": row[0], "subject_name": row[1], "section": row[2]}
        return None


async def bind(tg_chat_id: int, tg_topic_id: int, subject_id: int, section: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT id FROM groups WHERE tg_chat_id=?",
            (tg_chat_id,),
        )
        row = await cur.fetchone()
        if row is None:
            raise ValueError("group not found")
        group_id = row[0]
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


__all__ = ["get_group_id_by_chat", "get_binding", "bind"]
