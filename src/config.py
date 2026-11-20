"""Centralized configuration for Email Automation & Reminder System."""

from dataclasses import dataclass, field
import os
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    root_dir: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent)
    data_dir: Path = field(init=False)
    db_dir: Path = field(init=False)
    outputs_dir: Path = field(init=False)
    logs_dir: Path = field(init=False)
    templates_dir: Path = field(init=False)
    
    db_path: Path = field(init=False)
    schema_path: Path = field(init=False)
    contacts_path: Path = field(init=False)
    reminders_path: Path = field(init=False)
    log_file_path: Path = field(init=False)
    
    dry_run: bool = os.getenv("DRY_RUN", "true").lower() == "true"
    smtp_host: str = os.getenv("SMTP_HOST", "smtp.example.com")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_user: str = os.getenv("SMTP_USER", "")
    smtp_pass: str = os.getenv("SMTP_PASS", "")
    max_occurrences: int = int(os.getenv("MAX_OCCURRENCES", "100"))

    def __post_init__(self):
        root = self.root_dir
        object.__setattr__(self, "data_dir", root / "data")
        object.__setattr__(self, "db_dir", root / "db")
        object.__setattr__(self, "outputs_dir", root / "outputs")
        object.__setattr__(self, "logs_dir", root / "logs")
        object.__setattr__(self, "templates_dir", root / "templates")
        
        object.__setattr__(self, "db_path", root / "db" / "email.db")
        object.__setattr__(self, "schema_path", root / "db" / "schema.sql")
        object.__setattr__(self, "contacts_path", root / "data" / "contacts.csv")
        object.__setattr__(self, "reminders_path", root / "data" / "reminders.csv")
        object.__setattr__(self, "log_file_path", root / "logs" / "automation.log")
        
        self.outputs_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.db_dir.mkdir(parents=True, exist_ok=True)


settings = Settings()
