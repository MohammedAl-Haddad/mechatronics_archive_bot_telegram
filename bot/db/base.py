import os
import aiosqlite

DB_PATH = "database/archive.db"
DB_VERSION = 2


async def init_db() -> None:
    """Ensure database directory exists and migrate database to latest version."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    await migrate_if_needed()


async def migrate_if_needed() -> None:
    """Upgrade database schema to the latest version if needed."""
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("PRAGMA user_version")
        row = await cur.fetchone()
        user_version = row[0] if row else 0

        if user_version == 0:
            # Fresh database initialization
            with open("database/init.sql", "r", encoding="utf-8") as f:
                await db.executescript(f.read())
            await db.execute(f"PRAGMA user_version={DB_VERSION}")
            await db.commit()
            return

        if user_version >= DB_VERSION:
            return

        # Sequential migrations
        if user_version < 2:
            await db.executescript(
                """
                CREATE TABLE IF NOT EXISTS admins (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tg_user_id INTEGER NOT NULL UNIQUE,
                    username TEXT
                );

                CREATE TABLE IF NOT EXISTS groups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tg_chat_id INTEGER NOT NULL UNIQUE,
                    title TEXT
                );

                CREATE TABLE IF NOT EXISTS topics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    group_id INTEGER NOT NULL,
                    tg_topic_id INTEGER NOT NULL,
                    title TEXT,
                    FOREIGN KEY (group_id) REFERENCES groups(id)
                );

                ALTER TABLE subjects
                    ADD COLUMN sections_mode TEXT NOT NULL DEFAULT 'theory_only'
                        CHECK(sections_mode IN (
                            'theory_only',
                            'theory_discussion',
                            'theory_discussion_lab'
                        ));

                ALTER TABLE materials ADD COLUMN tg_storage_chat_id INTEGER;
                ALTER TABLE materials ADD COLUMN tg_storage_msg_id INTEGER;
                ALTER TABLE materials ADD COLUMN source_chat_id INTEGER;
                ALTER TABLE materials ADD COLUMN source_topic_id INTEGER;
                ALTER TABLE materials ADD COLUMN source_message_id INTEGER;
                ALTER TABLE materials ADD COLUMN created_by_admin_id INTEGER;

                CREATE TABLE IF NOT EXISTS ingestions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    material_id INTEGER,
                    status TEXT NOT NULL DEFAULT 'pending',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (material_id) REFERENCES materials(id)
                );

                CREATE INDEX IF NOT EXISTS idx_materials_core
                    ON materials(subject_id, section, year_id, category);
                CREATE INDEX IF NOT EXISTS idx_materials_storage
                    ON materials(tg_storage_chat_id, tg_storage_msg_id);
                CREATE INDEX IF NOT EXISTS idx_topics_chat
                    ON topics(group_id, tg_topic_id);
                CREATE INDEX IF NOT EXISTS idx_ingestions_status
                    ON ingestions(status, created_at);
                """
            )

        await db.execute(f"PRAGMA user_version={DB_VERSION}")
        await db.commit()
