# mechatronics_archive_bot_telegram

بوت لتجميع وفهرسة مواد قسم الميكاترونكس عبر تيليجرام.

## المتطلبات

- Python 3.12 أو أحدث.
- المكتبات الأساسية: [`python-telegram-bot`](https://python-telegram-bot.org/)، [`aiosqlite`](https://github.com/omnilib/aiosqlite)، [`python-dotenv`](https://github.com/theskumar/python-dotenv).

## الإعداد

1. **إنشاء بيئة افتراضية وتفعيلها**

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # على لينكس/ماك
   .\.venv\Scripts\activate  # على ويندوز
   ```

2. **تثبيت الاعتمادات**

   ```bash
   pip install python-telegram-bot aiosqlite python-dotenv
   ```

3. **إعداد ملف البيئة**

   انسخ المثال ثم عدّل القيم المطلوبة:

   ```bash
   cp .env.example .env
   ```

   أهم المتغيرات:

   ```env
   BOT_TOKEN=...
   ARCHIVE_CHANNEL_ID=...
   GROUP_ID=...
   ADMIN_USER_IDS=...
   OWNER_TG_ID=...
   ```

   `ARCHIVE_CHANNEL_ID` هو معرف قناة تيليجرام التي تُنسخ إليها الرسائل للمستودع.

4. **تهيئة قاعدة البيانات (اختياري)**

   لتحميل البيانات الأولية الموجودة في `seed_data.json` نفّذ:

   ```bash
   python data.py
   ```

## التشغيل

بعد تجهيز البيئة وملف `.env` وتشغيل تهيئة القاعدة، شغّل البوت:

```bash
python -m bot.main
```

سيقوم البرنامج بتهيئة قاعدة البيانات ثم يبدأ الاستماع لتحديثات تيليجرام.

## الوثائق

- [📘 دليل المستخدمين](docs/user_guide_ar.md)
- [🛠️ دليل المشرفين](docs/moderators_guide_ar.md)
- [🧩 قوالب الكابتشن](docs/caption_templates.md)

## الاختبار

لا توجد اختبارات آلية حالياً. للتحقق من سلامة الكود يمكن تجميع ملفات بايثون:

```bash
python -m py_compile $(git ls-files '*.py')
```

كما يمكن تشغيل البوت في بيئة تطويرية للتأكد من عمله باستخدام بيانات `.env` الصحيحة.

