import re


ARABIC_ORDINALS = {
    1: "الأولى",
    2: "الثانية",
    3: "الثالثة",
    4: "الرابعة",
    5: "الخامسة",
    6: "السادسة",
    7: "السابعة",
    8: "الثامنة",
    9: "التاسعة",
    10: "العاشرة",
    11: "الحادية عشرة",
    12: "الثانية عشرة",
    13: "الثالثة عشرة",
    14: "الرابعة عشرة",
    15: "الخامسة عشرة",
    16: "السادسة عشرة",
    17: "السابعة عشرة",
    18: "الثامنة عشرة",
    19: "التاسعة عشرة",
    20: "العشرون",
}


def arabic_ordinal(n: int) -> str:
    """Return Arabic ordinal word for *n* if known."""
    return ARABIC_ORDINALS.get(n, str(n))


_BIDI_RE = re.compile(r"[\u200e\u200f\u202a-\u202e\u2066-\u2069]")


def to_display_name(value: str) -> str:
    """Normalize *value* by removing direction markers and underscores."""
    if not value:
        return ""
    cleaned = _BIDI_RE.sub("", value)
    return cleaned.replace("_", " ").strip()


__all__ = ["arabic_ordinal", "to_display_name"]
