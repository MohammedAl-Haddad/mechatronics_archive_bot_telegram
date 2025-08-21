import os
import aiosqlite

DB_PATH = "database/archive.db"


async def init_db() -> None:
    """Ensure database folder exists and execute schema/init.sql once."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        with open("database/init.sql", "r", encoding="utf-8") as f:
            await db.executescript(f.read())
        await db.commit()
