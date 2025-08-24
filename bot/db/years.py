import aiosqlite

from .base import DB_PATH


async def get_or_create(name: str) -> int:
    """Return id for *name*, inserting a new year if needed."""

    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT id FROM years WHERE name=?", (name,))
        row = await cur.fetchone()
        if row:
            return row[0]
        cur = await db.execute("INSERT INTO years (name) VALUES (?)", (name,))
        await db.commit()
        return cur.lastrowid


__all__ = ["get_or_create"]

