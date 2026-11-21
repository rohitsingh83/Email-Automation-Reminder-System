"""Run with:  python -m pytest -q"""

from datetime import date, datetime

import pytest

from src.config import SmtpSettings
from src.data_loader import Contact, Reminder, is_valid_email, load_contacts, load_reminders, resolve_recipients
from src.engine import run_once
from src.log_store import DeliveryLog
from src.mailer import DryRunMailer, SmtpMailer
from src.renderer import render
from src.scheduler import add_months, birthdays_on, due_now, next_occurrence, occurrence_for_send_day


def make_reminder(**kw) -> Reminder:
    base = dict(id="T1", title="Test", category="meeting", recipients=["group:team"],
                due=datetime(2026, 1, 31, 10, 0), repeat="none", remind_before_days=0, details=[], active=True)
    base.update(kw)
    return Reminder(**base)


CONTACTS = [
    Contact("Asha Rao", "asha@example.com", "team", date(2000, 2, 29), True),
    Contact("Ravi Kumar", "ravi@example.com", "team", None, False),
    Contact("Neha Shah", "neha@example.com", "family", date(1999, 6, 15), True),
]


def test_email_validation():
    assert is_valid_email("a.b+tag@gmail.com")
    assert not is_valid_email("vikram.joshi@example")
    assert not is_valid_email("no-at-sign.com")


def test_sample_data_loads_and_reports_problems():
    contacts, problems = load_contacts()
    reminders, rproblems = load_reminders()
    assert len(contacts) == 9 and len(problems) == 1   # one invalid email in the sample
    assert len(reminders) == 9 and not rproblems


def test_month_end_repeat_clamps_to_last_day():
    assert add_months(date(2026, 1, 31), 1) == date(2026, 2, 28)
    assert add_months(date(2028, 1, 31), 1) == date(2028, 2, 29)   # leap year


@pytest.mark.parametrize("repeat,after,expected", [
    ("none", date(2026, 1, 20), date(2026, 1, 31)),
    ("none", date(2026, 2, 1), None),
    ("weekly", date(2026, 2, 3), date(2026, 2, 7)),
    ("monthly", date(2026, 2, 10), date(2026, 2, 28)),
    ("yearly", date(2026, 3, 1), date(2027, 1, 31)),
    ("daily", date(2026, 5, 5), date(2026, 5, 5)),
])
def test_next_occurrence(repeat, after, expected):
    assert next_occurrence(make_reminder(repeat=repeat), after) == expected


def test_lead_time_moves_the_send_date():
    r = make_reminder(remind_before_days=3)
    assert occurrence_for_send_day(r, date(2026, 1, 28)).days_left == 3
    assert occurrence_for_send_day(r, date(2026, 1, 29)) is None


def test_same_day_reminder_waits_until_one_hour_before():
    r = make_reminder()
    assert due_now([r], datetime(2026, 1, 31, 8, 30)) == []
    assert len(due_now([r], datetime(2026, 1, 31, 9, 0))) == 1
    assert due_now([make_reminder(active=False)], datetime(2026, 1, 31, 9, 30)) == []


def test_groups_expand_and_duplicates_merge():
    r = make_reminder(recipients=["group:team", "asha@example.com", "new.person@example.com"])
    emails = [c.email for c in resolve_recipients(r, CONTACTS)]
    assert emails == ["asha@example.com", "ravi@example.com", "new.person@example.com"]


def test_leap_day_birthday_on_non_leap_year():
    assert [c.name for c in birthdays_on(CONTACTS, date(2026, 2, 28))] == ["Asha Rao"]


def test_templates_render_personalised_html_and_text():
    email = render("bill", title="Rent", first_name="Asha", due=date(2026, 2, 1), days_left=2,
                   details=["Amount: Rs 15000"])
    assert "Hi Asha" in email.html and "Rs 15000" in email.html
    assert email.subject.startswith("💳") and "in 2 days" in email.subject
    assert "<" not in email.text


def test_engine_skips_unsubscribed_and_never_sends_twice(tmp_path):
    settings = SmtpSettings(user="", password="", dry_run=True)
    mailer = DryRunMailer(settings, folder=tmp_path / "mail")
    log = DeliveryLog(tmp_path / "log.db")
    r = make_reminder()
    now = datetime(2026, 1, 31, 9, 30)

    first = {res.email: res.status for res in run_once(now, [r], CONTACTS, mailer, log, settings, False)}
    assert first == {"asha@example.com": "dry-run", "ravi@example.com": "skipped"}
    assert len(list((tmp_path / "mail").glob("*.eml"))) == 1

    second = run_once(now, [r], CONTACTS, mailer, log, settings, False)
    assert [res.status for res in second if res.email == "asha@example.com"] == ["duplicate"]
    log.close()


def test_smtp_mailer_requires_credentials():
    with pytest.raises(ValueError):
        SmtpMailer(SmtpSettings(user="", password=""))
