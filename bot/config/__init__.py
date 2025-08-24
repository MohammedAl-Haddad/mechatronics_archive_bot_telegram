"""Load configuration values from environment variables."""

import os
from datetime import datetime
from dotenv import load_dotenv

from .constants import ENV_FILE


load_dotenv(ENV_FILE)

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is missing in .env")


def _to_int(env_key: str) -> int | None:
    val = os.getenv(env_key)
    return int(val) if val and val.strip() else None


ARCHIVE_CHANNEL_ID = _to_int("ARCHIVE_CHANNEL_ID")
if ARCHIVE_CHANNEL_ID is None:
    raise RuntimeError("ARCHIVE_CHANNEL_ID is missing in .env")
GROUP_ID = _to_int("GROUP_ID")

OWNER_TG_ID = _to_int("OWNER_TG_ID")
if OWNER_TG_ID is None:
    raise RuntimeError("OWNER_TG_ID is missing in .env")

_admin = os.getenv("ADMIN_USER_IDS", "")
ADMIN_USER_IDS = [int(x) for x in _admin.split(",") if x.strip().isdigit()]

VERSION = os.getenv("COMMIT_SHA", "dev")
START_TIME = datetime.now()

