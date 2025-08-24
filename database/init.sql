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
    sections_mode TEXT CHECK(sections_mode IN (
        'theory_only','theory_discussion','theory_discussion_lab'
    )) DEFAULT 'theory_discussion_lab',
    FOREIGN KEY (level_id) REFERENCES levels(id),
    FOREIGN KEY (term_id) REFERENCES terms(id)
);

CREATE INDEX IF NOT EXISTS idx_subjects_level
ON subjects(level_id);

CREATE INDEX IF NOT EXISTS idx_subjects_term
ON subjects(term_id);

CREATE INDEX IF NOT EXISTS idx_subjects_term_name
ON subjects(term_id, name);

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

-- حسابات إدارية
 CREATE TABLE IF NOT EXISTS admins (
     id INTEGER PRIMARY KEY AUTOINCREMENT,
     tg_user_id INTEGER UNIQUE,
     name TEXT,
     role TEXT NOT NULL,
     permissions_mask INTEGER NOT NULL,
     level_scope TEXT DEFAULT 'all',
     is_active INTEGER NOT NULL DEFAULT 1
 );

-- مجموعات تيليجرام
CREATE TABLE IF NOT EXISTS groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tg_chat_id INTEGER UNIQUE NOT NULL,
    title TEXT,
    level_id INTEGER,
    term_id INTEGER,
    FOREIGN KEY (level_id) REFERENCES levels(id),
    FOREIGN KEY (term_id) REFERENCES terms(id)
);

CREATE INDEX IF NOT EXISTS idx_groups_level
ON groups(level_id);

CREATE INDEX IF NOT EXISTS idx_groups_term
ON groups(term_id);

-- المواضيع داخل المجموعات
CREATE TABLE IF NOT EXISTS topics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id INTEGER NOT NULL,
    tg_topic_id INTEGER NOT NULL,
    subject_id INTEGER NOT NULL,
    section TEXT NOT NULL CHECK(section IN ('theory','discussion','lab')),
    FOREIGN KEY (group_id) REFERENCES groups(id),
    FOREIGN KEY (subject_id) REFERENCES subjects(id),
    UNIQUE (group_id, tg_topic_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_topics_chat
ON topics(group_id, tg_topic_id);

CREATE INDEX IF NOT EXISTS idx_topics_subject
ON topics(subject_id);

-- عمليات الإدخال/الرفع
CREATE TABLE IF NOT EXISTS ingestions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    material_id INTEGER,
    status TEXT NOT NULL,
    tg_message_id INTEGER,
    admin_id INTEGER,
    action TEXT NOT NULL DEFAULT 'add',
    file_unique_id TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (material_id) REFERENCES materials(id),
    FOREIGN KEY (admin_id) REFERENCES admins(id)
);

CREATE INDEX IF NOT EXISTS idx_ingestions_material
ON ingestions(material_id);

CREATE INDEX IF NOT EXISTS idx_ingestions_admin
ON ingestions(admin_id);

-- مواد تعليمية مرتبطة بالمادة + القسم + تصنيف المحتوى
CREATE TABLE IF NOT EXISTS materials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_id INTEGER NOT NULL,
    section TEXT NOT NULL CHECK(section IN ('theory','discussion','lab','syllabus','apps')),
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
    file_unique_id TEXT,
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

CREATE INDEX IF NOT EXISTS idx_materials_subject
ON materials(subject_id);

CREATE INDEX IF NOT EXISTS idx_materials_year
ON materials(year_id);

CREATE INDEX IF NOT EXISTS idx_materials_lecturer
ON materials(lecturer_id);

CREATE INDEX IF NOT EXISTS idx_materials_admin
ON materials(created_by_admin_id);

-- موارد مرتبطة بالترم (مثل جدول الحضور)
CREATE TABLE IF NOT EXISTS term_resources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    term_id INTEGER NOT NULL,
    kind TEXT NOT NULL,
    tg_storage_chat_id INTEGER NOT NULL,
    tg_storage_msg_id INTEGER NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (term_id) REFERENCES terms(id)
);

CREATE INDEX IF NOT EXISTS idx_term_resources_term_kind
ON term_resources(term_id, kind);
