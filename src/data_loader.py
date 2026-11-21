"""
Load contacts and reminders from CSV and check them for problems.

Bad rows (invalid email, unknown category, broken date) are reported instead
of crashing the program. Real-world data is never perfect.
"""

import re
from dataclasses import dataclass
from datetime import date, datetime, time
from pathlib import Path

import pandas as pd

from .config import DATA_DIR

EMAIL_RE = re.compile(r"^[\w.+-]+@[\w-]+(\.[\w-]+)*\.[A-Za-z]{2,}$")
CATEGORIES = {"meeting", "bill", "deadline", "renewal", "general"}
REPEATS = {"none", "daily", "weekly", "monthly", "yearly"}
YES = {"yes", "y", "true", "1"}


@dataclass
class Contact:
    name: str
    email: str
    group: str
    birthday: date | None
    subscribed: bool

    @property
    def first_name(self) -> str:
        return self.name.split()[0]


@dataclass
class Reminder:
    id: str
    title: str
    category: str
    recipients: list[str]          # emails or "group:<name>"
    due: datetime
    repeat: str
    remind_before_days: int
    details: list[str]
    active: bool


def is_valid_email(email: str) -> bool:
    return bool(EMAIL_RE.match(email.strip()))


def load_contacts(path: Path = DATA_DIR / "contacts.csv") -> tuple[list[Contact], list[str]]:
    df = pd.read_csv(path, dtype=str).fillna("")
    contacts, problems = [], []
    for i, row in df.iterrows():
        email = row["email"].strip().lower()
        if not is_valid_email(email):
            problems.append(f"contacts.csv row {i + 2}: invalid email '{row['email']}' ({row['name']})")
            continue
        try:
            bday = datetime.strptime(row["birthday"], "%Y-%m-%d").date() if row["birthday"] else None
        except ValueError:
            problems.append(f"contacts.csv row {i + 2}: bad birthday '{row['birthday']}', expected YYYY-MM-DD")
            bday = None
        contacts.append(Contact(row["name"].strip(), email, row["group"].strip().lower(), bday,
                                row["subscribed"].strip().lower() in YES))
    return contacts, problems


def load_reminders(path: Path = DATA_DIR / "reminders.csv") -> tuple[list[Reminder], list[str]]:
    df = pd.read_csv(path, dtype=str).fillna("")
    reminders, problems = [], []
    for i, row in df.iterrows():
        where = f"reminders.csv row {i + 2} ({row['id']})"
        category = row["category"].strip().lower()
        repeat = (row["repeat"].strip().lower() or "none")
        try:
            due = datetime.combine(datetime.strptime(row["due_date"], "%Y-%m-%d").date(),
                                   time.fromisoformat(row["due_time"] or "09:00"))
        except ValueError:
            problems.append(f"{where}: bad date/time '{row['due_date']} {row['due_time']}'")
            continue
        if category not in CATEGORIES:
            problems.append(f"{where}: unknown category '{category}', using 'general'")
            category = "general"
        if repeat not in REPEATS:
            problems.append(f"{where}: unknown repeat '{repeat}', using 'none'")
            repeat = "none"
        reminders.append(Reminder(
            id=row["id"].strip(), title=row["title"].strip(), category=category,
            recipients=[r.strip().lower() for r in row["recipients"].split(";") if r.strip()],
            due=due, repeat=repeat, remind_before_days=int(row["remind_before_days"] or 0),
            details=[d.strip() for d in row["details"].split("|") if d.strip()],
            active=row["active"].strip().lower() in YES))
    return reminders, problems


def resolve_recipients(reminder: Reminder, contacts: list[Contact]) -> list[Contact]:
    """Expand 'group:team' into the contacts of that group; look up plain emails."""
    by_email = {c.email: c for c in contacts}
    result: dict[str, Contact] = {}
    for target in reminder.recipients:
        if target.startswith("group:"):
            group = target.split(":", 1)[1]
            for c in contacts:
                if c.group == group:
                    result[c.email] = c
        elif target in by_email:
            result[target] = by_email[target]
        elif is_valid_email(target):
            result[target] = Contact(target.split("@")[0].title(), target, "", None, True)
    return list(result.values())
