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
    tg_message_id: int, admin_id: int, status: str = "pending"
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
    ingestion_id: int, material_id: int, status: str = "approved"
) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE ingestions SET material_id=?, status=? WHERE id=?",
            (material_id, status, ingestion_id),
        )
        await db.commit()


__all__ = ["get_admin_id_by_tg_user", "insert_ingestion", "attach_material"]

