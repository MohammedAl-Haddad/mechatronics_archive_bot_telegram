import re


def normalize_section(s: str | None) -> str | None:
    """Return canonical section code (theory/lab/discussion) or ``None``.

    Accepts Arabic labels or English codes, ignoring case, spaces and
    underscores.
    """
    if not s:
        return None
    key = re.sub(r"[_\s]+", "", s).lower()
    mapping = {
        "نظري": "theory",
        "عملي": "lab",
        "مناقشة": "discussion",
        "مناقشه": "discussion",
        "theory": "theory",
        "lab": "lab",
        "discussion": "discussion",
    }
    return mapping.get(key)

def display_section(code: str) -> str:
    """Return Arabic label for a canonical *code*."""
    labels = {
        "theory": "نظري",
        "discussion": "مناقشة",
        "lab": "عملي",
    }
    return labels.get(code, code)

__all__ = ["normalize_section", "display_section"]
