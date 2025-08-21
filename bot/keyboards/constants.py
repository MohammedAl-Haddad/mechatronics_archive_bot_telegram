from telegram import ReplyKeyboardMarkup

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

SECTION_LABELS = {
    "theory":    "📚 نظري",
    "discussion":"💬 مناقشة",
    "lab":       "🧪 عملي",
    "syllabus":  "📄 المفردات الدراسية",
    "apps":      "📱 تطبيقات",
}
LABEL_TO_SECTION = {v: k for k, v in SECTION_LABELS.items()}

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

CHOOSE_YEAR_FOR_LECTURER   = "📅 اختر السنة"
LIST_LECTURES_FOR_LECTURER = "📚 محاضرات هذا المحاضر"

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        ["📚 المستويات", "🗂 الخطة الدراسية"],
        ["🔧 البرامج الهندسية", " بحث"],
        ["📡 القنوات والمجموعات", "🆘 مساعدة"],
        ["📨 تواصل معنا"],
    ],
    resize_keyboard=True,
    one_time_keyboard=True,
    input_field_placeholder="اختر خيارًا من القائمة  ⬇️",
)

__all__ = [
    "TERM_MENU_SHOW_SUBJECTS",
    "TERM_MENU_PLAN",
    "TERM_MENU_LINKS",
    "TERM_MENU_ADV_SEARCH",
    "BACK",
    "BACK_TO_LEVELS",
    "BACK_TO_SUBJECTS",
    "FILTER_BY_YEAR",
    "FILTER_BY_LECTURER",
    "LIST_LECTURES",
    "YEAR_MENU_LECTURES",
    "SECTION_LABELS",
    "LABEL_TO_SECTION",
    "CATEGORY_TO_LABEL",
    "LABEL_TO_CATEGORY",
    "CHOOSE_YEAR_FOR_LECTURER",
    "LIST_LECTURES_FOR_LECTURER",
    "main_menu",
]
