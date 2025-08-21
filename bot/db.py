# db.py
# طبقة الوصول لقاعدة البيانات (SQLite عبر aiosqlite)
# تضم فقط الدوال التي يستخدمها bot.py في الإصدار الحالي.

import os
import aiosqlite

DB_PATH = "database/archive.db"


# -----------------------------------------------------------------------------
# تهيئة قاعدة البيانات
# -----------------------------------------------------------------------------
async def init_db() -> None:
    """
    يضمن وجود مجلد قاعدة البيانات، ثم ينفّذ ملف schema/init.sql مرة واحدة.
    """
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        with open("database/init.sql", "r", encoding="utf-8") as f:
            await db.executescript(f.read())
        await db.commit()


# -----------------------------------------------------------------------------
# قراءات أساسية (مستويات / أترام / مواد)
# -----------------------------------------------------------------------------
async def get_levels():
    """
    يرجع قائمة المستويات بشكل [(id, name), ...] مرتبة بالمعرّف.
    """
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

async def get_year_id_by_name(name: str) -> int | None:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT id FROM years WHERE name=?", (name,))
        row = await cur.fetchone()
        return row[0] if row else None

async def get_lecturer_id_by_name(name: str) -> int | None:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT id FROM lecturers WHERE name=?", (name,))
        row = await cur.fetchone()
        return row[0] if row else None

async def insert_level(name: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR IGNORE INTO levels (name) VALUES (?)", (name,))
        await db.commit()

async def insert_term(name: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR IGNORE INTO terms (name) VALUES (?)", (name,))
        await db.commit()

async def insert_subject(code: str, name: str, level_id: int, term_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO subjects (code, name, level_id, term_id) VALUES (?, ?, ?, ?)",
            (code, name, level_id, term_id)
        )
        await db.commit()

# ---------- materials ----------
async def insert_material(
    subject_id: int,
    section: str,       # 'theory' | 'discussion' | 'lab' | 'syllabus' | 'apps'
    category: str,      # 'lecture'|'exam'|'booklet'|'board_images'|'video'|'simulation'|'summary'|'notes'|'external_link'
    title: str,
    url: str | None = None,
    year_id: int | None = None,
    lecturer_id: int | None = None
):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO materials (subject_id, section, category, title, url, year_id, lecturer_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (subject_id, section, category, title, url, year_id, lecturer_id)
        )
        await db.commit()


async def insert_year(name: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR IGNORE INTO years (name) VALUES (?)", (name,))
        await db.commit()

async def insert_lecturer(name: str, role: str = "lecturer"):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO lecturers (name, role) VALUES (?, ?)",
            (name, role)
        )
        await db.commit()

async def ensure_year_id(name: str) -> int:
    _id = await get_year_id_by_name(name)
    if _id is not None:
        return _id
    await insert_year(name)
    _id = await get_year_id_by_name(name)
    if _id is None:
        raise RuntimeError(f"Failed to create year: {name}")
    return _id

async def ensure_lecturer_id(name: str, role: str = "lecturer") -> int:
    _id = await get_lecturer_id_by_name(name)
    if _id is not None:
        return _id
    await insert_lecturer(name, role)
    _id = await get_lecturer_id_by_name(name)
    if _id is None:
        raise RuntimeError(f"Failed to create lecturer: {name}")
    return _id


async def get_terms_by_level(level_id: int):
    """
    يرجع قائمة الأترام المرتبطة بالمستوى المحدد: [(term_id, term_name), ...]
    يعتمد على وجود مواد (subjects) مرتبطة بذلك المستوى.
    """
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
    """
    يرجع أسماء المواد لهذا (المستوى، الترم) بالشكل [(name,), ...]
    (يُستخدم في بناء أزرار اختيار المادة).
    """
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT name FROM subjects WHERE level_id = ? AND term_id = ? ORDER BY id",
            (level_id, term_id),
        )
        return await cur.fetchall()


async def get_subject_id_by_name(level_id: int, term_id: int, subject_name: str) -> int | None:
    """
    يرجع معرّف المادة بحسب الاسم والمستوى والترم، أو None إذا لم توجد.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT id FROM subjects WHERE level_id=? AND term_id=? AND name=?",
            (level_id, term_id, subject_name),
        )
        row = await cur.fetchone()
        return row[0] if row else None


# -----------------------------------------------------------------------------
# خصائص ديناميكية لبناء القوائم
# -----------------------------------------------------------------------------
async def count_subjects(level_id: int, term_id: int) -> int:
    """
    عدد المواد في (مستوى/ترم) — يُستخدم لاستخراج وجود مواد من عدمه.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT COUNT(*) FROM subjects WHERE level_id=? AND term_id=?",
            (level_id, term_id),
        )
        (n,) = await cur.fetchone()
        return n


