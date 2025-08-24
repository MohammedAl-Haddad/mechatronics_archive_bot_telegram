#!/usr/bin/env python3
"""Quick semantic checks ensuring runtime environment sanity."""
from __future__ import annotations

import compileall
import os
import sys
from pathlib import Path

# Show Python version early
print(f"Python: {sys.version}")

# Provide dummy environment variables so config imports don't fail
os.environ.setdefault("BOT_TOKEN", "dummy")
os.environ.setdefault("ARCHIVE_CHANNEL_ID", "0")
os.environ.setdefault("OWNER_TG_ID", "0")

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

# ---------------------------------------------------------------------------
# asyncio import and loop policy sanity
# ---------------------------------------------------------------------------
try:
    import asyncio
    policy = asyncio.get_event_loop_policy()
    if policy.__class__.__name__ == "WindowsSelectorEventLoopPolicy":
        print("سياسة الحلقة الافتراضية قديمة وغير مدعومة في بايثون ٣٫١٢")
        sys.exit(1)
except Exception as e:
    print(f"فشل استيراد asyncio: {e}")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Compile all modules to bytecode (redundant but useful)
# ---------------------------------------------------------------------------
for mod in ("bot", "keyboards"):
    if not compileall.compile_dir(REPO_ROOT / mod, quiet=1):
        print(f"تعذر ترجمة ملفات {mod}")
        sys.exit(1)

# ---------------------------------------------------------------------------
# python-telegram-bot version check
# ---------------------------------------------------------------------------
try:
    import telegram
    parts = tuple(int(p) for p in telegram.__version__.split(".")[:2])
    if parts < (20, 8):
        print("الرجاء التحديث إلى python-telegram-bot 20.8 أو أحدث")
        sys.exit(1)
except Exception as e:
    print(f"تعذر استيراد مكتبة telegram: {e}")
    sys.exit(1)

# ---------------------------------------------------------------------------
# uvloop import is optional and skipped on Windows
# ---------------------------------------------------------------------------
if sys.platform != "win32":
    try:
        import uvloop  # noqa: F401
    except ImportError:
        pass
    except Exception as e:
        print(f"مشكلة عند استيراد uvloop: {e}")
        sys.exit(1)

# ---------------------------------------------------------------------------
# Import critical modules and verify important callables
# ---------------------------------------------------------------------------
try:
    import bot.main  # noqa: F401
    from bot.db import admins, topics
    from bot import parser
except Exception as e:
    print(f"فشل استيراد الوحدات الأساسية: {e}")
    sys.exit(1)

for name in ("is_owner", "has_perm", "ensure_owner_full_perms"):
    if not callable(getattr(admins, name, None)):
        print(f"الدالة {name} غير موجودة في admins")
        sys.exit(1)

for name in ("bind", "get_binding"):
    if not callable(getattr(topics, name, None)):
        print(f"الدالة {name} غير موجودة في topics")
        sys.exit(1)

if not callable(getattr(parser, "extract_hijri_year", None)):
    print("الدالة extract_hijri_year غير موجودة في parser")
    sys.exit(1)

print("جميع الفحوصات ناجحة")
