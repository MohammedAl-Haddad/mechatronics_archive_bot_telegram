"""Unified DB package with convenient re-exports."""

from __future__ import annotations

from importlib import import_module

_SUBMODULES = [
    "admins",
    "topics",
    "subjects",
    "materials",
    "years",
    "lecturers",
    "groups",
    "ingestions",
    "term_resources",
]

__all__ = ["init_db", "ensure_owner_full_perms", "is_owner", "has_perm", "MANAGE_ADMINS"]

for _name in _SUBMODULES:
    _mod = import_module(f"{__name__}.{_name}")
    names = getattr(_mod, "__all__", dir(_mod))
    for _attr in names:
        if _attr.startswith("_"):
            continue
        globals()[_attr] = getattr(_mod, _attr)
        if _attr not in __all__:
            __all__.append(_attr)

from .base import init_db
from .admins import ensure_owner_full_perms, is_owner, has_perm, MANAGE_ADMINS
from .years import get_or_create as get_or_create_year
from .lecturers import get_or_create as get_or_create_lecturer
from .subjects import get_or_create as get_or_create_subject

__all__.extend(["get_or_create_year", "get_or_create_lecturer", "get_or_create_subject"])
