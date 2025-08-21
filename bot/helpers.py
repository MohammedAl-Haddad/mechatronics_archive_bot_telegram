# helpers.py
# إدارة حالة التنقل للمستخدم (Navigation State) داخل bot.py
# - نخزّن الحالة في context.user_data["nav"] بالشكل:
#   {"stack": [(node_type, label), ...], "data": {...}}
# - stack: يمثل مسار الشاشات (level -> term -> subject -> ...)
# - data: يحمل المعرّفات/القيم (level_id, term_id, subject_id, ...)

NAV_KEY = "nav"

# ---------------------------------------------------------------------------
# أدوات داخلية
# ---------------------------------------------------------------------------
def _get_nav(user_data: dict) -> dict:
    """يضمن وجود هيكل nav الأساسي داخل user_data."""
    nav = user_data.get(NAV_KEY)
    if not isinstance(nav, dict) or "stack" not in nav or "data" not in nav:
        nav = {"stack": [], "data": {}}
        user_data[NAV_KEY] = nav
    return nav

def _upsert_stack(nav: dict, node_type: str, label: str) -> None:
    """يضيف/يحدّث عقدة في stack بحسب نوعها."""
    for i, (t, _) in enumerate(nav["stack"]):
        if t == node_type:
            nav["stack"][i] = (node_type, label)
            return
    nav["stack"].append((node_type, label))

def _truncate_after(nav: dict, node_type: str) -> None:
    """يحذف كل ما بعد node_type في stack (لضمان تماسك المسار)."""
    for i, (t, _) in enumerate(nav["stack"]):
        if t == node_type:
            del nav["stack"][i + 1 :]
            return

# ---------------------------------------------------------------------------
# مفاتيح البيانات المرتبطة بكل نوع عقدة (لتنظيف data عند الرجوع)
# ---------------------------------------------------------------------------

# helpers.py

TYPE_TO_KEYS = {
    "level": ["level_id"],
    "term": ["term_id"],
    "subject": ["subject_id"],
    "section": ["section"],
    "year": ["year_id"],
    "lecturer": ["lecturer_id"],

    # 🎯 ثبت عنوان المحاضرة هنا فقط
    "lecture": ["lecture_title"],

    # مشاهد واجهة لا تحمل مفاتيح بيانات
    "term_list": [],
    "subject_list": [],
    "year_list": [],
    "lecturer_list": [],
    "lecture_list": [],
    "year_category_menu": [],
    "lecture_category_menu": [],
}


# ---------------------------------------------------------------------------
# عمليات عامة على الحالة
# ---------------------------------------------------------------------------
def nav_reset(user_data: dict) -> None:
    """يمسح كل المسار والبيانات (عودة للجذر)."""
    nav = _get_nav(user_data)
    nav["stack"].clear()
    nav["data"].clear()

def nav_back_to_levels(user_data: dict) -> None:
    """رجوع للجذر (قائمة المستويات)."""
    nav_reset(user_data)

def nav_get_ids(user_data: dict):
    """يرجع (level_id, term_id) إن وُجدا، وإلا (None, None)."""
    nav = _get_nav(user_data)
    return nav["data"].get("level_id"), nav["data"].get("term_id")

def nav_get_labels(user_data: dict):
    """يرجع (level_label, term_label) من stack لعرضها للمستخدم."""
    nav = _get_nav(user_data)
    level_label = term_label = None
    for t, lbl in nav.get("stack", []):
        if t == "level":
            level_label = lbl
        elif t == "term":
            term_label = lbl
    return level_label, term_label

def nav_back_one(user_data: dict) -> None:
    """يرجع خطوة واحدة في المسار ويمسح مفاتيحها من data."""
    nav = _get_nav(user_data)
    if not nav["stack"]:
        return
    node_type, _ = nav["stack"].pop()
    for k in TYPE_TO_KEYS.get(node_type, []):
        nav["data"].pop(k, None)

def nav_push_view(user_data: dict, node_type: str, label: str = "") -> None:
    """
    يدفع شاشة/عقدة واجهة بدون مفاتيح إضافية (مثل: term_list, subject_list, ...).
    """
    nav = _get_nav(user_data)
    _upsert_stack(nav, node_type, label)
    _truncate_after(nav, node_type)

# ---------------------------------------------------------------------------
# محددات المستوى/الترم/المادة/القسم/… (تضع القيمة وتمسح ما بعدها)
# ---------------------------------------------------------------------------
def nav_set_level(user_data: dict, label: str, level_id: int | str) -> None:
    nav = _get_nav(user_data)
    _upsert_stack(nav, "level", label)
    nav["data"]["level_id"] = level_id
    _truncate_after(nav, "level")

def nav_set_term(user_data: dict, label: str, term_id: int | str) -> None:
    nav = _get_nav(user_data)
    _upsert_stack(nav, "term", label)
    nav["data"]["term_id"] = term_id
    _truncate_after(nav, "term")

def nav_set_subject(user_data: dict, label: str, subject_id: int) -> None:
    nav = _get_nav(user_data)
    _upsert_stack(nav, "subject", label)
    nav["data"]["subject_id"] = subject_id
    _truncate_after(nav, "subject")

def nav_set_section(user_data: dict, label: str, section: str) -> None:
    nav = _get_nav(user_data)
    _upsert_stack(nav, "section", label)
    nav["data"]["section"] = section
    _truncate_after(nav, "section")

def nav_set_year(user_data: dict, label: str, year_id: int) -> None:
    nav = _get_nav(user_data)
    _upsert_stack(nav, "year", label)
    nav["data"]["year_id"] = year_id
    _truncate_after(nav, "year")

def nav_set_lecturer(user_data: dict, label: str, lecturer_id: int) -> None:
    nav = _get_nav(user_data)
    _upsert_stack(nav, "lecturer", label)
    nav["data"]["lecturer_id"] = lecturer_id
    _truncate_after(nav, "lecturer")

def nav_set_lecture(user_data: dict, title: str) -> None:
    """
    تثبيت عنوان محاضرة محددة، ثم إغلاق أي مسار أعمق.
    """
    nav = _get_nav(user_data)
    _upsert_stack(nav, "lecture", title)
    nav["data"]["lecture_title"] = title
    _truncate_after(nav, "lecture")

# ---------------------------------------------------------------------------
# انتقالات جاهزة (اختصارات)
# ---------------------------------------------------------------------------
def nav_go_levels_list(user_data: dict) -> None:
    """
    الانتقال لقائمة المستويات: نعيد التهيئة ثم نضع عقدة 'level' فارغة
    ليفهم البوت أن الشاشة التالية هي اختيار المستوى.
    """
    nav_reset(user_data)
    nav = _get_nav(user_data)
    _upsert_stack(nav, "level", "")
    _truncate_after(nav, "level")

def nav_go_subject_list(user_data: dict) -> None:
    """
    الانتقال لقائمة المواد للحالة الحالية:
    - نبقي حتى طبقة 'term'
    - نمسح أي بيانات أعمق (subject/year/lecturer/lecture_title/category/section)
    - نضع عقدة 'subject_list' كواجهة حالية.
    """
    nav = _get_nav(user_data)
    _truncate_after(nav, "term")  # أبقِ حتى الترم

    # تنظيف أي مفاتيح أعمق من الترم
    for k in ("subject_id", "section", "year_id", "lecturer_id", "lecture_title", "category"):
        nav["data"].pop(k, None)

    _upsert_stack(nav, "subject_list", "")
    _truncate_after(nav, "subject_list")

