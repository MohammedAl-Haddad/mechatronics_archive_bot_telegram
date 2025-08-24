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

    The helper removes any leading ``#`` markers, replaces hyphens with
    underscores and folds the text to lower‑case.  Extra whitespace around the
    tag is stripped so the result can be safely compared against our known
    aliases.
    """

    cleaned = tag.lstrip("#").replace("-", "_").strip()
    return cleaned.casefold()


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
    "notes": {"notes", "note", "ملاحظات", "نوته"},
    "board_images": {"صور_السبورة", "board", "board_images"},
    "related": {"ملف_ذو_صلة", "related"},
    # Additional categories supported by the database
    "external_link": {"external_link"},
    "simulation": {"simulation"},
    "mind_map": {"mind_map"},
    "transcript": {"transcript"},
}


def resolve_category(tag: str) -> str | None:
    """Map *tag* to a canonical category if possible."""

    return next(
        (category for category, aliases in CATEGORY_ALIASES.items() if tag in aliases),
        None,
    )


_YEAR_RE = re.compile(r"^\d{4}(?:-\d{4})?$")

LECTURER_PREFIXES: tuple[str, ...] = (
    "الدكتور_",
    "الدكتورة_",
    "الأستاذ_",
    "الأستاذة_",
    "م_",
    "م",
    "مهندس_",
    "مهندسة_",
)


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

        # Support ``category:title`` syntax
        if ":" in norm:
            norm, title = norm.split(":", 1)
            if not result["title"]:
                result["title"] = title.replace("_", " ")

        if result["category"] is None:
            cat = resolve_category(norm)
            if cat:
                result["category"] = cat
                continue

        if result["year"] is None and _YEAR_RE.match(norm):
            result["year"] = norm
            continue

        if result["lecturer"] is None:
            for prefix in LECTURER_PREFIXES:
                if norm.startswith(prefix):
                    name = norm[len(prefix) :].replace("_", " ").strip()
                    if name:
                        result["lecturer"] = name
                        break
            else:
                leftovers.append(norm)
        else:
            leftovers.append(norm)

    if leftovers and not result["title"]:
        result["title"] = " ".join(t.replace("_", " ") for t in leftovers)

    return result


__all__ = ["normalize_tag", "resolve_category", "parse_hashtags"]
