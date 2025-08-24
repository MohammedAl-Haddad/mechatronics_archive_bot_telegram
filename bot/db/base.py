import os
import aiosqlite

DB_PATH = "database/archive.db"


async def _column_exists(db: aiosqlite.Connection, table: str, column: str) -> bool:
    cur = await db.execute(f"PRAGMA table_info({table})")
    cols = [row[1] for row in await cur.fetchall()]
    return column in cols


async def _migrate(db: aiosqlite.Connection) -> None:
    """Apply additive schema updates (DB v2)."""
    # subjects.sections_mode
    if not await _column_exists(db, "subjects", "sections_mode"):
        await db.execute(
            """
            ALTER TABLE subjects
            ADD COLUMN sections_mode TEXT CHECK(sections_mode IN (
                'theory_only','theory_discussion','theory_discussion_lab'
            )) DEFAULT 'theory_discussion_lab'
            """
        )

    # materials new columns
    materials_cols = [
        ("tg_storage_chat_id", "INTEGER"),
        ("tg_storage_msg_id", "INTEGER"),
        ("source_chat_id", "INTEGER"),
        ("source_topic_id", "INTEGER"),
        ("source_message_id", "INTEGER"),
        ("created_by_admin_id", "INTEGER"),
        ("file_unique_id", "TEXT"),
    ]
    for col, col_type in materials_cols:
        if not await _column_exists(db, "materials", col):
            await db.execute(f"ALTER TABLE materials ADD COLUMN {col} {col_type}")

    # new tables
    await db.execute(
        """
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tg_user_id INTEGER UNIQUE,
            name TEXT,
            role TEXT NOT NULL,
            permissions_mask INTEGER NOT NULL,
            level_scope TEXT DEFAULT 'all',
            is_active INTEGER NOT NULL DEFAULT 1
        )
        """
    )
    admin_cols = [
        ("role", "TEXT", "'ADMIN'"),
        ("permissions_mask", "INTEGER", "0"),
        ("level_scope", "TEXT", "'all'"),
        ("is_active", "INTEGER", "1"),
    ]
    for col, col_type, default in admin_cols:
        if not await _column_exists(db, "admins", col):
            await db.execute(
                f"ALTER TABLE admins ADD COLUMN {col} {col_type} DEFAULT {default}"
            )
    await db.execute(
        """
        CREATE TABLE IF NOT EXISTS groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tg_chat_id INTEGER UNIQUE NOT NULL,
            title TEXT,
            level_id INTEGER,
            term_id INTEGER,
            FOREIGN KEY (level_id) REFERENCES levels(id),
            FOREIGN KEY (term_id) REFERENCES terms(id)
        )
        """
    )
    group_cols = [("level_id", "INTEGER"), ("term_id", "INTEGER")]
    for col, col_type in group_cols:
        if not await _column_exists(db, "groups", col):
            await db.execute(f"ALTER TABLE groups ADD COLUMN {col} {col_type}")
    await db.execute(
        """
        CREATE TABLE IF NOT EXISTS topics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id INTEGER NOT NULL,
            tg_topic_id INTEGER NOT NULL,
            subject_id INTEGER NOT NULL,
            section TEXT NOT NULL CHECK(section IN ('theory','discussion','lab')),
            FOREIGN KEY (group_id) REFERENCES groups(id),
            FOREIGN KEY (subject_id) REFERENCES subjects(id),
            UNIQUE (group_id, tg_topic_id)
        )
        """
    )

    topic_cols = [("subject_id", "INTEGER"), ("section", "TEXT")]
    for col, col_type in topic_cols:
        if not await _column_exists(db, "topics", col):
            await db.execute(f"ALTER TABLE topics ADD COLUMN {col} {col_type}")
    await db.execute(
        """
        CREATE TABLE IF NOT EXISTS ingestions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            material_id INTEGER,
            status TEXT NOT NULL,
            tg_message_id INTEGER,
            admin_id INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (material_id) REFERENCES materials(id),
            FOREIGN KEY (admin_id) REFERENCES admins(id)
        )
        """
    )

    ingestion_cols = [
        ("tg_message_id", "INTEGER"),
        ("admin_id", "INTEGER"),
        ("action", "TEXT DEFAULT 'add'"),
        ("file_unique_id", "TEXT"),
    ]
    for col, col_type in ingestion_cols:
        if not await _column_exists(db, "ingestions", col):
            await db.execute(f"ALTER TABLE ingestions ADD COLUMN {col} {col_type}")

    # indexes
    await db.execute(
        "CREATE INDEX IF NOT EXISTS idx_materials_core ON materials(subject_id, section, year_id, category)"
    )
    await db.execute(
        "CREATE INDEX IF NOT EXISTS idx_materials_storage ON materials(tg_storage_chat_id, tg_storage_msg_id)"
    )
    await db.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_topics_chat ON topics(group_id, tg_topic_id)"
    )
    await db.execute(
        "CREATE INDEX IF NOT EXISTS idx_ingestions_status ON ingestions(status, created_at)"
    )


async def migrate_if_needed() -> None:
    """Run migration on existing database."""
    async with aiosqlite.connect(DB_PATH) as db:
        await _migrate(db)
        await db.commit()


async def init_db() -> None:
    """Ensure database folder exists and initialize schema, then migrate."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        with open("database/init.sql", "r", encoding="utf-8") as f:
            await db.executescript(f.read())
        await _migrate(db)
        await db.commit()
