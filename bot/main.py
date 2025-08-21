# main.py
# نقطة الدخول للبوت (وضع Reply Keyboard)
# تنظير: لا تغييرات على الخوارزمية، فقط تنظيف الاستيرادات

import os
import asyncio
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

from .config import BOT_TOKEN

# --- DB: استيراد صريح للدوال المستخدمة فقط ---
from .db import (
    init_db,
    get_levels,
    get_terms_by_level,
    get_subjects_by_level_and_term,
    term_feature_flags,
    get_available_sections_for_subject,
    get_years_for_subject_section,
    get_lecturers_for_subject_section,
    has_lecture_category,
    get_years_for_subject_section_lecturer,
    list_lecture_titles,
    list_lecture_titles_by_year,
    list_lecture_titles_by_lecturer,
    list_lecture_titles_by_lecturer_year,
    get_subject_id_by_name,
    get_materials_by_category,
    get_lecture_materials,
    list_categories_for_subject_section_year,
    list_categories_for_lecture,
)

# from reaction import handle_reaction

# --- Keyboards (Reply) ---
from .keyboards import (
    main_menu,
    generate_levels_keyboard,
    generate_terms_keyboard,
    generate_subjects_keyboard,
    generate_term_menu_keyboard_dynamic,
    generate_subject_sections_keyboard_dynamic,
    generate_lecturer_filter_keyboard,
    generate_section_filters_keyboard_dynamic,
    generate_years_keyboard,
    generate_lecturers_keyboard,
    generate_lecture_titles_keyboard,
    generate_year_category_menu_keyboard,
    generate_lecture_category_menu_keyboard,
    TERM_MENU_SHOW_SUBJECTS,
    TERM_MENU_PLAN,
    TERM_MENU_LINKS,
    TERM_MENU_ADV_SEARCH,
    LABEL_TO_SECTION,
    BACK_TO_LEVELS,
    BACK_TO_SUBJECTS,
    FILTER_BY_YEAR,
    FILTER_BY_LECTURER,
    LIST_LECTURES,
    CHOOSE_YEAR_FOR_LECTURER,
    LIST_LECTURES_FOR_LECTURER,
    YEAR_MENU_LECTURES,
    LABEL_TO_CATEGORY,
)

# --- Nav helpers ---
from .helpers import (
    nav_set_subject,
    nav_set_section,
    nav_back_one,
    nav_get_ids,
    nav_get_labels,
    nav_set_level,
    nav_set_term,
    nav_back_to_levels,
    nav_push_view,
    nav_go_levels_list,
    nav_go_subject_list,
    nav_set_year,
    nav_set_lecturer,
    nav_set_lecture  
)


# --------------------------------------------------------------------------
# إعداد التسجيل لرؤية الرسائل التفصيلية
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 مرحبًا بك في بوت أرشيف قسم الميكاترونكس.\nاختر من القائمة:",
        reply_markup=main_menu)







