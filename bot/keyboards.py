# keyboards.py
# هذا الملف يعرّف لوحات المفاتيح "Reply Keyboard" فقط (المستخدمة حاليًا في bot.py)
# ويولّد القوائم الديناميكية للمستويات، الأترام، المواد، الأقسام، الفلاتر، السنوات، المحاضرين، وعناوين المحاضرات.

from telegram import ReplyKeyboardMarkup
from .config import ADMIN_USER_IDS
# -----------------------------------------------------------------------------
# ثوابت نصوص الأزرار (يجب أن تبقى متطابقة مع ما يستخدمه bot.py)
# -----------------------------------------------------------------------------
TERM_MENU_SHOW_SUBJECTS = "📖 عرض المواد"
TERM_MENU_PLAN          = "🗂 الخطة الدراسية"
TERM_MENU_LINKS         = "🔗 روابط المجموعات والقنوات"
TERM_MENU_ADV_SEARCH    = "🔎 البحث المتقدم"

BACK               = "🔙 العودة"
BACK_TO_LEVELS     = "🔙 العودة لقائمة المستويات"
BACK_TO_SUBJECTS   = "🔙 العودة لقائمة المواد"

FILTER_BY_YEAR     = "📅 حسب السنة"
FILTER_BY_LECTURER = "👤 حسب المحاضر"
LIST_LECTURES      = "📚 عرض المحاضرات"

YEAR_MENU_LECTURES = "📚 المحاضرات"

# تسميات الأقسام (واجهة) ↔ رموز الأقسام (داخل قاعدة البيانات)
SECTION_LABELS = {
    "theory":    "📚 نظري",
    "discussion":"💬 مناقشة",
    "lab":       "🧪 عملي",
    "syllabus":  "📄 المفردات الدراسية",
    "apps":      "📱 تطبيقات",
}
LABEL_TO_SECTION = {v: k for k, v in SECTION_LABELS.items()}

# تسميات عربية لتصنيفات الملفات (واجهة) ↔ أسماء التصنيفات في القاعدة
CATEGORY_TO_LABEL = {
    "lecture":       "📄 ملف المحاضرة",
    "slides":        "📑 سلايدات المحاضرة",
    "audio":         "🎧 تسجيل صوتي",
    "video":         "🎥 تسجيل فيديو",
    "board_images":  "🖼️ صور السبورة",
    "external_link": "🔗 روابط خارجية",
    "exam":          "📝 الامتحانات",
    "booklet":       "📘 الملازم",
    "summary":       "🧾 ملخص",
    "notes":         "🗒️ ملاحظات",
    "simulation":    "🧪 محاكاة",
    "mind_map":      "🗺️ خرائط ذهنية",
    "transcript":    "⌨️ تفريغ صوتي",
    "related":       "📎 ملفات ذات صلة",
}
LABEL_TO_CATEGORY = {v: k for k, v in CATEGORY_TO_LABEL.items()}

# في قائمة المحاضر: خيارات إضافية
CHOOSE_YEAR_FOR_LECTURER   = "📅 اختر السنة"
LIST_LECTURES_FOR_LECTURER = "📚 محاضرات هذا المحاضر"

# -----------------------------------------------------------------------------
# مُساعد داخلي لتجزئة العناصر إلى صفوف بعدد أعمدة ثابت (لتناسق حجم القوائم)
# -----------------------------------------------------------------------------
def _rows(items: list[str], cols: int = 2) -> list[list[str]]:
    """
    يُقسّم قائمة العناصر إلى صفوف بعدد أعمدة محدد (افتراضيًا عمودان)
    للحصول على مظهر متناسق عبر كل القوائم.
    """
    keyboard, row = [], []
    for item in items:
        row.append(item)
        if len(row) == cols:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    return keyboard

# -----------------------------------------------------------------------------
# القائمة الرئيسية (Reply Keyboard)
# -----------------------------------------------------------------------------
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        ["📚 المستويات", "🗂 الخطة الدراسية"],
        ["🔧 البرامج الهندسية", "🔍 بحث"],
        ["📡 القنوات والمجموعات", "🆘 مساعدة"],
        ["📨 تواصل معنا"],
    ],
    resize_keyboard=True,
    one_time_keyboard=True,
    input_field_placeholder="اختر خيارًا من القائمة  ⬇️",
)

# -----------------------------------------------------------------------------
# مولدات لوحات المفاتيح الديناميكية المستخدمة في bot.py
# -----------------------------------------------------------------------------
def generate_levels_keyboard(levels: list) -> ReplyKeyboardMarkup:
    """
    يعرض قائمة المستويات (بالأسماء فقط).
    levels: [(id, name), ...] — نستخدم الاسم في الزر.
    """
    names = [name for _id, name in levels]
    keyboard = _rows(names, cols=2)
    keyboard.append(["🔙 العودة للقائمة الرئيسية"])
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="إختر المستوى الدراسي  ⬇️",
    )

def generate_terms_keyboard(terms: list) -> ReplyKeyboardMarkup:
    """
    يعرض قائمة الأترام التابعة لمستوى محدد.
    terms: [(id, name), ...]
    """
    names = [name for _id, name in terms]
    keyboard = _rows(names, cols=2)
    keyboard.append([BACK])
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="إختر الفصل الدراسي  ⬇️",
    )

