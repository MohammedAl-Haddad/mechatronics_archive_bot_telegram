import aiosqlite

from .base import DB_PATH


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
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            """
            SELECT i.id, i.tg_message_id, a.tg_user_id
            FROM ingestions i
            JOIN admins a ON a.id = i.admin_id
            WHERE i.status='pending'
            ORDER BY i.created_at
            """,
        )
        return await cur.fetchall()


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
    "get_admin_id_by_tg_user",
    "insert_ingestion",
    "attach_material",
    "list_pending_ingestions",
    "update_ingestion_status",
    "delete_ingestion",
    "delete_old_pending_ingestions",
]

