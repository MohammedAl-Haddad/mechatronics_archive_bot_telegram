"""Navigation state management as a class.

This module defines :class:`NavigationState` which encapsulates all logic that
previously lived as standalone helper functions.  The class stores a reference
to ``user_data`` provided by ``telegram.ext`` and exposes methods such as
``set_level`` and ``back_one`` to manipulate the navigation stack.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple


NAV_KEY = "nav"

TYPE_TO_KEYS: Dict[str, List[str]] = {
    "level": ["level_id"],
    "term": ["term_id"],
    "subject": ["subject_id"],
    "section": ["section"],
    "year": ["year_id"],
    "lecturer": ["lecturer_id"],
    "lecture": ["lecture_title"],
    # Views that do not store additional keys
    "term_list": [],
    "subject_list": [],
    "year_list": [],
    "lecturer_list": [],
    "lecture_list": [],
    "year_category_menu": [],
    "lecture_category_menu": [],
}


@dataclass
class NavigationState:
    """Stateful navigation helper operating on ``context.user_data``."""

    user_data: Dict

    def __post_init__(self) -> None:
        nav = self.user_data.get(NAV_KEY)
        if not isinstance(nav, dict) or "stack" not in nav or "data" not in nav:
            nav = {"stack": [], "data": {}}
            self.user_data[NAV_KEY] = nav
        self._nav = nav

    # ------------------------------------------------------------------
    # Convenience accessors
    @property
    def stack(self) -> List[Tuple[str, str]]:
        return self._nav["stack"]

    @property
    def data(self) -> Dict:
        return self._nav["data"]

    # ------------------------------------------------------------------
    # Internal helpers
    def _upsert_stack(self, node_type: str, label: str) -> None:
        for i, (t, _) in enumerate(self.stack):
            if t == node_type:
                self.stack[i] = (node_type, label)
                return
        self.stack.append((node_type, label))

    def _truncate_after(self, node_type: str) -> None:
        for i, (t, _) in enumerate(self.stack):
            if t == node_type:
                del self.stack[i + 1 :]
                return

    # ------------------------------------------------------------------
    # Public operations
    def reset(self) -> None:
        self.stack.clear()
        self.data.clear()

    def back_to_levels(self) -> None:
        self.reset()

    def get_ids(self) -> Tuple[int | None, int | None]:
        return self.data.get("level_id"), self.data.get("term_id")

    def get_labels(self) -> Tuple[str | None, str | None]:
        level_label = term_label = None
        for t, lbl in self.stack:
            if t == "level":
                level_label = lbl
            elif t == "term":
                term_label = lbl
        return level_label, term_label

    def back_one(self) -> None:
        if not self.stack:
            return
        node_type, _ = self.stack.pop()
        for key in TYPE_TO_KEYS.get(node_type, []):
            self.data.pop(key, None)

    def push_view(self, node_type: str, label: str = "") -> None:
        self._upsert_stack(node_type, label)
        self._truncate_after(node_type)

    # Setters for different hierarchy levels
    def set_level(self, label: str, level_id: int | str) -> None:
        self._upsert_stack("level", label)
        self.data["level_id"] = level_id
        self._truncate_after("level")

    def set_term(self, label: str, term_id: int | str) -> None:
        self._upsert_stack("term", label)
        self.data["term_id"] = term_id
        self._truncate_after("term")

    def set_subject(self, label: str, subject_id: int) -> None:
        self._upsert_stack("subject", label)
        self.data["subject_id"] = subject_id
        self._truncate_after("subject")

    def set_section(self, label: str, section: str) -> None:
        self._upsert_stack("section", label)
        self.data["section"] = section
        self._truncate_after("section")

    def set_year(self, label: str, year_id: int) -> None:
        self._upsert_stack("year", label)
        self.data["year_id"] = year_id
        self._truncate_after("year")

    def set_lecturer(self, label: str, lecturer_id: int) -> None:
        self._upsert_stack("lecturer", label)
        self.data["lecturer_id"] = lecturer_id
        self._truncate_after("lecturer")

    def set_lecture(self, title: str) -> None:
        self._upsert_stack("lecture", title)
        self.data["lecture_title"] = title
        self._truncate_after("lecture")

    # Composite navigation helpers
    def go_levels_list(self) -> None:
        self.reset()
        self._upsert_stack("level", "")
        self._truncate_after("level")

    def go_subject_list(self) -> None:
        self._truncate_after("term")
        for key in ("subject_id", "section", "year_id", "lecturer_id", "lecture_title", "category"):
            self.data.pop(key, None)
        self._upsert_stack("subject_list", "")
        self._truncate_after("subject_list")

