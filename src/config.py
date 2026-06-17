import logging
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

log = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN", "")

ADMIN_IDS: list[int] = [
    int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip().isdigit()
]
if not ADMIN_IDS:
    log.warning("ADMIN_IDS пуст. Админ-команды будут недоступны.")

CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME", "").strip()
CHANNEL_URL = os.getenv("CHANNEL_URL", "").strip()

REDIS_URL = os.getenv("REDIS_URL", "").strip()

DATABASE_URL = os.getenv("DATABASE_URL", "")
if not DATABASE_URL:
    DB_PATH = Path("backend/data/cargo_tps.db")
    DATABASE_URL = f"sqlite+aiosqlite:///{DB_PATH}"
