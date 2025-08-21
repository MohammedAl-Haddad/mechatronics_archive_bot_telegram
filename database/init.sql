-- إسم الملف: database/init.sql
-- وصف: إنشاء الجداول الأساسية لقاعدة البيانات
-- قاعدة البيانات 
-- =========================
-- هذا الملف يحتوي على إنشاء الجداول الأساسية لقاعدة البيانات
-- ويشمل مستويات التعليم، الاترام، والمقررات الدراسية.
-- تأكد من تشغيل هذا الملف مرة واحدة فقط لإنشاء الجداول
-- وتجنب تكرار إنشاء الجداول.
-- =========================
CREATE TABLE IF NOT EXISTS levels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS terms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

-- إنشاء جدول المقررات الدراسية
-- يحتوي على معرف فريد، رمز المقرر، اسم المقرر، معرف المستوى ومعرف الترم
-- يربط المقرر بالمستوى والترم المناسبين        

CREATE TABLE IF NOT EXISTS subjects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL,
    name TEXT NOT NULL,
    level_id INTEGER NOT NULL,
    term_id INTEGER NOT NULL,
    FOREIGN KEY (level_id) REFERENCES levels(id),
    FOREIGN KEY (term_id) REFERENCES terms(id)
);

-- سنوات (هجري/ميلادي أو صيغة مثل 2024-2025)
CREATE TABLE IF NOT EXISTS years (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

-- محاضرون/مناقشون/مدرسو عملي
CREATE TABLE IF NOT EXISTS lecturers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    role TEXT CHECK(role IN ('lecturer','ta','lab')) DEFAULT 'lecturer'
);

-- مواد تعليمية مرتبطة بالمادة + القسم + تصنيف المحتوى
CREATE TABLE IF NOT EXISTS materials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_id INTEGER NOT NULL,
    section TEXT NOT NULL CHECK(section IN ('theory','discussion','lab','syllabus','apps')),
    -- category TEXT NOT NULL CHECK(category IN ('lecture','exam','booklet','board_images','video','simulation','summary','notes','external_link')),
    category TEXT NOT NULL CHECK(category IN (
    'lecture','slides','audio','exam','booklet','board_images','video','simulation',
    'summary','notes','external_link','mind_map','transcript','related'
    )),

    title TEXT NOT NULL,
    url TEXT,                 -- رابط تيليجرام/جوجل درايف/يوتيوب ... الخ
    year_id INTEGER,          -- اختياري
    lecturer_id INTEGER,      -- اختياري
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (subject_id) REFERENCES subjects(id),
    FOREIGN KEY (year_id) REFERENCES years(id),
    FOREIGN KEY (lecturer_id) REFERENCES lecturers(id)
);

