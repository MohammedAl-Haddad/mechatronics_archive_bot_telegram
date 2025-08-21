
# enterst.py ملف لإدخال ملفات تجريبية للبوت 
import asyncio
import aiosqlite
from bot.db import (
    DB_PATH,
    insert_level, insert_term, insert_subject,
    get_level_id_by_name, get_term_id_by_name, get_subject_id_by_name,
    ensure_year_id, ensure_lecturer_id, insert_material
)

# ---------------- أدوات مساعدة بسيطة ----------------

ALLOWED_TABLES = {"levels", "terms"}

async def _get_id_by_name(table: str, name: str) -> int | None:
    if table not in ALLOWED_TABLES:
        raise ValueError("Invalid table name")
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(f"SELECT id FROM {table} WHERE name = ?", (name,))
        row = await cur.fetchone()
        return row[0] if row else None

async def ensure_level_id(name: str) -> int:
    _id = await _get_id_by_name("levels", name)
    if _id is not None:
        return _id
    await insert_level(name)
    _id = await _get_id_by_name("levels", name)
    if _id is None:
        raise RuntimeError(f"Failed to create level: {name}")
    return _id

async def ensure_term_id(name: str) -> int:
    _id = await _get_id_by_name("terms", name)
    if _id is not None:
        return _id
    await insert_term(name)
    _id = await _get_id_by_name("terms", name)
    if _id is None:
        raise RuntimeError(f"Failed to create term: {name}")
    return _id

async def add_subjects(level_name: str, term_name: str, pairs: list[tuple[str, str]]):
    """
    إضافة مواد لمستوى/ترم.
    pairs: [(code, name), ...]
    - نتجاوز أي كود قيمته '---' لتجنب إدخال مواد placeholders.
    """
    level_id = await ensure_level_id(level_name)
    term_id  = await ensure_term_id(term_name)
    for code, name in pairs:
        if code.strip() == "---":
            continue
        await insert_subject(code, name, level_id, term_id)

async def _subject_id(level_name: str, term_name: str, subject_name: str) -> int:
    level_id = await get_level_id_by_name(level_name)
    term_id  = await get_term_id_by_name(term_name)
    if not (level_id and term_id):
        raise RuntimeError(f"Level/Term not found: {level_name} / {term_name}")
    sid = await get_subject_id_by_name(level_id, term_id, subject_name)
    if not sid:
        raise RuntimeError(f"Subject not found: {subject_name} ({level_name}/{term_name})")
    return sid

def _t(n: int, title: str) -> str:
    """عنوان موحّد لعناصر المحاضرة ومرفقاتها."""
    return f"محاضرة {n}: {title}"

# ---------------- تهيئة الهيكل (المستويات/الأترام/المواد) ----------------