# --------------------------------------------------------------------------
async def render_state(update: Update, context: ContextTypes.DEFAULT_TYPE):
    level_id, term_id = nav_get_ids(context.user_data)
    level_label, term_label = nav_get_labels(context.user_data)
    nav = context.user_data.get("nav", {"stack": []})
    stack = nav.get("stack", [])

    # لا شيء محدد → القائمة الرئيسية
    if not stack:
        return await update.message.reply_text("اختر من القائمة:", reply_markup=main_menu)
    
    top_type = stack[-1][0]

    if top_type == "level":
        levels = await get_levels()
        return await update.message.reply_text("اختر المستوى:", reply_markup=generate_levels_keyboard(levels))

    if top_type == "term_list":
        terms = await get_terms_by_level(level_id)
        return await update.message.reply_text(f"المستوى: {level_label}\nاختر الترم:", reply_markup=generate_terms_keyboard(terms))

    if top_type == "term":
        flags = await term_feature_flags(level_id, term_id)
        return await update.message.reply_text(
            f"المستوى: {level_label}\nالترم: {term_label}\nاختر خيارًا:",
            reply_markup=generate_term_menu_keyboard_dynamic(flags),
        )

    if top_type == "subject":
        nav = context.user_data.get("nav", {})
        subject_label = nav.get("stack", [])[-1][1] if nav.get("stack") else ""
        subject_id = nav.get("data", {}).get("subject_id")
        sections = await get_available_sections_for_subject(subject_id) if subject_id else []
        msg = f"المادة: {subject_label}\nاختر القسم:" if sections else "لا توجد أقسام متاحة لهذه المادة حتى الآن."
        return await update.message.reply_text(msg, reply_markup=generate_subject_sections_keyboard_dynamic(sections))

    if top_type == "subject_list":
        subjects = await get_subjects_by_level_and_term(level_id, term_id)
        msg = "اختر المادة:" if subjects else "لا توجد مواد لهذا الترم."
        return await update.message.reply_text(msg, reply_markup=generate_subjects_keyboard(subjects))

    if top_type == "section":
        subject_id = nav.get("data", {}).get("subject_id")
        section_code = nav.get("data", {}).get("section")
        years = await get_years_for_subject_section(subject_id, section_code)
        lecturers = await get_lecturers_for_subject_section(subject_id, section_code)
        lectures_exist = await has_lecture_category(subject_id, section_code)
        return await update.message.reply_text(
            "اختر طريقة التصفية:",
            reply_markup=generate_section_filters_keyboard_dynamic(bool(years), bool(lecturers), lectures_exist),
        )

    if top_type == "year":
        subject_id = nav.get("data", {}).get("subject_id")
        section_code = nav.get("data", {}).get("section")
        year_label = stack[-1][1]
        year_id = nav.get("data", {}).get("year_id")
        titles = await list_lecture_titles_by_year(subject_id, section_code, year_id)
        msg = f"السنة: {year_label}\nاختر محاضرة:" if titles else "لا توجد محاضرات لهذه السنة."
        return await update.message.reply_text(msg, reply_markup=generate_lecture_titles_keyboard(titles))

    if top_type == "lecturer":
        subject_id = nav.get("data", {}).get("subject_id")
        section_code = nav.get("data", {}).get("section")
        lecturer_label = stack[-1][1]
        lecturer_id = nav.get("data", {}).get("lecturer_id")
        years = await get_years_for_subject_section_lecturer(subject_id, section_code, lecturer_id)
        lectures_exist = await has_lecture_category(subject_id, section_code) or False
        return await update.message.reply_text(
            f"المحاضر: {lecturer_label}\nاختر خيارًا:",
            reply_markup=generate_lecturer_filter_keyboard(bool(years), lectures_exist),
        )

    if top_type == "year_list":
        subject_id = nav.get("data", {}).get("subject_id")
        section_code = nav.get("data", {}).get("section")
        lecturer_id = nav.get("data", {}).get("lecturer_id")
        if lecturer_id:
            years = await get_years_for_subject_section_lecturer(subject_id, section_code, lecturer_id)
            msg = "اختر السنة (للمحاضر المحدد):"
        else:
            years = await get_years_for_subject_section(subject_id, section_code)
            msg = "اختر السنة:"
        return await update.message.reply_text(msg, reply_markup=generate_years_keyboard(years))

    if top_type == "lecturer_list":
        subject_id = nav.get("data", {}).get("subject_id")
        section_code = nav.get("data", {}).get("section")
        lecturers = await get_lecturers_for_subject_section(subject_id, section_code)
        return await update.message.reply_text("اختر المحاضر:", reply_markup=generate_lecturers_keyboard(lecturers))

    if top_type == "lecture_list":
        subject_id = nav.get("data", {}).get("subject_id")
        section_code = nav.get("data", {}).get("section")
        year_id = nav.get("data", {}).get("year_id")
        lecturer_id = nav.get("data", {}).get("lecturer_id")

        titles = await list_lecture_titles(subject_id, section_code)
        heading = "اختر محاضرة:"

        if year_id and lecturer_id:
            titles = await list_lecture_titles_by_lecturer_year(subject_id, section_code, lecturer_id, year_id)
            heading = "اختر محاضرة (محاضر + سنة):"
        elif lecturer_id:
            titles = await list_lecture_titles_by_lecturer(subject_id, section_code, lecturer_id)
            heading = "اختر محاضرة (حسب المحاضر):"
        elif year_id:
            titles = await list_lecture_titles_by_year(subject_id, section_code, year_id)
            heading = "اختر محاضرة (حسب السنة):"

        msg = heading if titles else "لا توجد محاضرات مطابقة."
        return await update.message.reply_text(msg, reply_markup=generate_lecture_titles_keyboard(titles))

    if top_type == "year_category_menu":
        subject_id = nav.get("data", {}).get("subject_id")
        section_code = nav.get("data", {}).get("section")
        year_id = nav.get("data", {}).get("year_id")
        lecturer_id = nav.get("data", {}).get("lecturer_id")
        if not year_id:
            return await render_state(update, context)
        if lecturer_id:
            lectures_exist = bool(await list_lecture_titles_by_lecturer_year(subject_id, section_code, lecturer_id, year_id))
            cats = await list_categories_for_subject_section_year(subject_id, section_code, year_id, lecturer_id=lecturer_id)
        else:
            lectures_exist = bool(await list_lecture_titles_by_year(subject_id, section_code, year_id))
            cats = await list_categories_for_subject_section_year(subject_id, section_code, year_id)
        return await update.message.reply_text("اختر نوع المحتوى:", reply_markup=generate_year_category_menu_keyboard(cats, lectures_exist))

    if top_type == "lecture_category_menu":
        subject_id = nav.get("data", {}).get("subject_id")
        section_code = nav.get("data", {}).get("section")
        year_id = nav.get("data", {}).get("year_id")
        lecturer_id = nav.get("data", {}).get("lecturer_id")
        lecture_title = nav.get("data", {}).get("lecture_title", "")
        cats = await list_categories_for_lecture(subject_id, section_code, lecture_title, year_id=year_id, lecturer_id=lecturer_id)
        msg = f"المحاضرة: {lecture_title}\nاختر نوع الملف:" if cats else "لا توجد أنواع ملفات لهذه المحاضرة."
        return await update.message.reply_text(msg, reply_markup=generate_lecture_category_menu_keyboard(cats))

    return await update.message.reply_text("اختر من القائمة:", reply_markup=main_menu)

