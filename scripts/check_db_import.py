import importlib, sys
print(f"Python: {sys.version}")
try:
    pkg = importlib.import_module("bot.db")
    print("✓ imported: bot.db")
    for name in ("admins","topics","subjects","materials","years","lecturers"):
        m = importlib.import_module(f"bot.db.{name}")
        print(f"✓ imported: bot.db.{name}")
    print("✅ DB imports OK")
except Exception as e:
    print("❌ DB import failed:", e)
    raise
