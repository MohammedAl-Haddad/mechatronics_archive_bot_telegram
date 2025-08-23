import os

import aiosqlite
from dotenv import load_dotenv

from bot.config.constants import ENV_FILE
from .base import DB_PATH

FULL_ACCESS = 0xFFFFFFFF


async def seed_owner() -> None:
    """Seed database with OWNER admin based on OWNER_TG_ID env variable."""
    load_dotenv(ENV_FILE)
    owner_tg_id = os.getenv("OWNER_TG_ID")
    if not owner_tg_id:
        raise RuntimeError("OWNER_TG_ID is missing in environment")
    tg_id = int(owner_tg_id)

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS admins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tg_user_id INTEGER NOT NULL UNIQUE,
                username TEXT,
                role TEXT NOT NULL DEFAULT 'ADMIN',
                permissions_mask INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        await db.execute(
            """
            INSERT OR IGNORE INTO admins (tg_user_id, role, permissions_mask)
            VALUES (?, 'OWNER', ?)
            """,
            (tg_id, FULL_ACCESS),
        )
        await db.execute(
            "UPDATE admins SET role='OWNER', permissions_mask=? WHERE tg_user_id=?",
            (FULL_ACCESS, tg_id),
        )
        await db.commit()


__all__ = ["seed_owner", "FULL_ACCESS"]