def generate_subjects_keyboard(subjects: list) -> ReplyKeyboardMarkup:
    """
    يعرض قائمة مواد الترم الحالي.
    subjects: [(name,), ...]
    """
    names = [name for (name,) in subjects]
    keyboard = _rows(names, cols=2)
    keyboard.append([BACK])
    keyboard.append([BACK_TO_LEVELS])  # الرجوع مباشرة للمستويات من هنا مفيد
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="إختر المقرر الدراسي  ⬇️",
    )

def generate_term_menu_keyboard_dynamic(flags: dict) -> ReplyKeyboardMarkup:
    """
    ينشئ أزرار قائمة الترم حسب المتوفر فعليًا:
    flags = {'has_subjects': bool, 'has_syllabus': bool, 'has_links': bool}
    """
    items: list[str] = []
    if flags.get("has_subjects"):
        items.append(TERM_MENU_SHOW_SUBJECTS)
    if flags.get("has_syllabus"):
        items.append(TERM_MENU_PLAN)
    if flags.get("has_links"):
        items.append(TERM_MENU_LINKS)
    # إظهار البحث إن توفّر أي محتوى
    if flags.get("has_subjects") or flags.get("has_syllabus") or flags.get("has_links"):
        items.append(TERM_MENU_ADV_SEARCH)

    keyboard = _rows(items, cols=2)
    keyboard.append([BACK, BACK_TO_LEVELS])
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def generate_subject_sections_keyboard_dynamic(sections: list[str]) -> ReplyKeyboardMarkup:
    """
    يعرض فقط الأقسام الموجودة فعليًا للمادة (حسب جدول materials).
    sections: قيم داخلية مثل 'theory','discussion','lab','syllabus','apps'
    """
    labels = [SECTION_LABELS[s] for s in sections if s in SECTION_LABELS]
    keyboard = _rows(labels, cols=2)
    keyboard.append([BACK])
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def generate_section_filters_keyboard_dynamic(
    years_exist: bool, lecturers_exist: bool, lectures_exist: bool
) -> ReplyKeyboardMarkup:
    """
    يوفّر فلاتر القسم: حسب السنة/المحاضر/عرض كل المحاضرات.
    كما يضيف أزرار الرجوع المناسبة.
    """
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
    """
    يعرض السنوات المتاحة لقسم/مادة (وقد تكون هجري فقط كما في مشروعك).
    years: [(id, name), ...] — نعرض الاسم كزر.
    """
    names = [name for _id, name in years]
    keyboard = _rows(names, cols=2)
    keyboard.append([BACK, BACK_TO_SUBJECTS])
    keyboard.append([BACK_TO_LEVELS])
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def generate_lecturers_keyboard(lecturers: list[tuple[int, str]]) -> ReplyKeyboardMarkup:
    """
    يعرض المحاضرين المرتبطين بالقسم/المادة.
    lecturers: [(id, name), ...] — نعرض الاسم كزر.
    """
    names = [name for _id, name in lecturers]
    keyboard = _rows(names, cols=2)
    keyboard.append([BACK, BACK_TO_SUBJECTS])
    keyboard.append([BACK_TO_LEVELS])
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def generate_lecture_titles_keyboard(titles: list[str]) -> ReplyKeyboardMarkup:
    """
    يعرض عناوين المحاضرات (قد تُصفّى حسب سنة/محاضر).
    """
    keyboard = _rows(titles, cols=2)
    keyboard.append([BACK, BACK_TO_SUBJECTS])
    keyboard.append([BACK_TO_LEVELS])
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def generate_lecturer_filter_keyboard(years_exist: bool, lectures_exist: bool) -> ReplyKeyboardMarkup:
    """
    داخل صفحة المحاضر: إمّا اختيار سنة لذلك المحاضر أو عرض كل محاضراته.
    """
    row: list[str] = []
    if years_exist:
        row.append(CHOOSE_YEAR_FOR_LECTURER)
    if lectures_exist:
        row.append(LIST_LECTURES_FOR_LECTURER)

    keyboard: list[list[str]] = []
    if row:
        keyboard.append(row)
    keyboard.append([BACK])  # رجوع خطوة واحدة
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def generate_year_category_menu_keyboard(categories: list[str], lectures_exist: bool) -> ReplyKeyboardMarkup:
    """
    شاشة سنة معينة: تعرض (📚 المحاضرات) + التصنيفات العامة للسنة
    (مع إخفاء مرفقات المحاضرات مثل السلايدات والصوتيات… حسب منطق db.list_categories_for_subject_section_year).
    """
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
    """
    شاشة محاضرة محددة: تعرض تصنيفات الملفات الخاصة بهذه المحاضرة (سلايدات/صوت/فيديو/صور سبورة/…).
    """
    labels = [CATEGORY_TO_LABEL.get(c, c) for c in categories]
    keyboard = _rows(labels, cols=2)
    keyboard.append([BACK, BACK_TO_SUBJECTS])
    keyboard.append([BACK_TO_LEVELS])
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


