from __future__ import annotations

from bot.db import (
    insert_level,
    insert_term,
    insert_subject,
    insert_material,
    ensure_year_id,
    ensure_lecturer_id,
    get_level_id_by_name,
    get_term_id_by_name,
    get_subject_id_by_name,
    init_db,
)
from .db.seed_admins import seed_owner


async def _ensure_level_id(name: str) -> int:
    _id = await get_level_id_by_name(name)
    if _id is not None:
        return _id
    await insert_level(name)
    _id = await get_level_id_by_name(name)
    if _id is None:
        raise RuntimeError(f"Failed to create level: {name}")
    return _id


async def _ensure_term_id(name: str) -> int:
    _id = await get_term_id_by_name(name)
    if _id is not None:
        return _id
    await insert_term(name)
    _id = await get_term_id_by_name(name)
    if _id is None:
        raise RuntimeError(f"Failed to create term: {name}")
    return _id


async def load_structure(levels: dict) -> None:
    for level_name, terms in levels.items():
        level_id = await _ensure_level_id(level_name)
        for term_name, subjects in terms.items():
            term_id = await _ensure_term_id(term_name)
            for subj in subjects:
                code = subj.get("code", "").strip()
                name = subj.get("name", "")
                if code == "---":
                    continue
                await insert_subject(code, name, level_id, term_id)


async def load_years_and_lecturers(years: list, lecturers: list) -> None:
    for year in years:
        await ensure_year_id(year)
    for lec in lecturers:
        await ensure_lecturer_id(lec["name"], lec.get("role", "lecturer"))


async def _subject_id(level_name: str, term_name: str, subject_name: str) -> int:
    level_id = await get_level_id_by_name(level_name)
    term_id = await get_term_id_by_name(term_name)
    if not (level_id and term_id):
        raise RuntimeError(f"Level/Term not found: {level_name} / {term_name}")
    sid = await get_subject_id_by_name(level_id, term_id, subject_name)
    if sid is None:
        raise RuntimeError(
            f"Subject not found: {subject_name} ({level_name}/{term_name})"
        )
    return sid


async def load_materials(materials: list[dict]) -> None:
    for m in materials:
        sid = await _subject_id(m["level"], m["term"], m["subject"])
        year_id = None
        if m.get("year"):
            year_id = await ensure_year_id(m["year"])
        lecturer_id = None
        if m.get("lecturer"):
            lecturer_id = await ensure_lecturer_id(m["lecturer"])
        await insert_material(
            sid,
            m["section"],
            m["category"],
            m["title"],
            m.get("url"),
            year_id,
            lecturer_id,
        )


__all__ = [
    "load_structure",
    "load_years_and_lecturers",
    "load_materials",
    "main",
]


async def main() -> None:
    import json

    await init_db()
    payload = json.load(open("seed_data.json", encoding="utf-8"))
    await load_structure(payload["levels"])
    await load_years_and_lecturers(payload["years"], payload["lecturers"])
    await load_materials(payload["materials"])
    await seed_owner()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())