# --------------------------------------------------------------------------
async def echo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text if update.message else ""

    # معالجة ردود الفعل (إن كانت مفعّلة لديك)
    # await handle_reaction(update, context)


    # دخول قائمة المستويات
    if text == BACK_TO_LEVELS:
        nav_go_levels_list(context.user_data)
        return await render_state(update, context)

    # زر "العودة لقائمة المواد"
    if text == BACK_TO_SUBJECTS:
        level_id, term_id = nav_get_ids(context.user_data)
        if level_id and term_id:
            nav_go_subject_list(context.user_data)
            return await render_state(update, context)
        nav_go_levels_list(context.user_data)
        return await render_state(update, context)

    # 1) دخول قائمة المستويات
    if text == "📚 المستويات":
        nav_back_to_levels(context.user_data)
        levels = await get_levels()
        return await update.message.reply_text("اختر المستوى:", reply_markup=generate_levels_keyboard(levels))

    # 2) زر العودة إلى الرئيسية
    if text == "🔙 العودة للقائمة الرئيسية":
        nav_back_to_levels(context.user_data)
        return await update.message.reply_text("تم الرجوع إلى القائمة الرئيسية ⬇️", reply_markup=main_menu)

    # # 3) زر الرجوع الذكي (خطوة واحدة)
    # if text == "🔙 العودة":
    #     nav_back_one(context.user_data)
    #     return await render_state(update, context)

    # 3) زر الرجوع الذكي (خطوة واحدة)
    if text == "🔙 العودة":
        nav = context.user_data.get("nav", {})
        stack = nav.get("stack", [])

        if stack:
            top = stack[-1][0]

            # ✅ من شاشة السنة → ارجع لقائمة السنوات
            if top == "year_category_menu":
                nav_back_one(context.user_data)  # أزل شاشة السنة
                nav_back_one(context.user_data)  # أزل طبقة year للعودة إلى year_list
                return await render_state(update, context)

            # ✅ من شاشة تصنيفات المحاضرة → ارجع لقائمة العناوين
            if top == "lecture_category_menu":
                nav_back_one(context.user_data)  # أزل شاشة تصنيفات المحاضرة
                nav_back_one(context.user_data)  # أزل طبقة lecture للعودة إلى lecture_list
                return await render_state(update, context)

        # الافتراضي: خطوة واحدة
        nav_back_one(context.user_data)
        return await render_state(update, context)


    # 4) اختيار مستوى؟
    levels = await get_levels()
    levels_map = {name: _id for _id, name in levels}
    if text in levels_map:
        level_id = levels_map[text]
        nav_set_level(context.user_data, text, level_id)
        terms = await get_terms_by_level(level_id)
        if not terms:
            return await update.message.reply_text("لا توجد أترام لهذا المستوى حتى الآن.", reply_markup=generate_levels_keyboard(levels))
        nav_push_view(context.user_data, "term_list")
        return await update.message.reply_text("اختر الترم:", reply_markup=generate_terms_keyboard(terms))

    # 5) اختيار ترم؟
    level_id, _ = nav_get_ids(context.user_data)
    if level_id:
        terms = await get_terms_by_level(level_id)
        terms_map = {name: _id for _id, name in terms}
        if text in terms_map:
            term_id = terms_map[text]
            nav_set_term(context.user_data, text, term_id)
            flags = await term_feature_flags(level_id, term_id)
            return await update.message.reply_text("اختر:", reply_markup=generate_term_menu_keyboard_dynamic(flags))

    # 6) قائمة خيارات الترم
    if text in (TERM_MENU_SHOW_SUBJECTS, TERM_MENU_PLAN, TERM_MENU_LINKS, TERM_MENU_ADV_SEARCH):
        level_id, term_id = nav_get_ids(context.user_data)
        if not (level_id and term_id):
            return await update.message.reply_text("ابدأ باختيار المستوى ثم الترم.", reply_markup=main_menu)

        if text == TERM_MENU_SHOW_SUBJECTS:
            nav_push_view(context.user_data, "subject_list")
            subjects = await get_subjects_by_level_and_term(level_id, term_id)
            if not subjects:
                flags = await term_feature_flags(level_id, term_id)
                return await update.message.reply_text("لا توجد مواد لهذا الترم.", reply_markup=generate_term_menu_keyboard_dynamic(flags))
            return await update.message.reply_text("اختر المادة:", reply_markup=generate_subjects_keyboard(subjects))

        if text == TERM_MENU_PLAN:
            flags = await term_feature_flags(level_id, term_id)
            return await update.message.reply_text("الخطة الدراسية (قريبًا).", reply_markup=generate_term_menu_keyboard_dynamic(flags))

        if text == TERM_MENU_LINKS:
            flags = await term_feature_flags(level_id, term_id)
            return await update.message.reply_text("روابط المجموعات والقنوات (قريبًا).", reply_markup=generate_term_menu_keyboard_dynamic(flags))

        if text == TERM_MENU_ADV_SEARCH:
            flags = await term_feature_flags(level_id, term_id)
            return await update.message.reply_text("البحث المتقدم (قريبًا).", reply_markup=generate_term_menu_keyboard_dynamic(flags))

    # 7) اختيار مادة؟
    level_id, term_id = nav_get_ids(context.user_data)
    if level_id and term_id:
        subjects = await get_subjects_by_level_and_term(level_id, term_id)
        subject_names = {name for (name,) in subjects}
        if text in subject_names:
            subject_id = await get_subject_id_by_name(level_id, term_id, text)
            if subject_id is None:
                flags = await term_feature_flags(level_id, term_id)
                return await update.message.reply_text("تعذر العثور على المادة.", reply_markup=generate_term_menu_keyboard_dynamic(flags))
            nav_set_subject(context.user_data, text, subject_id)
            sections = await get_available_sections_for_subject(subject_id)
            return await update.message.reply_text(
                f"المادة: {text}\nاختر القسم:" if sections else "لا توجد أقسام متاحة لهذه المادة حتى الآن.",
                reply_markup=generate_subject_sections_keyboard_dynamic(sections),
            )

    # 8) اختيار قسم المادة
    if text in LABEL_TO_SECTION:
        section_code = LABEL_TO_SECTION[text]
        nav_set_section(context.user_data, text, section_code)

        nav = context.user_data.get("nav", {})
        subject_id = nav.get("data", {}).get("subject_id")

        years = await get_years_for_subject_section(subject_id, section_code)
        lecturers = await get_lecturers_for_subject_section(subject_id, section_code)
        lectures_exist = await has_lecture_category(subject_id, section_code)

        return await update.message.reply_text(
            "اختر طريقة التصفية:",
            reply_markup=generate_section_filters_keyboard_dynamic(bool(years), bool(lecturers), lectures_exist),
        )

    # 8.1) تصفية حسب السنة/المحاضر/عرض كل المحاضرات
    if text in {FILTER_BY_YEAR, FILTER_BY_LECTURER, LIST_LECTURES}:
        nav = context.user_data.get("nav", {})
        subject_id = nav.get("data", {}).get("subject_id")
        section_code = nav.get("data", {}).get("section")
        if not (subject_id and section_code):
            return await update.message.reply_text("ابدأ باختيار المادة ثم القسم.", reply_markup=main_menu)

        if text == FILTER_BY_YEAR:
            years = await get_years_for_subject_section(subject_id, section_code)
            if not years:
                return await update.message.reply_text("لا توجد سنوات لهذا القسم.", reply_markup=generate_subject_sections_keyboard_dynamic([]))
            nav_push_view(context.user_data, "year_list")
            return await update.message.reply_text("اختر السنة:", reply_markup=generate_years_keyboard(years))

        if text == FILTER_BY_LECTURER:
            lecturers = await get_lecturers_for_subject_section(subject_id, section_code)
            if not lecturers:
                return await update.message.reply_text("لا يوجد محاضرون مرتبطون بهذا القسم.", reply_markup=generate_subject_sections_keyboard_dynamic([]))
            nav_push_view(context.user_data, "lecturer_list")
            return await update.message.reply_text("اختر المحاضر:", reply_markup=generate_lecturers_keyboard(lecturers))

        if text == LIST_LECTURES:
            titles = await list_lecture_titles(subject_id, section_code)
            if not titles:
                return await update.message.reply_text("لا توجد محاضرات متاحة.", reply_markup=generate_subject_sections_keyboard_dynamic([]))
            nav_push_view(context.user_data, "lecture_list")
            return await update.message.reply_text("اختر محاضرة:", reply_markup=generate_lecture_titles_keyboard(titles))

    # 8.2) اختيار سنة/محاضر
    nav = context.user_data.get("nav", {})
    subject_id = nav.get("data", {}).get("subject_id")
    section_code = nav.get("data", {}).get("section")
    lecturer_id = nav.get("data", {}).get("lecturer_id")

    if subject_id and section_code:
        if lecturer_id:
            years = await get_years_for_subject_section_lecturer(subject_id, section_code, lecturer_id)
            years_map = {name: _id for _id, name in years}
            if text in years_map:
                year_id = years_map[text]
                nav_set_year(context.user_data, text, year_id)
                titles = await list_lecture_titles_by_lecturer_year(subject_id, section_code, lecturer_id, year_id)
                lectures_exist = bool(titles)
                cats = await list_categories_for_subject_section_year(subject_id, section_code, year_id, lecturer_id=lecturer_id)
                nav_push_view(context.user_data, "year_category_menu")
                return await update.message.reply_text(
                    f"المحاضر: {next((lbl for t, lbl in nav.get('stack', []) if t=='lecturer'), '')}\nالسنة: {text}\nاختر نوع المحتوى:",
                    reply_markup=generate_year_category_menu_keyboard(cats, lectures_exist),
                )
        else:
            years = await get_years_for_subject_section(subject_id, section_code)
            years_map = {name: _id for _id, name in years}
            if text in years_map:
                year_id = years_map[text]
                nav_set_year(context.user_data, text, year_id)
                titles = await list_lecture_titles_by_year(subject_id, section_code, year_id)
                lectures_exist = bool(titles)
                cats = await list_categories_for_subject_section_year(subject_id, section_code, year_id)
                nav_push_view(context.user_data, "year_category_menu")
                return await update.message.reply_text(
                    f"السنة: {text}\nاختر نوع المحتوى:",
                    reply_markup=generate_year_category_menu_keyboard(cats, lectures_exist),
                )

        # اختيار محاضر بالاسم
        lecturers = await get_lecturers_for_subject_section(subject_id, section_code)
        lect_map = {name: _id for _id, name in lecturers}
        if text in lect_map:
            lecturer_id = lect_map[text]
            nav_set_lecturer(context.user_data, text, lecturer_id)
            years = await get_years_for_subject_section_lecturer(subject_id, section_code, lecturer_id)
            lectures_exist = await list_lecture_titles_by_lecturer(subject_id, section_code, lecturer_id)
            return await update.message.reply_text(
                f"المحاضر: {text}\nاختر خيارًا:",
                reply_markup=generate_lecturer_filter_keyboard(bool(years), bool(lectures_exist)),
            )

    # 8.2.1) داخل قائمة المحاضر: اختر السنة/عرض كل محاضرات هذا المحاضر
    if text in {CHOOSE_YEAR_FOR_LECTURER, LIST_LECTURES_FOR_LECTURER}:
        nav = context.user_data.get("nav", {})
        subject_id = nav.get("data", {}).get("subject_id")
        section_code = nav.get("data", {}).get("section")
        lecturer_id = nav.get("data", {}).get("lecturer_id")
        lecturer_label = next((lbl for t, lbl in nav.get("stack", []) if t == "lecturer"), "")

        if not (subject_id and section_code and lecturer_id):
            return await update.message.reply_text("ابدأ باختيار المادة → القسم → المحاضر.", reply_markup=main_menu)

        if text == CHOOSE_YEAR_FOR_LECTURER:
            years = await get_years_for_subject_section_lecturer(subject_id, section_code, lecturer_id)
            if not years:
                years_exist = False
                lectures_exist = await list_lecture_titles_by_lecturer(subject_id, section_code, lecturer_id)
                return await update.message.reply_text(
                    "لا توجد سنوات مرتبطة بمحاضرات هذا المحاضر.",
                    reply_markup=generate_lecturer_filter_keyboard(years_exist, bool(lectures_exist)),
                )
            nav_push_view(context.user_data, "year_list")
            return await update.message.reply_text(f"المحاضر: {lecturer_label}\nاختر السنة:", reply_markup=generate_years_keyboard(years))

        if text == LIST_LECTURES_FOR_LECTURER:
            titles = await list_lecture_titles_by_lecturer(subject_id, section_code, lecturer_id)
            if not titles:
                years = await get_years_for_subject_section_lecturer(subject_id, section_code, lecturer_id)
                return await update.message.reply_text(
                    "لا توجد محاضرات لهذا المحاضر.",
                    reply_markup=generate_lecturer_filter_keyboard(bool(years), False),
                )
            nav_push_view(context.user_data, "lecture_list")
            return await update.message.reply_text(f"المحاضر: {lecturer_label}\nاختر محاضرة:", reply_markup=generate_lecture_titles_keyboard(titles))


    # 8.2.x) داخل قائمة تصنيفات السنة (نفذ فقط إن كانت الشاشة الحالية هي year_category_menu)
    if text == YEAR_MENU_LECTURES or text in LABEL_TO_CATEGORY:
        nav = context.user_data.get("nav", {})
        stack = nav.get("stack", [])
        current = stack[-1][0] if stack else None

        if current == "year_category_menu":
            subject_id   = nav.get("data", {}).get("subject_id")
            section_code = nav.get("data", {}).get("section")
            year_id      = nav.get("data", {}).get("year_id")
            lecturer_id  = nav.get("data", {}).get("lecturer_id")

            # (أ) زر "📚 المحاضرات" من شاشة السنة
            if text == YEAR_MENU_LECTURES:
                if lecturer_id and year_id:
                    titles = await list_lecture_titles_by_lecturer_year(subject_id, section_code, lecturer_id, year_id)
                else:
                    titles = await list_lecture_titles_by_year(subject_id, section_code, year_id)

                if not titles:
                    cats = await list_categories_for_subject_section_year(subject_id, section_code, year_id, lecturer_id=lecturer_id)
                    return await update.message.reply_text("لا توجد محاضرات لهذه السنة.", reply_markup=generate_year_category_menu_keyboard(cats, False))

                nav_push_view(context.user_data, "lecture_list")
                return await update.message.reply_text("اختر محاضرة:", reply_markup=generate_lecture_titles_keyboard(titles))

            # (ب) اختيار تصنيف سنة (امتحانات/ملازم/ملخصات/…)
            if text in LABEL_TO_CATEGORY:
                category = LABEL_TO_CATEGORY[text]

                # 🔒 حماية إضافية: ملف المحاضرة لا يُعرض في شاشة السنة
                if category == "lecture":
                    # وجّه المستخدم لقائمة المحاضرات بدلًا من عرض كل "ملف المحاضرة" للسنة
                    if lecturer_id and year_id:
                        titles = await list_lecture_titles_by_lecturer_year(subject_id, section_code, lecturer_id, year_id)
                    else:
                        titles = await list_lecture_titles_by_year(subject_id, section_code, year_id)
                    nav_push_view(context.user_data, "lecture_list")
                    return await update.message.reply_text("اختر محاضرة أولًا:", reply_markup=generate_lecture_titles_keyboard(titles))

                mats = await get_materials_by_category(
                    subject_id, section_code, category,
                    year_id=year_id, lecturer_id=lecturer_id
                )
                if not mats:
                    titles_exist = False
                    if lecturer_id and year_id:
                        titles_exist = bool(await list_lecture_titles_by_lecturer_year(subject_id, section_code, lecturer_id, year_id))
                    else:
                        titles_exist = bool(await list_lecture_titles_by_year(subject_id, section_code, year_id))
                    cats = await list_categories_for_subject_section_year(subject_id, section_code, year_id, lecturer_id=lecturer_id)
                    return await update.message.reply_text("لا توجد ملفات لهذا التصنيف.", reply_markup=generate_year_category_menu_keyboard(cats, titles_exist))

                for _id, title, url in mats:
                    await update.message.reply_text(f"📄 {title}\n{url or '(لا يوجد رابط)'}")

                titles_exist = False
                if lecturer_id and year_id:
                    titles_exist = bool(await list_lecture_titles_by_lecturer_year(subject_id, section_code, lecturer_id, year_id))
                else:
                    titles_exist = bool(await list_lecture_titles_by_year(subject_id, section_code, year_id))
                cats = await list_categories_for_subject_section_year(subject_id, section_code, year_id, lecturer_id=lecturer_id)
                return await update.message.reply_text("اختر نوع محتوى آخر:", reply_markup=generate_year_category_menu_keyboard(cats, titles_exist))




    # 8.3) اختيار عنوان محاضرة → عرض تصنيفات المحاضرة
    if subject_id and section_code:
        year_id = nav.get("data", {}).get("year_id")
        lecturer_id = nav.get("data", {}).get("lecturer_id")

        candidate_titles = set(await list_lecture_titles(subject_id, section_code))
        if year_id:
            candidate_titles.update(await list_lecture_titles_by_year(subject_id, section_code, year_id))
        if lecturer_id:
            candidate_titles.update(await list_lecture_titles_by_lecturer(subject_id, section_code, lecturer_id))
        if year_id and lecturer_id:
            candidate_titles.update(await list_lecture_titles_by_lecturer_year(subject_id, section_code, lecturer_id, year_id))

        if text in candidate_titles:
            # ✅ ثبّت اختيار المحاضرة في الـ stack والـ data
            nav_set_lecture(context.user_data, text)
            # افتح شاشة تصنيفات المحاضرة
            nav_push_view(context.user_data, "lecture_category_menu")

            cats = await list_categories_for_lecture(subject_id, section_code, text, year_id=year_id, lecturer_id=lecturer_id)
            if not cats:
                mats = await get_lecture_materials(subject_id, section_code, year_id=year_id, lecturer_id=lecturer_id, title=text)
                if mats:
                    for _id, title, url in mats:
                        await update.message.reply_text(f"📄 {title}\n{url or '(لا يوجد رابط)'}")
                    # ارجع لقائمة العناوين المناسبة للسياق
                    titles = await list_lecture_titles(subject_id, section_code)
                    if year_id and lecturer_id:
                        titles = await list_lecture_titles_by_lecturer_year(subject_id, section_code, lecturer_id, year_id)
                    elif year_id:
                        titles = await list_lecture_titles_by_year(subject_id, section_code, year_id)
                    elif lecturer_id:
                        titles = await list_lecture_titles_by_lecturer(subject_id, section_code, lecturer_id)
                    # أزل طبقة تصنيفات المحاضرة لأننا أرسلنا الملفات مباشرة
                    nav_back_one(context.user_data)
                    return await update.message.reply_text("اختر محاضرة أخرى:", reply_markup=generate_lecture_titles_keyboard(titles))

                # لا توجد أي مرفقات
                nav_back_one(context.user_data)  # أزل شاشة التصنيفات
                titles = await list_lecture_titles(subject_id, section_code)
                if year_id and lecturer_id:
                    titles = await list_lecture_titles_by_lecturer_year(subject_id, section_code, lecturer_id, year_id)
                elif year_id:
                    titles = await list_lecture_titles_by_year(subject_id, section_code, year_id)
                elif lecturer_id:
                    titles = await list_lecture_titles_by_lecturer(subject_id, section_code, lecturer_id)
                return await update.message.reply_text("لا توجد أنواع ملفات لهذه المحاضرة.", reply_markup=generate_lecture_titles_keyboard(titles))

            # يوجد تصنيفات للمحاضرة
            return await update.message.reply_text(
                f"المحاضرة: {text}\nاختر نوع الملف:",
                reply_markup=generate_lecture_category_menu_keyboard(cats)
            )


  
    # 8.4) اختيار تصنيف داخل "قائمة تصنيفات المحاضرة"
    if text in LABEL_TO_CATEGORY:
        nav = context.user_data.get("nav", {})
        stack = nav.get("stack", [])
        current = stack[-1][0] if stack else None

        if current == "lecture_category_menu":
            subject_id    = nav.get("data", {}).get("subject_id")
            section_code  = nav.get("data", {}).get("section")
            year_id       = nav.get("data", {}).get("year_id")
            lecturer_id   = nav.get("data", {}).get("lecturer_id")
            lecture_title = nav.get("data", {}).get("lecture_title")
            category      = LABEL_TO_CATEGORY[text]

            # لو حصل خلل وفُقد العنوان، لا تعرض كل شيء — وجّه المستخدم لاختيار عنوان
            if not lecture_title:
                titles = await list_lecture_titles(subject_id, section_code)
                return await update.message.reply_text("اختر محاضرة أولًا:", reply_markup=generate_lecture_titles_keyboard(titles))

            mats = await get_materials_by_category(
                subject_id, section_code, category,
                year_id=year_id, lecturer_id=lecturer_id, title=lecture_title  # ✅ يقيّد بالعنوان
            )
            if not mats:
                cats = await list_categories_for_lecture(subject_id, section_code, lecture_title, year_id=year_id, lecturer_id=lecturer_id)
                return await update.message.reply_text("لا توجد ملفات لهذا النوع.", reply_markup=generate_lecture_category_menu_keyboard(cats))

            for _id, title, url in mats:
                await update.message.reply_text(f"📄 {title}\n{url or '(لا يوجد رابط)'}")

            cats = await list_categories_for_lecture(subject_id, section_code, lecture_title, year_id=year_id, lecturer_id=lecturer_id)
            return await update.message.reply_text("اختر نوعًا آخر:", reply_markup=generate_lecture_category_menu_keyboard(cats))


    if text.startswith("/"):
        return await update.message.reply_text("هذا أمر خاص. لم يتم تفعيله بعد.")

    return await update.message.reply_text("الخيار غير معروف. ابدأ بـ: 📚 المستويات")









# --------------------------------------------------------------------------
def main():
    # سياسة loop مناسبة لويندوز
    if os.name == "nt":
        try:
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        except Exception:
            pass

    # تأكد من وجود event loop للـ MainThread (مهم لبايثون 3.12)
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    # تهيئة قاعدة البيانات
    loop.run_until_complete(init_db())

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo_handler))
   
    print("✅ Bot is running...")
    app.run_polling()























if __name__ == "__main__":
    try:
        main()
        
    except KeyboardInterrupt:
        print("\nBot stopped by user")




