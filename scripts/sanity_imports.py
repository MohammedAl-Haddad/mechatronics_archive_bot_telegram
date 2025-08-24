#!/usr/bin/env python3
"""Import every project module to ensure wiring is valid."""

from __future__ import annotations

import compileall
import importlib
import os
import sys
import traceback
from pathlib import Path

# Provide dummy environment variables so config imports don't fail.
os.environ.setdefault("BOT_TOKEN", "dummy")
os.environ.setdefault("ARCHIVE_CHANNEL_ID", "0")
os.environ.setdefault("OWNER_TG_ID", "0")

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

# Compile all modules to bytecode to catch syntax errors.
if not compileall.compile_dir(REPO_ROOT / "bot", quiet=1):
    sys.exit(1)
if not compileall.compile_dir(REPO_ROOT / "keyboards", quiet=1):
    sys.exit(1)

modules: list[str] = []
for base in ("bot", "keyboards"):
    for path in (REPO_ROOT / base).rglob("*.py"):
        if path.name == "__init__.py":
            continue
        module = ".".join(path.relative_to(REPO_ROOT).with_suffix("").parts)
        modules.append(module)

for name in sorted(modules):
    try:
        importlib.import_module(name)
        print(f"PASS {name}")
    except Exception:
        print(f"FAIL {name}")
        traceback.print_exc()
        sys.exit(1)

print("All imports passed")
