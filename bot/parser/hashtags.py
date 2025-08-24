"""Parsing utilities for hashtag based ingestion.

The new ingestion flow relies solely on plain text contained in the caption
or message body.  ``telegram`` entities are intentionally ignored so the
parsing logic here works with raw text only.  The helpers normalise hidden
direction markers, convert Eastern Arabic digits to their Latin
representation and then extract structured information from the ordered list
of hashtags.

The parser understands a small, fixed set of Arabic hashtags that indicate
the *content type* in addition to generic tags for the lecture number, year
and lecturer name.  The order of these tags is significant and is validated
according to the rules described in :mod:`README`.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable, List, Tuple

from ..utils.formatting import arabic_ordinal, to_display_name, ARABIC_ORDINALS

# ---------------------------------------------------------------------------
# Normalisation helpers
# ---------------------------------------------------------------------------
BIDI_RE = re.compile(r"[\u200e\u200f\u202a-\u202e]")
_ARABIC_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")


def _clean(text: str) -> str:
    """Return *text* without direction markers and with normalised digits."""

    return BIDI_RE.sub("", text).translate(_ARABIC_DIGITS)


# ---------------------------------------------------------------------------
# Tag extraction
# ---------------------------------------------------------------------------

CONTENT_TYPE_ALIASES = {
    "موجز_يومي": "daily_brief",
    "صور_السبورة": "board_images",
    "الملزمة": "booklet",
    "نموذج_النصفي": "exam_mid",
    "نموذج_النهائي": "exam_final",
    "التوصيف": "syllabus",
    "جدول_الحضور": "attendance",
    # Existing types kept for backwards compatibility
    "slides": "slides",
    "audio": "audio",
    "video": "video",
    "board_images": "board_images",
}

LECTURER_PREFIXES: Tuple[str, ...] = (
    "الدكتور_",
    "الدكتورة_",
    "الأستاذ_",
    "الأستاذة_",
    "المهندس_",
    "المهندسة_",
    "م_",
    "م",
)

ORDINAL_WORDS = {v: k for k, v in ARABIC_ORDINALS.items()}


@dataclass
class ParsedHashtags:
    content_type: str | None = None
    lecture_no: int | None = None
    lecture_no_display: str | None = None
    title: str | None = None
    year: int | None = None
    lecturer: str | None = None
    tags: List[str] | None = None


# Regular expressions
YEAR_TAG_RE = re.compile(r"^#(\d{4})(?:هـ|ه)?$")
LECTURE_TAG_RE = re.compile(r"^#(?:ال)?محاضرة_(.+?)(?::\s*(.+))?$")


def _split_lines(text: str) -> List[str]:
    """Return ordered list of hashtag lines from *text*.

    Only lines starting with ``#`` are considered hashtags.  Trailing text
    after ``:`` is preserved so titles can be extracted for lecture tags.
    """

    lines = []
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("#"):
            lines.append(s)
    return lines


def parse_hashtags(text: str) -> Tuple[ParsedHashtags, str | None]:
    """Parse *text* and return ``(info, error)``.

    ``error`` is ``None`` when parsing and validation succeed.  Otherwise it
    contains a short Arabic message suitable for presenting to the user.
    """

    cleaned = _clean(text or "")
    tags = _split_lines(cleaned)
    info = ParsedHashtags(tags=tags)
    sequence: List[str] = []

    for raw in tags:
        token = raw.split()[0]

        # Content type
        ct = CONTENT_TYPE_ALIASES.get(token.lstrip("#"))
        if ct and info.content_type is None:
            info.content_type = ct
            sequence.append("content")
            continue

        # Year
        m = YEAR_TAG_RE.match(token)
        if m and info.year is None:
            y = int(m.group(1))
            if 1300 <= y <= 1600:
                info.year = y
                sequence.append("year")
                continue

        # Lecturer
        if info.lecturer is None:
            norm = token.lstrip("#")
            for p in LECTURER_PREFIXES:
                if norm.startswith(p):
                    info.lecturer = to_display_name(norm[len(p):])
                    sequence.append("lecturer")
                    break
            else:
                # Lecture tag?
                m = LECTURE_TAG_RE.match(raw)
                if m and info.lecture_no is None:
                    ident, title = m.groups()
                    ident = ident.strip()
                    if ident.isdigit():
                        info.lecture_no = int(ident)
                    else:
                        info.lecture_no = ORDINAL_WORDS.get(ident)
                    if info.lecture_no:
                        info.lecture_no_display = arabic_ordinal(info.lecture_no)
                    if title:
                        info.title = title.strip()
                    sequence.append("lecture")
                else:
                    sequence.append("unknown")
        else:
            # Lecture tag after lecturer?
            m = LECTURE_TAG_RE.match(raw)
            if m and info.lecture_no is None:
                ident, title = m.groups()
                ident = ident.strip()
                if ident.isdigit():
                    info.lecture_no = int(ident)
                else:
                    info.lecture_no = ORDINAL_WORDS.get(ident)
                if info.lecture_no:
                    info.lecture_no_display = arabic_ordinal(info.lecture_no)
                if title:
                    info.title = title.strip()
                sequence.append("lecture")
            else:
                sequence.append("unknown")

    # ------------------------------------------------------------------
    # Validation of order and required tags
    # ------------------------------------------------------------------
    def _err(msg: str) -> Tuple[ParsedHashtags, str]:
        return info, msg

    ct = info.content_type
    if ct in {"daily_brief", "board_images"}:
        expected = ["content", "lecture", "year"]
        if sequence[:3] != expected:
            return _err(
                "رجاءً اتّبع ترتيب الوسوم لهذا النوع: #موجز_يومي\n#المحاضرة_1: العنوان\n#1446"
            )
        if len(sequence) > 4 or (len(sequence) == 4 and sequence[3] != "lecturer"):
            return _err(
                "رجاءً اتّبع ترتيب الوسوم لهذا النوع: #موجز_يومي\n#المحاضرة_1: العنوان\n#1446\n#الدكتور_اسم (اختياري)"
            )
        if not info.lecture_no or not info.title:
            return _err("هذا النوع يتطلب وسم محاضرة بصيغة: #المحاضرة_1: <العنوان>")

    elif ct in {"booklet", "exam_mid", "exam_final"}:
        expected = ["content", "year"]
        if sequence[:2] != expected:
            return _err(
                "رجاءً اتّبع ترتيب الوسوم لهذا النوع: #الملزمة\n#1446"
            )
        if len(sequence) > 3 or (len(sequence) == 3 and sequence[2] != "lecturer"):
            return _err(
                "رجاءً اتّبع ترتيب الوسوم لهذا النوع: #الملزمة\n#1446\n#الدكتور_اسم (اختياري)"
            )

    elif ct == "syllabus":
        if not sequence or sequence[0] != "content":
            return _err("رجاءً اتّبع ترتيب الوسوم لهذا النوع: #التوصيف")
        if any(s not in {"content", "year", "lecturer"} for s in sequence):
            return _err("رجاءً اتّبع ترتيب الوسوم لهذا النوع: #التوصيف")
        if sequence.count("year") and sequence.index("year") != 1:
            return _err("رجاءً اتّبع ترتيب الوسوم لهذا النوع: #التوصيف\n#1446 (اختياري)")
        if sequence.count("lecturer"):
            idx = sequence.index("lecturer")
            if idx not in {1, 2}:
                return _err(
                    "رجاءً اتّبع ترتيب الوسوم لهذا النوع: #التوصيف\n#1446\n#الدكتور_اسم"
                )

    elif ct == "attendance":
        if sequence != ["content"]:
            return _err("رجاءً اتّبع ترتيب الوسوم لهذا النوع: #جدول_الحضور")

    # Types that require lecture tag but have no strict ordering
    if ct in {"slides", "audio", "video", "board_images"}:
        if not info.lecture_no:
            return _err("هذا النوع يتطلب وسم محاضرة بصيغة: #المحاضرة_1: <العنوان>")

    return info, None


__all__ = ["parse_hashtags", "ParsedHashtags"]