async def seed_structure():
    # مستويات + أترام
    L1 = "المستوى الأول";   L2 = "المستوى الثاني";  L3 = "المستوى الثالث"
    L4 = "المستوى الرابع";  L5 = "المستوى الخامس"
    T1 = "الترم الأول";     T2 = "الترم الثاني"

    # المستوى الأول
    await add_subjects(L1, T1, [
        ("B0303101", "لغة عربية (1)"),
        ("B0303103", "لغة إنجليزية (1)"),
        ("B0303111", "رياضيات (1)"),
        ("B0303121", "فيزياء هندسية"),
        ("B0303141", "دوائر كهربائية (1)"),
        ("B0303105", "ثقافة إسلامية"),
        ("B0303122", "ورش هندسية"),
        ("B0303107", "ثقافة وطنية (1)"),
    ])
    await add_subjects(L1, T2, [
        ("B0303102", "لغة عربية (2)"),
        ("B0303104", "لغة إنجليزية (2)"),
        ("B0303112", "رياضيات (2)"),
        ("B0303123", "كيمياء هندسية"),
        ("B0303142", "دوائر كهربائية (2)"),
        ("B0303106", "أساسيات حاسوب"),
        ("B0303124", "رسم هندسي"),
        ("B0303108", "ثقافة وطنية (2)"),
    ])

    # المستوى الثاني
    await add_subjects(L2, T1, [
        ("B0303213", "جبر خطي ومعادلات تفاضلية"),
        ("B0303251", "مشاكل وحلول"),
        ("B0303243", "آلات كهربائية (1)"),
        ("B0303231", "ستاتيكا"),
        ("B0303261", "مقدمة في الميكاترونيكس"),
        ("B0303271", "الكترونيات تماثلية"),
        ("B0303225", "مهارات التواصل"),
    ])
    await add_subjects(L2, T2, [
        ("B0303214", "الاحتمالات والإحصاء"),
        ("B0303252", "البرمجة الشيئية (بالكائنات)"),
        ("B0303244", "آلات كهربائية (2)"),
        ("B0303232", "ديناميكا"),
        ("B0303262", "الأجهزة والقياسات الهندسية"),
        ("B0303272", "تصميم منطقي"),
        ("B0303233", "مقاومة مواد"),
    ])

    # المستوى الثالث
    await add_subjects(L3, T1, [
        ("B0303353", "البرمجة للمهندسين"),
        ("B0303334", "الديناميكا الحرارية وانتقال حرارة"),
        ("B0303315", "تحليل عددي"),
        ("B0303374", "إشارات ونظم"),
        ("B0303373", "الكترونيك رقمي"),
        ("B0303381", "تحكم آلي (1)"),
        ("B0303326", "أخلاقيات المهنة"),
    ])
    await add_subjects(L3, T2, [
        ("B0303375", "تصميم نظم رقمية"),
        ("B0303335", "ميكانيكا الموائع"),
        ("B0303376", "معالجة إشارة رقمية"),
        ("B0303336", "طرق تصنيع"),
        ("B0303382", "تحكم آلي (2)"),
        ("B0303337", "نظرية آلات"),
    ])

    # المستوى الرابع
    await add_subjects(L4, T1, [
        ("B0303445", "الكترونيات القوى والمحركات"),
        ("B0303491", "التصميم والتصنيع بالكمبيوتر"),
        ("B0303463", "تصميم أنظمة الميكاترونيكس (1)"),
        ("B0303438", "تصميم عناصر الآلة"),
        ("B0303464", "أنظمة الروبوتات"),
        ("B0303427", "مبادئ البحث العلمي"),
    ])
    await add_subjects(L4, T2, [
        ("B0303483", "أنظمة مدمجة"),
        ("B0303478", "الاتصال والحصول على البيانات"),
        ("B0303484", "التحكم المنطقي المبرمج (PLC)"),
        ("B0303565", "تصميم أنظمة الميكاترونيكس (2)"),
        ("B0303439", "الأنظمة الهيدروليكية والهوائية"),
        ("---",      "مقرر اختياري (1)"),
    ])

    # المستوى الخامس
    await add_subjects(L5, T1, [
        ("B0303579", "شبكات صناعية"),
        ("B0303592", "سلامة صناعية"),
        ("---",      "مقرر اختياري (2)"),
        ("B0303528", "مشروع التخرج (1)"),
    ])
    await add_subjects(L5, T2, [
        ("B0303554", "الأنظمة الخبيرة"),
        ("B0303593", "إدارة المشروع الهندسي"),
        ("---",      "مقرر اختياري (3)"),
        ("B0303529", "مشروع التخرج (2)"),
    ])

    print("✅ تم إدخال الهيكل (مستويات/أترام/مواد).")

# ---------------- بيانات السنوات/المحاضرين ----------------

async def seed_years_and_lecturers():
    # سنوات (أسماء فقط – حرّة)
    y_1445 = await ensure_year_id("1445")
    y_1446 = await ensure_year_id("1446")
    y_1447 = await ensure_year_id("1447")
    y_1448 = await ensure_year_id("1448")
    y_2324 = await ensure_year_id("2023/2024")  # مثال سنة غير رقمية

    # محاضرون/معيدون
    lec_abdu   = await ensure_lecturer_id("د. عبده محمد", "lecturer")
    lec_hassan = await ensure_lecturer_id("د. حسن المتوكل", "lecturer")
    lec_hayfi  = await ensure_lecturer_id("أ.د. محمد الحيفي", "lecturer")
    lec_mustafa= await ensure_lecturer_id("د. مصطفى العريقي", "lecturer")
    lec_ashraf = await ensure_lecturer_id("م. أشرف الشبيبي", "lecturer")
    ta_arwa    = await ensure_lecturer_id("أ. أروى الهندي", "ta")
    ta_waleed  = await ensure_lecturer_id("م. وليد غالب", "ta")
    eng_salma  = await ensure_lecturer_id("م. سلمى الحرازي", "lecturer")

    return {
        "years":   dict(y_1445=y_1445, y_1446=y_1446, y_1447=y_1447, y_1448=y_1448, y_2324=y_2324),
        "people":  dict(lec_abdu=lec_abdu, lec_hassan=lec_hassan, lec_hayfi=lec_hayfi,
                        lec_mustafa=lec_mustafa, lec_ashraf=lec_ashraf,
                        ta_arwa=ta_arwa, ta_waleed=ta_waleed, eng_salma=eng_salma)
    }

