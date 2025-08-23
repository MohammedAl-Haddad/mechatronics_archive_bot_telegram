from telegram import ReplyKeyboardMarkup

from .constants import (
    TERM_MENU_SHOW_SUBJECTS,
    TERM_MENU_PLAN,
    TERM_MENU_LINKS,
    TERM_MENU_ADV_SEARCH,
    BACK,
    BACK_TO_LEVELS,
    BACK_TO_SUBJECTS,
    FILTER_BY_YEAR,
    FILTER_BY_LECTURER,
    LIST_LECTURES,
    YEAR_MENU_LECTURES,
    SECTION_LABELS,
    CATEGORY_TO_LABEL,
    CHOOSE_YEAR_FOR_LECTURER,
    LIST_LECTURES_FOR_LECTURER,
)


def _rows(items: list[str], cols: int = 2) -> list[list[str]]:
    """Split items into rows with a fixed number of columns, skipping empties."""
    items = [i for i in items if i]
    keyboard, row = [], []
    for item in items:
        row.append(item)
        if len(row) == cols:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    return keyboard


def generate_levels_keyboard(levels: list) -> ReplyKeyboardMarkup:
    """Display available levels."""
    names = [name for _id, name in levels]
    keyboard = _rows(names, cols=2)
    keyboard.append(["🔙 العودة للقائمة الرئيسية"])
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="إختر المستوى الدراسي  ⬇️",
    )


def generate_terms_keyboard(terms: list) -> ReplyKeyboardMarkup:
    """Display terms for a specific level."""
    names = [name for _id, name in terms]
    keyboard = _rows(names, cols=2)
    keyboard.append([BACK])
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="إختر الفصل الدراسي  ⬇️",
    )


def generate_subjects_keyboard(subjects: list) -> ReplyKeyboardMarkup:
    """Display subjects for the current term."""
    names = [name for (name,) in subjects]
    keyboard = _rows(names, cols=2)
    keyboard.append([BACK])
    keyboard.append([BACK_TO_LEVELS])
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="إختر المقرر الدراسي  ⬇️",
    )


def generate_term_menu_keyboard_dynamic(flags: dict) -> ReplyKeyboardMarkup:
    """Create term menu buttons based on available data."""
    items: list[str] = []
    if flags.get("has_subjects"):
        items.append(TERM_MENU_SHOW_SUBJECTS)
    if flags.get("has_syllabus"):
        items.append(TERM_MENU_PLAN)
    if flags.get("has_links"):
        items.append(TERM_MENU_LINKS)
    if flags.get("has_subjects") or flags.get("has_syllabus") or flags.get("has_links"):
        items.append(TERM_MENU_ADV_SEARCH)

    keyboard = _rows(items, cols=2)
    keyboard.append([BACK, BACK_TO_LEVELS])
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def generate_subject_sections_keyboard_dynamic(sections: list[str]) -> ReplyKeyboardMarkup:
    """Display available sections for a subject."""
    labels = [SECTION_LABELS[s] for s in sections if s in SECTION_LABELS]
    keyboard = _rows(labels, cols=2)
    keyboard.append([BACK])
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def generate_section_filters_keyboard_dynamic(
    years_exist: bool, lecturers_exist: bool, lectures_exist: bool
) -> ReplyKeyboardMarkup:
    """Provide section filters for year, lecturer, and lectures."""
    first_row: list[str] = []
    if years_exist:
        first_row.append(FILTER_BY_YEAR)
    if lecturers_exist:
        first_row.append(FILTER_BY_LECTURER)

    keyboard: list[list[str]] = []
    if first_row:
        keyboard.append(first_row)
    if lectures_exist:
        keyboard.append([LIST_LECTURES])

    keyboard.append([BACK, BACK_TO_SUBJECTS])
    keyboard.append([BACK_TO_LEVELS])
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def generate_years_keyboard(years: list[tuple[int, str]]) -> ReplyKeyboardMarkup:
    """Display available years for a subject/section."""
    names = [name for _id, name in years]
    keyboard = _rows(names, cols=2)
    keyboard.append([BACK, BACK_TO_SUBJECTS])
    keyboard.append([BACK_TO_LEVELS])
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def generate_lecturers_keyboard(lecturers: list[tuple[int, str]]) -> ReplyKeyboardMarkup:
    """Display lecturers for the subject/section."""
    names = [name for _id, name in lecturers]
    keyboard = _rows(names, cols=2)
    keyboard.append([BACK, BACK_TO_SUBJECTS])
    keyboard.append([BACK_TO_LEVELS])
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def generate_lecture_titles_keyboard(titles: list[str]) -> ReplyKeyboardMarkup:
    """Display lecture titles."""
    keyboard = _rows(titles, cols=2)
    keyboard.append([BACK, BACK_TO_SUBJECTS])
    keyboard.append([BACK_TO_LEVELS])
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def generate_lecturer_filter_keyboard(
    years_exist: bool, lectures_exist: bool
) -> ReplyKeyboardMarkup:
    """Provide filters when viewing a lecturer."""
    row: list[str] = []
    if years_exist:
        row.append(CHOOSE_YEAR_FOR_LECTURER)
    if lectures_exist:
        row.append(LIST_LECTURES_FOR_LECTURER)

    keyboard: list[list[str]] = []
    if row:
        keyboard.append(row)
    keyboard.append([BACK])
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def generate_year_category_menu_keyboard(
    categories: list[str], lectures_exist: bool
) -> ReplyKeyboardMarkup:
    """Display categories for a given year."""
    labels = [CATEGORY_TO_LABEL.get(c, c) for c in categories]
    first_row: list[str] = []
    if lectures_exist:
        first_row.append(YEAR_MENU_LECTURES)

    keyboard: list[list[str]] = []
    if first_row:
        keyboard.append(first_row)
    keyboard += _rows(labels, cols=2)

    keyboard.append([BACK, BACK_TO_SUBJECTS])
    keyboard.append([BACK_TO_LEVELS])
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def generate_lecture_category_menu_keyboard(categories: list[str]) -> ReplyKeyboardMarkup:
    """Display categories for a specific lecture."""
    labels = [CATEGORY_TO_LABEL.get(c, c) for c in categories]
    keyboard = _rows(labels, cols=2)
    keyboard.append([BACK, BACK_TO_SUBJECTS])
    keyboard.append([BACK_TO_LEVELS])
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


__all__ = [
    "generate_levels_keyboard",
    "generate_terms_keyboard",
    "generate_subjects_keyboard",
    "generate_term_menu_keyboard_dynamic",
    "generate_subject_sections_keyboard_dynamic",
    "generate_section_filters_keyboard_dynamic",
    "generate_years_keyboard",
    "generate_lecturers_keyboard",
    "generate_lecture_titles_keyboard",
    "generate_lecturer_filter_keyboard",
    "generate_year_category_menu_keyboard",
    "generate_lecture_category_menu_keyboard",
]
