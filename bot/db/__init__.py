"""
Unified DB package exports (imports only; no I/O).
Allows:
  - import bot.db
  - from bot.db import admins, topics, subjects, materials, years, lecturers
"""
from __future__ import annotations

# Re-export submodules explicitly (no side effects here)
from . import admins
from . import topics
from . import subjects
from . import materials
from . import years
from . import lecturers

__all__ = [
    "admins",
    "topics",
    "subjects",
    "materials",
    "years",
    "lecturers",
]