async def term_feature_flags(level_id: int, term_id: int) -> dict:
    """
    يُعيد أعلام توضح ما إذا كانت هناك مواد/سيلابس/روابط خارجية في الترم:
    {
        "has_subjects": bool,
        "has_syllabus": bool,
        "has_links": bool
    }
    """
    async with aiosqlite.connect(DB_PATH) as db:
        # سيلابس
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

        # روابط خارجية
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
    """
    الأقسام المتوفرة فعليًا لهذه المادة من جدول materials
    (مثال: theory / discussion / lab / syllabus / apps).
    """
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT DISTINCT section FROM materials WHERE subject_id=?",
            (subject_id,),
        )
        rows = await cur.fetchall()
        return [r[0] for r in rows]


# -----------------------------------------------------------------------------
# فلاتر حسب السنة/المحاضر/التصنيفات
# -----------------------------------------------------------------------------
async def get_years_for_subject_section(subject_id: int, section: str):
    """
    السنوات المتاحة لمادة + قسم بالشكل [(year_id, year_name), ...] تنازليًا بالاسم.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            """
            SELECT DISTINCT y.id, y.name
            FROM materials m
            JOIN years y ON y.id = m.year_id
            WHERE m.subject_id = ? AND m.section = ?
            ORDER BY y.name DESC
            """,
            (subject_id, section),
        )
        return await cur.fetchall()


async def get_lecturers_for_subject_section(subject_id: int, section: str):
    """
    المحاضرون المتاحون لمادة + قسم بالشكل [(lect_id, lect_name), ...].
    """
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            """
            SELECT DISTINCT l.id, l.name
            FROM materials m
            JOIN lecturers l ON l.id = m.lecturer_id
            WHERE m.subject_id = ? AND m.section = ?
            ORDER BY l.name
            """,
            (subject_id, section),
        )
        return await cur.fetchall()


async def has_lecture_category(subject_id: int, section: str) -> bool:
    """
    هل توجد محاضرات (category='lecture') لهذه المادة + القسم؟
    """
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            """
            SELECT 1
            FROM materials
            WHERE subject_id=? AND section=? AND category='lecture'
            LIMIT 1
            """,
            (subject_id, section),
        )
        return (await cur.fetchone()) is not None


async def list_lecture_titles(subject_id: int, section: str) -> list[str]:
    """
    عناوين المحاضرات لجميع السنوات/المحاضرين (distinct) مرتبة أبجديًا.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            """
            SELECT DISTINCT title
            FROM materials
            WHERE subject_id=? AND section=? AND category='lecture'
            ORDER BY title
            """,
            (subject_id, section),
        )
        return [r[0] for r in await cur.fetchall()]


async def list_lecture_titles_by_year(subject_id: int, section: str, year_id: int) -> list[str]:
    """
    عناوين المحاضرات لسنة محددة.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            """
            SELECT DISTINCT title
            FROM materials
            WHERE subject_id=? AND section=? AND category='lecture' AND year_id=?
            ORDER BY title
            """,
            (subject_id, section, year_id),
        )
        return [r[0] for r in await cur.fetchall()]


async def list_lecture_titles_by_lecturer(subject_id: int, section: str, lecturer_id: int) -> list[str]:
    """
    عناوين المحاضرات لمحاضر محدد.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            """
            SELECT DISTINCT title
            FROM materials
            WHERE subject_id=? AND section=? AND category='lecture' AND lecturer_id=?
            ORDER BY title
            """,
            (subject_id, section, lecturer_id),
        )
        return [r[0] for r in await cur.fetchall()]


