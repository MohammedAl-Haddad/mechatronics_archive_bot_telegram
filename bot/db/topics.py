import os

import aiosqlite

from bot.config import ADMIN_USER_IDS  # loads environment variables
from .base import DB_PATH

_owner = os.getenv("OWNER_TG_ID")
OWNER_TG_ID = int(_owner) if _owner and _owner.strip().isdigit() else None


async def is_admin(tg_user_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT 1 FROM admins WHERE tg_user_id=? AND is_active=1", (tg_user_id,)
        )
        if (await cur.fetchone()) is not None:
            return True

    if OWNER_TG_ID is not None and tg_user_id == OWNER_TG_ID:
        return True
    return tg_user_id in ADMIN_USER_IDS


async def get_group_id_by_chat(tg_chat_id: int) -> tuple[int, int, int] | None:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT id, level_id, term_id FROM groups WHERE tg_chat_id=?",
            (tg_chat_id,),
        )
        row = await cur.fetchone()
        return (row[0], row[1], row[2]) if row else None


async def get_subject_by_name(name: str) -> tuple[int, str] | None:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT id, sections_mode FROM subjects WHERE name=?", (name,)
        )
        row = await cur.fetchone()
        return (row[0], row[1]) if row else None


async def get_topic_link(
    group_id: int, tg_topic_id: int
) -> tuple[int, str, str] | None:
    """Return existing topic linkage if present.

    Returns a tuple of (subject_id, subject_name, section)
    or ``None`` if the topic is not linked yet.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            """
            SELECT t.subject_id, s.name, t.section
            FROM topics t
            JOIN subjects s ON s.id = t.subject_id
            WHERE t.group_id=? AND t.tg_topic_id=?
            """,
            (group_id, tg_topic_id),
        )
        row = await cur.fetchone()
        return (row[0], row[1], row[2]) if row else None


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
    "get_topic_link",
    "upsert_topic",
]