# ---------------- مواد كل مادة/قسم بحالات متنوعة ----------------

async def seed_materials_variants(ctx):
    Y = ctx["years"]; P = ctx["people"]

    # المستوى الأول / الترم الأول --------------------------------------------
    L1 = "المستوى الأول"; T1 = "الترم الأول"

    # دوائر كهربائية (1): قسم نظري متكامل + سنة عامة + اختلافات في المرفقات
    sid = await _subject_id(L1, T1, "دوائر كهربائية (1)")
    lectures_1446 = [
        (1, "أساسيات التيار والجهد"),
        (2, "قانونا كيرشوف"),
        (3, "المكافئات ونظرية ثيفينن"),
        (4, "الممانعات والتيار المتناوب"),
    ]
    for n, title in lectures_1446:
        T = _t(n, title)
        await insert_material(sid, "theory", "lecture", T, f"https://example.com/circuits1/lec{n}.pdf", Y["y_1446"], P["lec_abdu"])
        await insert_material(sid, "theory", "slides",  T, f"https://example.com/circuits1/lec{n}_slides.pdf", Y["y_1446"], P["lec_abdu"])
        # تنويع المرفقات
        if n in (1, 3):
            await insert_material(sid, "theory", "audio", T, f"https://example.com/circuits1/lec{n}_audio.mp3", Y["y_1446"], P["lec_abdu"])
        if n == 2:
            await insert_material(sid, "theory", "board_images", T, f"https://example.com/circuits1/lec{n}_board.zip", Y["y_1446"], P["lec_abdu"])
        if n == 4:
            await insert_material(sid, "theory", "video", T, f"https://example.com/circuits1/lec{n}_video.mp4", Y["y_1446"], P["lec_abdu"])
        # روابط مرتبطة بالمحاضرة
        await insert_material(sid, "theory", "related", T, "https://example.com/circuits1/refs", Y["y_1446"], P["lec_abdu"])
    # مواد سنة عامة (بدون محاضر)
    await insert_material(sid, "theory", "booklet", "ملزمة المقرر 1446", "https://example.com/circuits1/booklet_1446.pdf", Y["y_1446"], None)
    await insert_material(sid, "theory", "exam",    "نماذج امتحانات 1446", None, Y["y_1446"], None)
    await insert_material(sid, "theory", "notes",   "تكاليف وتمارين 1446", "https://example.com/circuits1/hw_1446.pdf", Y["y_1446"], None)
    await insert_material(sid, "theory", "summary", "ملخصات الطلاب 1446",  "https://example.com/circuits1/summary_1446.pdf", Y["y_1446"], None)
    # سيلابس وروابط عامة لتفعيل أعلام الترم
    await insert_material(sid, "syllabus", "external_link", "وصف المقرر (سلسلة فيديو)", "https://example.com/circuits1/syllabus_playlist", Y["y_1446"], None)

    # discussion: مواد سنة عامة فقط + TA مختلف عن نظري
    await insert_material(sid, "discussion", "notes",        "مناقشة: مسائل 1 (1446)", None, Y["y_1446"], P["ta_arwa"])
    await insert_material(sid, "discussion", "board_images", "صور السبورة (مناقشة) 1446", "https://example.com/circuits1/disc_board_1446.zip", Y["y_1446"], P["ta_arwa"])

    # lab: محاكاة + فيديو
    await insert_material(sid, "lab", "simulation", "محاكاة: قانون أوم (1446)", "https://example.com/sim/ohm", Y["y_1446"], None)
    await insert_material(sid, "lab", "video",      "تجربة: قياس مقاومة (1446)", "https://example.com/video/lab1", Y["y_1446"], None)

    # رياضيات (1): سنة مختلفة + محاضرات قليلة ومرفقات بسيطة
    sid = await _subject_id(L1, T1, "رياضيات (1)")
    for n, title in [(1, "النهايات"), (2, "الاشتقاق"), (3, "التكامل")]:
        T = _t(n, title)
        await insert_material(sid, "theory", "lecture", T, f"https://example.com/math1/lec{n}.pdf", Y["y_1445"], None)
        await insert_material(sid, "theory", "slides",  T, f"https://example.com/math1/lec{n}_slides.pdf", Y["y_1445"], None)
    await insert_material(sid, "theory", "booklet", "ملزمة 1445", "https://example.com/math1/booklet_1445.pdf", Y["y_1445"], None)
    await insert_material(sid, "theory", "notes",   "تمارين 1445", "https://example.com/math1/exercises_1445.pdf", Y["y_1445"], None)

    # فيزياء هندسية: محاضرة واحدة + ملزمة سنة أخرى (لاختبار اختلاف السنوات داخل نفس المادة)
    sid = await _subject_id(L1, T1, "فيزياء هندسية")
    T = _t(1, "الوحدات والأبعاد")
    await insert_material(sid, "theory", "lecture", T, "https://example.com/engphys/lec1.pdf", Y["y_1447"], None)
    await insert_material(sid, "theory", "booklet", "ملزمة 2023/2024", "https://example.com/engphys/booklet_2324.pdf", Y["y_2324"], None)

    # لغة إنجليزية (1): مادة بلا محاضرات – فقط سيلابس وروابط/تطبيقات (لا يظهر زر "المحاضرات" في هذا القسم)
    sid = await _subject_id(L1, T1, "لغة إنجليزية (1)")
    await insert_material(sid, "syllabus", "external_link", "مرجع قواعد", "https://example.com/eng1/grammar_ref", Y["y_1446"], None)
    await insert_material(sid, "apps",     "external_link", "قاموس تقني", "https://example.com/eng1/dictionary", Y["y_1446"], None)

    # المستوى الأول / الترم الثاني ------------------------------------------
    L1 = "المستوى الأول"; T2 = "الترم الثاني"

    # دوائر كهربائية (2): محاضرتان + مرفقات مختلفة + امتحانات سنة عامة
    sid = await _subject_id(L1, T2, "دوائر كهربائية (2)")
    for n, title in [(1, "الاستجابة الزمنية"), (2, "دوائر الرنين")]:
        T = _t(n, title)
        await insert_material(sid, "theory", "lecture", T, f"https://example.com/circuits2/lec{n}.pdf", Y["y_1446"], P["lec_hassan"])
        if n == 2:
            await insert_material(sid, "theory", "video",        T, "https://example.com/circuits2/lec2_video.mp4", Y["y_1446"], P["lec_hassan"])
            await insert_material(sid, "theory", "board_images", T, "https://example.com/circuits2/lec2_board.zip", Y["y_1446"], P["lec_hassan"])
    await insert_material(sid, "theory", "exam", "نماذج امتحانات 1446", None, Y["y_1446"], None)

    # كيمياء هندسية: لا محاضرات، فقط مختبر وفيديو سنة عامة (لا يُظهر محاضرات)
    sid = await _subject_id(L1, T2, "كيمياء هندسية")
    await insert_material(sid, "lab", "video", "مختبر: معايرة حمض-قاعدة (1446)", "https://example.com/chem/lab_titrate.mp4", Y["y_1446"], None)

    # المستوى الثاني / الترم الأول ------------------------------------------
    L2 = "المستوى الثاني"; T1 = "الترم الأول"

    # مقدمة في الميكاترونيكس: محاضرة + أدوات Apps + ملزمة
    sid = await _subject_id(L2, T1, "مقدمة في الميكاترونيكس")
    T = _t(1, "تعريف الميكاترونيكس")
    await insert_material(sid, "theory", "lecture", T, "https://example.com/mecha/intro.pdf", Y["y_1445"], P["eng_salma"])
    await insert_material(sid, "apps",   "external_link", "أدوات Arduino", "https://example.com/arduino/tools", Y["y_1445"], None)
    await insert_material(sid, "theory", "booklet", "ملزمة 1445", "https://example.com/mecha/booklet_1445.pdf", Y["y_1445"], None)

    # آلات كهربائية (1): مختبر فقط (لا محاضرات) + محقق بالتاريخ الحديث 1448
    sid = await _subject_id(L2, T1, "آلات كهربائية (1)")
    await insert_material(sid, "lab", "simulation", "محاكاة: منحنى المغنطة (1448)", "https://example.com/machines1/sim_bh", Y["y_1448"], None)

    # المستوى الثاني / الترم الثاني -----------------------------------------
    L2 = "المستوى الثاني"; T2 = "الترم الثاني"

    # تصميم منطقي: محاضرات + سلايدات + مختبر + مناقشة + مواد سنة عامة
    sid = await _subject_id(L2, T2, "تصميم منطقي")
    for n, title in [(1, "البوابات المنطقية"), (2, "خرائط كارنوه")]:
        T = _t(n, title)
        await insert_material(sid, "theory", "lecture", T, f"https://example.com/logic/lec{n}.pdf", Y["y_1446"], P["lec_hayfi"])
        await insert_material(sid, "theory", "slides",  T, f"https://example.com/logic/lec{n}_slides.pdf", Y["y_1446"], P["lec_hayfi"])
    await insert_material(sid, "lab",        "simulation", "محاكاة: عداد ثنائي (1446)", "https://example.com/logic/sim_counter", Y["y_1446"], None)
    await insert_material(sid, "discussion", "notes",      "مناقشة 1: تبسيط الدوال (1446)", None, Y["y_1446"], P["ta_waleed"])
    await insert_material(sid, "theory", "booklet", "ملزمة 1446", "https://example.com/logic/booklet_1446.pdf", Y["y_1446"], None)
    await insert_material(sid, "theory", "exam",    "نماذج امتحانات 1446", None, Y["y_1446"], None)

    # آلات كهربائية (2): محاضرة واحدة + امتحانات سنة عامة
    sid = await _subject_id(L2, T2, "آلات كهربائية (2)")
    T = _t(1, "محولات القدرة")
    await insert_material(sid, "theory", "lecture", T, "https://example.com/machines2/lec1.pdf", Y["y_1446"], P["lec_hayfi"])
    await insert_material(sid, "theory", "exam",    "نماذج امتحانات 1446", None, Y["y_1446"], None)

    # المستوى الثالث / الترم الأول ------------------------------------------
    L3 = "المستوى الثالث"; T1 = "الترم الأول"

    # تحكم آلي (1): سنتان مختلفتان + مرفقات متنوعة
    sid = await _subject_id(L3, T1, "تحكم آلي (1)")
    T1c = _t(1, "مقدمة في التحكم")
    await insert_material(sid, "theory", "lecture", T1c, "https://example.com/control1/lec1.pdf", Y["y_1445"], P["lec_abdu"])
    await insert_material(sid, "theory", "slides",  T1c, "https://example.com/control1/lec1_slides.pdf", Y["y_1445"], P["lec_abdu"])
    await insert_material(sid, "theory", "audio",   T1c, "https://example.com/control1/lec1_audio.mp3",  Y["y_1445"], P["lec_abdu"])

    T2c = _t(2, "أنظمة الزمن المتصل والمنفصل")
    await insert_material(sid, "theory", "lecture", T2c, "https://example.com/control1/lec2.pdf", Y["y_1446"], P["lec_abdu"])
    await insert_material(sid, "theory", "video",   T2c, "https://example.com/control1/lec2_video.mp4", Y["y_1446"], P["lec_abdu"])

    await insert_material(sid, "discussion", "notes",        "مناقشة 1: تحويل لابلاس (1445)", None, Y["y_1445"], P["ta_arwa"])
    await insert_material(sid, "discussion", "board_images", "صور السبورة (مناقشة) 1445", "https://example.com/control1/disc1_board.zip", Y["y_1445"], P["ta_arwa"])

    await insert_material(sid, "theory", "mind_map",     "خريطة ذهنية (1446)", "https://example.com/control1/mindmap_1446.png", Y["y_1446"], None)
    await insert_material(sid, "theory", "summary",      "ملخص موجز 1446", "https://example.com/control1/summary_1446.pdf", Y["y_1446"], None)
    await insert_material(sid, "theory", "external_link","كورسات تحكم", "https://example.com/courses/control", Y["y_1446"], None)

    # الديناميكا الحرارية وانتقال حرارة: ملف محاضرة مع سلايدات ولكن (مثال رابط مفقود لعنصر ليظهر '(لا يوجد رابط)')
    sid = await _subject_id(L3, T1, "الديناميكا الحرارية وانتقال حرارة")
    T = _t(1, "قوانين الديناميكا الحرارية")
    await insert_material(sid, "theory", "lecture", T, None, Y["y_1445"], None)  # رابط مفقود عمداً
    await insert_material(sid, "theory", "slides",  T, "https://example.com/thermo/lec1_slides.pdf", Y["y_1445"], None)

    # المستوى الثالث / الترم الثاني -----------------------------------------
    L3 = "المستوى الثالث"; T2 = "الترم الثاني"

    # تحكم آلي (2): محاضرتان + روابط ذات صلة
    sid = await _subject_id(L3, T2, "تحكم آلي (2)")
    for n, title in [(1, "مقدمة التحكم الرقمي"), (2, "تحكم PID")]:
        T = _t(n, title)
        await insert_material(sid, "theory", "lecture", T, f"https://example.com/control2/lec{n}.pdf", Y["y_1446"], P["lec_mustafa"])
        if n == 2:
            await insert_material(sid, "theory", "related", T, "https://example.com/control2/pid_links", Y["y_1446"], P["lec_mustafa"])

    # ميكانيكا الموائع: مادة سنة عامة فقط (امتحان/ملزمة) لا توجد محاضرات
    sid = await _subject_id(L3, T2, "ميكانيكا الموائع")
    await insert_material(sid, "theory", "exam",    "نماذج 1446", None, Y["y_1446"], None)
    await insert_material(sid, "theory", "booklet", "دليل المختبر 1446", "https://example.com/fluids/handbook.pdf", Y["y_1446"], None)

    # المستوى الرابع / الترم الأول ------------------------------------------
    L4 = "المستوى الرابع"; T1 = "الترم الأول"

    # أنظمة الروبوتات: مختبر فيديو + محاضرة واحدة + سلايدات
    sid = await _subject_id(L4, T1, "أنظمة الروبوتات")
    await insert_material(sid, "lab", "video", "مختبر: حركة الذراع الروبوتي (1447)", "https://example.com/robot/lab_arm.mp4", Y["y_1447"], None)
    T = _t(1, "مقدمة الروبوتات")
    await insert_material(sid, "theory", "lecture", T, "https://example.com/robot/intro.pdf", Y["y_1447"], P["lec_ashraf"])
    await insert_material(sid, "theory", "slides",  T, "https://example.com/robot/intro_slides.pdf", Y["y_1447"], P["lec_ashraf"])

    # المستوى الرابع / الترم الثاني -----------------------------------------
    L4 = "المستوى الرابع"; T2 = "الترم الثاني"

    # PLC: محاضرة + رابط خارجي داخل نفس المحاضرة + سيلابس عام
    sid = await _subject_id(L4, T2, "التحكم المنطقي المبرمج (PLC)")
    T = _t(1, "مقدمة PLC")
    await insert_material(sid, "theory",   "lecture",       T, "https://example.com/plc/intro.pdf", Y["y_1446"], P["lec_ashraf"])
    await insert_material(sid, "theory",   "external_link", T, "https://example.com/plc/playlist",  Y["y_1446"], P["lec_ashraf"])
    await insert_material(sid, "syllabus", "external_link", "وصف مقرر PLC", "https://example.com/plc/syllabus", Y["y_1446"], None)

    # الأنظمة الهيدروليكية والهوائية: مادة سنة عامة بلا محاضر
    sid2 = await _subject_id(L4, T2, "الأنظمة الهيدروليكية والهوائية")
    await insert_material(sid2, "theory", "booklet", "مرجع شامل 1446", "https://example.com/hyd_pneu/handbook_1446.pdf", Y["y_1446"], None)

    # المستوى الخامس / الترم الأول ------------------------------------------
    L5 = "المستوى الخامس"; T1 = "الترم الأول"

    # شبكات صناعية: محاضرة بدون مرفقات إضافية (اختبار أبسط حالة)
    sid = await _subject_id(L5, T1, "شبكات صناعية")
    T = _t(1, "مقدمة الشبكات الصناعية")
    await insert_material(sid, "theory", "lecture", T, "https://example.com/indnet/lec1.pdf", Y["y_2324"], P["eng_salma"])

    # سلامة صناعية: لا محاضرات – فقط ملخص
    sid = await _subject_id(L5, T1, "سلامة صناعية")
    await insert_material(sid, "theory", "summary", "ملخص السلامة 2023/2024", "https://example.com/safety/summary.pdf", Y["y_2324"], None)

    print("✅ تم إدخال مواد تجريبية متنوعة مع حالات مفارِقة.")

# ---------------- نقطة البداية ----------------

async def main():
    await seed_structure()
    ctx = await seed_years_and_lecturers()
    await seed_materials_variants(ctx)
    print("🎉 اكتمل إدخال البيانات (شغّله مرة واحدة فقط).")

if __name__ == "__main__":
    asyncio.run(main())
