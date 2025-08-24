import aiosqlite
from dataclasses import dataclass

from .base import DB_PATH


# -----------------------------------------------------------------------------
# Basic reads for levels/terms/subjects
# -----------------------------------------------------------------------------
async def get_levels():
    """Return list of levels as [(id, name), ...] ordered by id."""
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT id, name FROM levels ORDER BY id")
        return await cur.fetchall()


async def get_level_id_by_name(name: str) -> int | None:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT id FROM levels WHERE name=?", (name,))
        row = await cur.fetchone()
        return row[0] if row else None


async def get_term_id_by_name(name: str) -> int | None:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT id FROM terms WHERE name=?", (name,))
        row = await cur.fetchone()
        return row[0] if row else None


async def insert_level(name: str) -> None:
    """Insert a level name if it does not already exist."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR IGNORE INTO levels (name) VALUES (?)", (name,))
        await db.commit()


async def insert_term(name: str) -> None:
    """Insert a term name if it does not already exist."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR IGNORE INTO terms (name) VALUES (?)", (name,))
        await db.commit()


async def get_or_create_level(name: str) -> int:
    """Return id for a level, creating it if necessary."""
    level_id = await get_level_id_by_name(name)
    if level_id is not None:
        return level_id
    await insert_level(name)
    level_id = await get_level_id_by_name(name)
    assert level_id is not None
    return level_id


async def get_or_create_term(name: str) -> int:
    """Return id for a term, creating it if necessary."""
    term_id = await get_term_id_by_name(name)
    if term_id is not None:
        return term_id
    await insert_term(name)
    term_id = await get_term_id_by_name(name)
    assert term_id is not None
    return term_id

async def insert_subject(
    code: str,
    name: str,
    level_id: int,
    term_id: int,
    sections_mode: str = "theory_only",
):
    """Insert a new subject row."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO subjects (code, name, level_id, term_id, sections_mode) VALUES (?, ?, ?, ?, ?)",
            (code, name, level_id, term_id, sections_mode),
        )
        await db.commit()


async def update_subject_mode(subject_id: int, mode: str) -> None:
    """Update the sections mode for a subject."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE subjects SET sections_mode=? WHERE id=?",
            (mode, subject_id),
        )
        await db.commit()


@dataclass
class Subject:
    id: int
    name: str
    level_id: int
    term_id: int
    theory_only: bool


async def get_or_create(term_id: int, name: str, level_id: int | None = None) -> Subject:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT id, level_id, sections_mode FROM subjects WHERE term_id=? AND name=?",
            (term_id, name),
        )
        row = await cur.fetchone()
        if row is None:
            if level_id is None:
                raise ValueError("level_id required to create subject")
            await db.execute(
                "INSERT INTO subjects (code, name, level_id, term_id, sections_mode) VALUES (?, ?, ?, ?, 'theory_only')",
                ("AUTO", name, level_id, term_id),
            )
            await db.commit()
            cur = await db.execute(
                "SELECT id, level_id, sections_mode FROM subjects WHERE term_id=? AND name=?",
                (term_id, name),
            )
            row = await cur.fetchone()
        subj_id, lvl_id, mode = row
        return Subject(subj_id, name, lvl_id, term_id, mode == "theory_only")


async def set_theory_only(subject_id: int, value: bool) -> None:
    mode = "theory_only" if value else "theory_discussion_lab"
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE subjects SET sections_mode=? WHERE id=?",
            (mode, subject_id),
        )
        await db.commit()


# -----------------------------------------------------------------------------
# Queries for navigation
# -----------------------------------------------------------------------------
async def get_terms_by_level(level_id: int):
    """Return terms available for a level: [(term_id, term_name), ...]."""
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            """
            SELECT DISTINCT t.id, t.name
            FROM terms t
            JOIN subjects s ON s.term_id = t.id
            WHERE s.level_id = ?
            ORDER BY t.id
            """,
            (level_id,),
        )
        return await cur.fetchall()


async def get_subjects_by_level_and_term(level_id: int, term_id: int):
    """Return subject names for level/term as [(name,), ...]."""
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT name FROM subjects WHERE level_id = ? AND term_id = ? ORDER BY id",
            (level_id, term_id),
        )
        return await cur.fetchall()


async def get_subject_id_by_name(level_id: int, term_id: int, subject_name: str) -> int | None:
    """Return subject id for given level/term/name or None."""
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT id FROM subjects WHERE level_id=? AND term_id=? AND name=?",
            (level_id, term_id, subject_name),
        )
        row = await cur.fetchone()
        return row[0] if row else None


# -----------------------------------------------------------------------------
# Dynamic helpers
# -----------------------------------------------------------------------------
async def count_subjects(level_id: int, term_id: int) -> int:
    """Return number of subjects for the specified level and term."""
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT COUNT(*) FROM subjects WHERE level_id=? AND term_id=?",
            (level_id, term_id),
        )
        (n,) = await cur.fetchone()
        return n


async def term_feature_flags(level_id: int, term_id: int) -> dict:
    """Return flags describing available materials for a level/term pair."""
    async with aiosqlite.connect(DB_PATH) as db:
        # syllabus exists?
        cur = await db.execute(
            """
            SELECT 1
            FROM materials m
            JOIN subjects s ON s.id = m.subject_id
            WHERE s.level_id=? AND s.term_id=? AND m.section='syllabus'
            LIMIT 1
            """,
            (level_id, term_id),
        )
        has_syllabus = (await cur.fetchone()) is not None

        # external links exist?
        cur = await db.execute(
            """
            SELECT 1
            FROM materials m
            JOIN subjects s ON s.id = m.subject_id
            WHERE s.level_id=? AND s.term_id=? AND m.category='external_link'
            LIMIT 1
            """,
            (level_id, term_id),
        )
        has_links = (await cur.fetchone()) is not None

        n_subj = await count_subjects(level_id, term_id)

    return {"has_subjects": n_subj > 0, "has_syllabus": has_syllabus, "has_links": has_links}


async def get_available_sections_for_subject(subject_id: int) -> list[str]:
    """Return distinct sections available for a subject from materials."""
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT DISTINCT section FROM materials WHERE subject_id=?",
            (subject_id,),
        )
        rows = await cur.fetchall()
        return [r[0] for r in rows]
