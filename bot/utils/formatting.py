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
}


def arabic_ordinal(n: int) -> str:
    """Return Arabic ordinal word for *n* if known."""
    return ARABIC_ORDINALS.get(n, str(n))


def to_display_name(value: str) -> str:
    """Normalize *value* by removing direction markers and underscores."""
    if not value:
        return ""
    cleaned = re.sub(r"[\u200e\u200f]", "", value)
    return cleaned.replace("_", " ").strip()


__all__ = ["arabic_ordinal", "to_display_name"]
