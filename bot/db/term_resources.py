import aiosqlite

from .base import DB_PATH


async def insert_term_resource(
    term_id: int,
    kind: str,
    storage_chat_id: int,
    storage_msg_id: int,
):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            """
            INSERT INTO term_resources (term_id, kind, tg_storage_chat_id, tg_storage_msg_id)
            VALUES (?, ?, ?, ?)
            """,
            (term_id, kind, storage_chat_id, storage_msg_id),
        )
        await db.commit()
        return cur.lastrowid


async def get_latest_term_resource(term_id: int, kind: str):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            """
            SELECT tg_storage_chat_id, tg_storage_msg_id
            FROM term_resources
            WHERE term_id=? AND kind=?
            ORDER BY id DESC LIMIT 1
            """,
            (term_id, kind),
        )
        return await cur.fetchone()


__all__ = ["insert_term_resource", "get_latest_term_resource"]

