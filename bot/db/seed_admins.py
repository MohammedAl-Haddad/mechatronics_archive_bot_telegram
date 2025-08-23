"""Utility to seed admin accounts.

Currently only supports inserting the bot owner with full permissions.
"""

from __future__ import annotations

import os

import aiosqlite
from dotenv import load_dotenv

from .base import DB_PATH

ENV_FILE = ".env"

ROLE_OWNER = "OWNER"
FULL_ACCESS = 0xFFFFFFFF


async def seed_owner() -> None:
    """Create or update the bot owner in the admins table.

    The Telegram user id is read from ``OWNER_TG_ID`` environment variable.
    The operation is idempotent: running it multiple times will not create
    duplicate records and will ensure the owner stays active with full access.
    """

    load_dotenv(ENV_FILE)
    owner_id = os.getenv("OWNER_TG_ID")
    if not owner_id:
        raise RuntimeError("OWNER_TG_ID is missing in environment")

    tg_user_id = int(owner_id)

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO admins (tg_user_id, role, permissions_mask, is_active)
            VALUES (?, ?, ?, 1)
            ON CONFLICT(tg_user_id) DO UPDATE SET
                role=excluded.role,
                permissions_mask=excluded.permissions_mask,
                is_active=1
            """,
            (tg_user_id, ROLE_OWNER, FULL_ACCESS),
        )
        await db.commit()


__all__ = ["seed_owner"]

