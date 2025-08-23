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
    sections_mode TEXT NOT NULL DEFAULT 'theory_only' CHECK(
        sections_mode IN (
            'theory_only',
            'theory_discussion',
            'theory_discussion_lab'
        )
    ),
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

-- مستخدمون بامتيازات إدارية
CREATE TABLE IF NOT EXISTS admins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tg_user_id INTEGER NOT NULL UNIQUE,
    username TEXT,
    role TEXT NOT NULL DEFAULT 'ADMIN',
    permissions_mask INTEGER NOT NULL DEFAULT 0
);

-- مجموعات تيليجرام التي يتم الأرشفة منها
CREATE TABLE IF NOT EXISTS groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tg_chat_id INTEGER NOT NULL UNIQUE,
    title TEXT
);

CREATE TABLE IF NOT EXISTS topics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id INTEGER NOT NULL,
    tg_topic_id INTEGER NOT NULL,
    title TEXT,
    FOREIGN KEY (group_id) REFERENCES groups(id)
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
    tg_storage_chat_id INTEGER,
    tg_storage_msg_id INTEGER,
    source_chat_id INTEGER,
    source_topic_id INTEGER,
    source_message_id INTEGER,
    created_by_admin_id INTEGER,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (subject_id) REFERENCES subjects(id),
    FOREIGN KEY (year_id) REFERENCES years(id),
    FOREIGN KEY (lecturer_id) REFERENCES lecturers(id),
    FOREIGN KEY (created_by_admin_id) REFERENCES admins(id)
);

-- عمليات الاستيراد أو المعالجة الخلفية
CREATE TABLE IF NOT EXISTS ingestions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    material_id INTEGER,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (material_id) REFERENCES materials(id)
);

-- فهارس لتحسين الاستعلامات
CREATE INDEX IF NOT EXISTS idx_materials_core
    ON materials(subject_id, section, year_id, category);
CREATE INDEX IF NOT EXISTS idx_materials_storage
    ON materials(tg_storage_chat_id, tg_storage_msg_id);
CREATE INDEX IF NOT EXISTS idx_topics_chat
    ON topics(group_id, tg_topic_id);
CREATE INDEX IF NOT EXISTS idx_ingestions_status
    ON ingestions(status, created_at);

