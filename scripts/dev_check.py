#!/usr/bin/env python3
"""Run development sanity checks."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def run(args: list[str]) -> None:
    proc = subprocess.run([sys.executable, *args], cwd=ROOT)
    if proc.returncode != 0:
        sys.exit(proc.returncode)

if __name__ == "__main__":
    run(["scripts/sanity_imports.py"])
    run(["scripts/audit_incompletes.py"])
    run(["scripts/smoke_checks.py"])
