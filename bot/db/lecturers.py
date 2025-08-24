import aiosqlite

from .base import DB_PATH


async def get_or_create(name: str, role: str = "lecturer") -> int:
    """Return id for lecturer *name*, inserting if necessary."""

    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT id FROM lecturers WHERE name=?", (name,))
        row = await cur.fetchone()
        if row:
            return row[0]
        cur = await db.execute(
            "INSERT INTO lecturers (name, role) VALUES (?, ?)",
            (name, role),
        )
        await db.commit()
        return cur.lastrowid


__all__ = ["get_or_create"]

