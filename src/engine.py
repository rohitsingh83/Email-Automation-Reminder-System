"""
The automation loop: find what is due, personalise it, send it, log it.

    for each reminder due now (and each birthday today):
        for each recipient:
            skip if unsubscribed or already sent for this occurrence
            render the template -> send (or save in dry-run) -> write to the log
"""

from dataclasses import dataclass
from datetime import datetime

from .config import SmtpSettings
from .data_loader import Contact, Reminder, resolve_recipients
from .log_store import DeliveryLog
from .renderer import render
from .scheduler import birthdays_on, due_now


@dataclass
class Result:
    reminder_id: str
    title: str
    recipient: str
    email: str
    status: str
    detail: str


def _deliver(mailer, log: DeliveryLog, settings: SmtpSettings, *, reminder_id: str, title: str, category: str,
             contact: Contact, occurrence: str, render_kwargs: dict) -> Result:
    def done(status: str, detail: str) -> Result:
        log.record(reminder_id, title, category, contact.name, contact.email, occurrence, status, detail, mailer.mode)
        return Result(reminder_id, title, contact.name, contact.email, status, detail)

    if not contact.subscribed:
        return done("skipped", "contact unsubscribed")
    if log.already_sent(reminder_id, contact.email, occurrence):
        return Result(reminder_id, title, contact.name, contact.email, "duplicate", "already sent, not repeated")
    email = render(category, first_name=contact.first_name, reminder_id=reminder_id,
                   sender_name=settings.sender_name, **render_kwargs)
    try:
        detail = mailer.send(email, contact.name, contact.email, f"{reminder_id}_{occurrence}")
        return done("dry-run" if mailer.mode == "dry-run" else "sent", detail)
    except Exception as exc:  # one failed address must not stop the others
        return done("failed", str(exc))


def run_once(now: datetime, reminders: list[Reminder], contacts: list[Contact], mailer, log: DeliveryLog,
             settings: SmtpSettings, include_birthdays: bool = True) -> list[Result]:
    results = []
    for occ in due_now(reminders, now):
        r = occ.reminder
        for contact in resolve_recipients(r, contacts):
            results.append(_deliver(
                mailer, log, settings, reminder_id=r.id, title=r.title, category=r.category, contact=contact,
                occurrence=occ.due_date.isoformat(),
                render_kwargs=dict(title=r.title, due=occ.due_date, due_time=r.due.strftime("%I:%M %p"),
                                   days_left=occ.days_left, details=r.details)))

    if include_birthdays and now.hour >= 8:
        for contact in birthdays_on(contacts, now.date()):
            results.append(_deliver(
                mailer, log, settings, reminder_id="BDAY", title=f"Birthday: {contact.name}", category="birthday",
                contact=contact, occurrence=now.date().isoformat(),
                render_kwargs=dict(title=contact.first_name, due=now.date(), days_left=0)))
    return results
