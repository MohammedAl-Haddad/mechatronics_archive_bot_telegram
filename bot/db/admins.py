import os

import aiosqlite

from bot.config import ADMIN_USER_IDS, OWNER_TG_ID  # loads environment variables
from .base import DB_PATH


# Permission bit flags
MANAGE_GROUPS = 1 << 0
UPLOAD_CONTENT = 1 << 1
APPROVE_CONTENT = 1 << 2
MANAGE_ADMINS = 1 << 3

PERMISSIONS = {
    MANAGE_GROUPS: "إدارة المجموعات",
    UPLOAD_CONTENT: "رفع المحتوى",
    APPROVE_CONTENT: "مصادقة المحتوى",
    MANAGE_ADMINS: "إدارة المشرفين",
}

# Mask representing full access to all permissions
FULL_ACCESS = (1 << 31) - 1


def is_owner(user_id: int | None) -> bool:
    return OWNER_TG_ID is not None and user_id == OWNER_TG_ID


async def has_perm(user_id: int | None, perm: int) -> bool:
    if is_owner(user_id):
        return True
    if user_id is None:
        return False
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT permissions_mask FROM admins WHERE tg_user_id=? AND is_active=1",
            (user_id,),
        )
        row = await cur.fetchone()
    return bool(row and (row[0] & perm))


async def ensure_owner_full_perms(owner_id: int | None) -> None:
    if owner_id is None:
        return
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO admins (tg_user_id, name, role, permissions_mask, level_scope, is_active)
            VALUES (?, 'OWNER', 'OWNER', ?, 'all', 1)
            ON CONFLICT(tg_user_id) DO UPDATE SET
                name=excluded.name,
                role=excluded.role,
                permissions_mask=excluded.permissions_mask,
                level_scope=excluded.level_scope,
                is_active=1
            """,
            (owner_id, FULL_ACCESS),
        )
        await db.commit()


async def list_admins() -> list[tuple[int, str, int, str]]:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT tg_user_id, name, permissions_mask, level_scope FROM admins WHERE is_active=1"
        )
        return await cur.fetchall()


async def get_admin(tg_user_id: int) -> tuple[int, str, int, str] | None:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT tg_user_id, name, permissions_mask, level_scope FROM admins WHERE tg_user_id=? AND is_active=1",
            (tg_user_id,),
        )
        return await cur.fetchone()


async def add_admin(
    tg_user_id: int, name: str, permissions_mask: int, level_scope: str
) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO admins (tg_user_id, name, role, permissions_mask, level_scope, is_active)
            VALUES (?, ?, 'ADMIN', ?, ?, 1)
            ON CONFLICT(tg_user_id) DO UPDATE SET
                name=excluded.name,
                permissions_mask=excluded.permissions_mask,
                level_scope=excluded.level_scope,
                is_active=1
            """,
            (tg_user_id, name, permissions_mask, level_scope),
        )
        await db.commit()


async def update_admin(
    tg_user_id: int, name: str, permissions_mask: int, level_scope: str
) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE admins SET name=?, permissions_mask=?, level_scope=? WHERE tg_user_id=?",
            (name, permissions_mask, level_scope, tg_user_id),
        )
        await db.commit()


async def remove_admin(tg_user_id: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE admins SET is_active=0 WHERE tg_user_id=?", (tg_user_id,))
        await db.commit()


async def get_admin_with_permissions(tg_user_id: int) -> tuple[int, int] | None:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT id, permissions_mask FROM admins WHERE tg_user_id=? AND is_active=1",
            (tg_user_id,),
        )
        row = await cur.fetchone()

    if row:
        return row[0], row[1]

    if OWNER_TG_ID is not None and tg_user_id == OWNER_TG_ID:
        return 0, FULL_ACCESS

    return None


async def get_admin_id_by_tg_user(tg_user_id: int) -> int | None:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT id FROM admins WHERE tg_user_id=? AND is_active=1",
            (tg_user_id,),
        )
        row = await cur.fetchone()
        return row[0] if row else None


async def is_admin(
    tg_user_id: int, permission: int | None = None, level_id: int | None = None
) -> bool:
    if is_owner(tg_user_id):
        permissions, level_scope = FULL_ACCESS, "all"
    else:
        async with aiosqlite.connect(DB_PATH) as db:
            cur = await db.execute(
                "SELECT permissions_mask, level_scope, is_active FROM admins WHERE tg_user_id=?",
                (tg_user_id,),
            )
            row = await cur.fetchone()

        if row and row[2] == 1:
            permissions, level_scope = row[0], row[1]
        else:
            return tg_user_id in ADMIN_USER_IDS

    if permission and not (permissions & permission):
        return False
    if level_id is not None and level_scope not in ("all", str(level_id)):
        return False
    return True


__all__ = [
    "MANAGE_GROUPS",
    "UPLOAD_CONTENT",
    "APPROVE_CONTENT",
    "MANAGE_ADMINS",
    "FULL_ACCESS",
    "PERMISSIONS",
    "list_admins",
    "get_admin",
    "add_admin",
    "update_admin",
    "remove_admin",
    "get_admin_with_permissions",
    "get_admin_id_by_tg_user",
    "is_owner",
    "has_perm",
    "ensure_owner_full_perms",
    "is_admin",
]

