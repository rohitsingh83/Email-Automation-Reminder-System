"""Settings are read from a .env file so passwords never live in the code."""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
TEMPLATE_DIR = ROOT / "templates"
OUTPUT_DIR = ROOT / "outputs"
DB_PATH = OUTPUT_DIR / "delivery_log.db"

load_dotenv(ROOT / ".env")


@dataclass
class SmtpSettings:
    host: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    port: int = int(os.getenv("SMTP_PORT", "587"))
    user: str = os.getenv("SMTP_USER", "")
    password: str = os.getenv("SMTP_PASSWORD", "")
    sender_name: str = os.getenv("SENDER_NAME", "Reminder Bot")
    dry_run: bool = os.getenv("DRY_RUN", "true").strip().lower() in {"1", "true", "yes"}

    @property
    def configured(self) -> bool:
        return bool(self.user and self.password)
