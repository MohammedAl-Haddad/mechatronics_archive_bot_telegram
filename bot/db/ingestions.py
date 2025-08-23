import aiosqlite

from .base import DB_PATH


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
    """Fetch material information linked to *ingestion_id*."""

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
    "insert_ingestion",
    "attach_material",
    "list_pending_ingestions",
    "get_ingestion_material",
    "update_ingestion_status",
    "delete_ingestion",
    "delete_old_pending_ingestions",
]