async def list_lecture_titles_by_lecturer_year(
    subject_id: int, section: str, lecturer_id: int, year_id: int
) -> list[str]:
    """
    عناوين المحاضرات لمحاضر + سنة معًا.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            """
            SELECT DISTINCT title
            FROM materials
            WHERE subject_id=? AND section=? AND category='lecture' AND lecturer_id=? AND year_id=?
            ORDER BY title
            """,
            (subject_id, section, lecturer_id, year_id),
        )
        return [r[0] for r in await cur.fetchall()]


async def get_years_for_subject_section_lecturer(subject_id: int, section: str, lecturer_id: int):
    """
    السنوات المتاحة لمحاضر معيّن داخل مادة + قسم.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            """
            SELECT DISTINCT y.id, y.name
            FROM materials m
            JOIN years y ON y.id = m.year_id
            WHERE m.subject_id=? AND m.section=? AND m.lecturer_id=?
              AND m.category='lecture' AND m.year_id IS NOT NULL
            ORDER BY y.name DESC
            """,
            (subject_id, section, lecturer_id),
        )
        return await cur.fetchall()


# -----------------------------------------------------------------------------
# جلب المواد/التصنيفات
# -----------------------------------------------------------------------------
async def get_lecture_materials(
    subject_id: int,
    section: str,
    *,
    year_id: int | None = None,
    lecturer_id: int | None = None,
    title: str | None = None,
):
    """
    يرجع ملفات (category='lecture') مع إمكانية التصفية بالسنة/المحاضر/العنوان.
    الشكل: [(id, title, url), ...]
    """
    q = """
        SELECT id, title, url
        FROM materials
        WHERE subject_id=? AND section=? AND category='lecture'
    """
    params = [subject_id, section]
    if year_id is not None:
        q += " AND year_id=?"
        params.append(year_id)
    if lecturer_id is not None:
        q += " AND lecturer_id=?"
        params.append(lecturer_id)
    if title is not None:
        q += " AND title=?"
        params.append(title)
    q += " ORDER BY id"

    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(q, tuple(params))
        return await cur.fetchall()


async def get_materials_by_category(
    subject_id: int,
    section: str,
    category: str,
    *,
    year_id: int | None = None,
    lecturer_id: int | None = None,
    title: str | None = None,
):
    """
    يرجع مواد حسب تصنيف عام (امتحانات/ملازم/ملخصات/… إلخ)
    مع مرشحات اختيارية (سنة/محاضر/عنوان).
    الشكل: [(id, title, url), ...]
    """
    q = """
        SELECT id, title, url
        FROM materials
        WHERE subject_id=? AND section=? AND category=?
    """
    params = [subject_id, section, category]
    if year_id is not None:
        q += " AND year_id=?"
        params.append(year_id)
    if lecturer_id is not None:
        q += " AND lecturer_id=?"
        params.append(lecturer_id)
    if title is not None:
        q += " AND title=?"
        params.append(title)
    q += " ORDER BY id"

    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(q, tuple(params))
        return await cur.fetchall()


async def list_categories_for_subject_section_year(
    subject_id: int,
    section: str,
    year_id: int,
    lecturer_id: int | None = None,
) -> list[str]:
    """
    تصنيفات سنة متاحة لمادة + قسم + سنة (باستثناء:
    - 'lecture' (المحاضرات تُعرض من زر منفصل)
    - مرفقات المحاضرات التي يجب ألا تظهر على شاشة السنة)
    """
    lecture_attachment_cats = (
        "slides",
        "audio",
        "board_images",
        "video",
        "mind_map",
        "transcript",
        "related",
    )

    placeholders = ",".join("?" * len(lecture_attachment_cats))
    q = f"""
        SELECT DISTINCT category
        FROM materials
        WHERE subject_id=? AND section=? AND year_id=? AND category IS NOT NULL
          AND category <> 'lecture'
          AND category NOT IN ({placeholders})
    """
    params = [subject_id, section, year_id, *lecture_attachment_cats]

    if lecturer_id is not None:
        q += " AND lecturer_id=?"
        params.append(lecturer_id)

    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(q, tuple(params))
        return [r[0] for r in await cur.fetchall()]


async def list_categories_for_lecture(
    subject_id: int,
    section: str,
    title: str,
    year_id: int | None = None,
    lecturer_id: int | None = None,
) -> list[str]:
    """
    التصنيفات المتوفرة داخل محاضرة محددة (lecture/slides/audio/…).
    """
    q = """
        SELECT DISTINCT category
        FROM materials
        WHERE subject_id=? AND section=? AND title=? AND category IS NOT NULL
    """
    params = [subject_id, section, title]
    if year_id is not None:
        q += " AND year_id=?"
        params.append(year_id)
    if lecturer_id is not None:
        q += " AND lecturer_id=?"
        params.append(lecturer_id)

    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(q, tuple(params))
        return [r[0] for r in await cur.fetchall()]


# __________الاصدار الثاني ____________

