"""Utilities for parsing and normalizing hashtags.

The ingestion flow relies on hashtags embedded in Telegram messages to
extract metadata about the shared material.  This module provides helpers
for normalizing the raw hashtag tokens and mapping them to the canonical
categories used by the database.  Arabic synonyms for the supported
categories are also recognised.
"""
from __future__ import annotations

import re
from typing import Iterable

# ---------------------------------------------------------------------------
# Normalisation helpers
# ---------------------------------------------------------------------------

def normalize_tag(tag: str) -> str:
    """Return a simplified representation of a hashtag.

    Leading ``#`` symbols are stripped, hyphens are converted to underscores
    and the value is lower‑cased.
    """

    return tag.lstrip("#").replace("-", "_").strip().lower()


# ---------------------------------------------------------------------------
# Category mapping
# ---------------------------------------------------------------------------
# Synonyms for the supported categories.  Both English and Arabic aliases are
# included so that admins can use whichever language they prefer when tagging
# materials.
CATEGORY_ALIASES: dict[str, set[str]] = {
    "lecture": {"lecture", "lectures", "محاضرة", "محاضرات"},
    "slides": {"slides", "شرائح", "شريحة", "سلايد", "سلايدات"},
    "audio": {"audio", "صوت", "صوتية", "صوتيات"},
    "video": {"video", "فيديو", "فديو"},
    "exam": {"exam", "اختبار", "اختبارات", "امتحان"},
    "booklet": {"booklet", "مذكرة", "مذكرات"},
    "summary": {"summary", "ملخص", "ملخصات"},
    "notes": {"notes", "ملاحظات", "نوته"},
}


def resolve_category(tag: str) -> str | None:
    """Map *tag* to a canonical category if possible."""

    for category, aliases in CATEGORY_ALIASES.items():
        if tag in aliases:
            return category
    return None


_YEAR_RE = re.compile(r"^\d{4}(?:-\d{4})?$")


def parse_hashtags(tags: Iterable[str]) -> dict[str, str | None]:
    """Parse *tags* into structured information.

    The function looks for known categories, year labels and lecturer names.
    Remaining tags are combined and treated as the material title.
    """

    result: dict[str, str | None] = {
        "year": None,
        "lecturer": None,
        "category": None,
        "title": None,
    }
    leftovers: list[str] = []

    for raw in tags:
        norm = normalize_tag(raw)
        if not norm:
            continue

        if result["category"] is None:
            cat = resolve_category(norm)
            if cat:
                result["category"] = cat
                continue

        if result["year"] is None and _YEAR_RE.match(norm):
            result["year"] = norm
            continue

        leftovers.append(norm)

    if leftovers:
        result["lecturer"] = leftovers.pop(0).replace("_", " ")
        if leftovers:
            result["title"] = " ".join(t.replace("_", " ") for t in leftovers)

    return result


__all__ = ["normalize_tag", "resolve_category", "parse_hashtags"]
