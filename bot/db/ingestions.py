import aiosqlite

from .base import DB_PATH


# Permission bit flags
UPLOAD_CONTENT = 1 << 0


async def get_admin_with_permissions(tg_user_id: int) -> tuple[int, int] | None:
    """Return admin id and permission mask for *tg_user_id*.

    Only active admins are considered.  ``None`` is returned if the user is not
    registered as an admin.
    """

    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT id, permissions_mask FROM admins WHERE tg_user_id=? AND is_active=1",
            (tg_user_id,),
        )
        row = await cur.fetchone()
        return (row[0], row[1]) if row else None


async def get_admin_id_by_tg_user(tg_user_id: int) -> int | None:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT id FROM admins WHERE tg_user_id=? AND is_active=1",
            (tg_user_id,),
        )
        row = await cur.fetchone()
        return row[0] if row else None


async def insert_ingestion(
    tg_message_id: int, admin_id: int, status: str = "pending",
) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            """
            INSERT INTO ingestions (tg_message_id, admin_id, status)
            VALUES (?, ?, ?)
            """,
            (tg_message_id, admin_id, status),
        )
        await db.commit()
        return cur.lastrowid


async def attach_material(
    ingestion_id: int, material_id: int, status: str = "approved",
) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE ingestions SET material_id=?, status=? WHERE id=?",
            (material_id, status, ingestion_id),
        )
        await db.commit()


async def list_pending_ingestions() -> list[tuple[int, int, int]]:
    """Return pending ingestions with source message identifiers."""

    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            """
            SELECT i.id, m.source_chat_id, m.source_message_id
            FROM ingestions i
            JOIN materials m ON m.id = i.material_id
            WHERE i.status='pending'
            ORDER BY i.created_at
            """,
        )
        return await cur.fetchall()


async def get_ingestion_material(
    ingestion_id: int,
) -> tuple[int, int, int] | None:
    """Fetch material information linked to *ingestion_id*.

    Returns a tuple of ``(material_id, source_chat_id, source_message_id)`` or
    ``None`` if the ingestion does not exist.
    """

    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            """
            SELECT m.id, m.source_chat_id, m.source_message_id
            FROM ingestions i
            JOIN materials m ON m.id = i.material_id
            WHERE i.id=?
            """,
            (ingestion_id,),
        )
        row = await cur.fetchone()
        return (row[0], row[1], row[2]) if row else None


async def update_ingestion_status(ingestion_id: int, status: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE ingestions SET status=? WHERE id=?",
            (status, ingestion_id),
        )
        await db.commit()


async def delete_ingestion(ingestion_id: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM ingestions WHERE id=?", (ingestion_id,))
        await db.commit()


async def delete_old_pending_ingestions(hours: int = 24) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            """
            DELETE FROM ingestions
            WHERE status='pending' AND created_at < datetime('now', ?)
            """,
            (f'-{hours} hours',),
        )
        await db.commit()
        return cur.rowcount


__all__ = [
    "UPLOAD_CONTENT",
    "get_admin_id_by_tg_user",
    "get_admin_with_permissions",
    "insert_ingestion",
    "attach_material",
    "list_pending_ingestions",
    "get_ingestion_material",
    "update_ingestion_status",
    "delete_ingestion",
    "delete_old_pending_ingestions",
]

