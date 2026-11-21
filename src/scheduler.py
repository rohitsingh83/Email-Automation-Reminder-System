"""
Work out *when* each reminder should be sent.

A reminder has a due date, an optional repeat rule (daily / weekly / monthly /
yearly) and a lead time ("remind me 2 days before"). For any moment we can ask:
  - next_occurrence(): the next due date on or after a day
  - send_date():       due date minus the lead time
  - due_now():         reminders whose send date is today and send time has passed
"""

import calendar
from dataclasses import dataclass
from datetime import date, datetime, timedelta

from .data_loader import Contact, Reminder


def add_months(d: date, months: int) -> date:
    """Same day next month; 31 Jan + 1 month = 28/29 Feb (last valid day)."""
    month = d.month - 1 + months
    year, month = d.year + month // 12, month % 12 + 1
    return date(year, month, min(d.day, calendar.monthrange(year, month)[1]))


def next_occurrence(reminder: Reminder, on_or_after: date) -> date | None:
    """First due date >= on_or_after, or None if a one-time reminder has passed."""
    due = reminder.due.date()
    if due >= on_or_after or reminder.repeat == "none":
        return due if due >= on_or_after else None
    if reminder.repeat == "daily":
        return on_or_after
    if reminder.repeat == "weekly":
        return due + timedelta(days=-(-(on_or_after - due).days // 7) * 7)
    step = 1 if reminder.repeat == "monthly" else 12
    n = 0
    while add_months(due, n) < on_or_after:
        n += step
    return add_months(due, n)


@dataclass
class Occurrence:
    reminder: Reminder
    due_date: date
    send_date: date

    @property
    def days_left(self) -> int:
        return (self.due_date - self.send_date).days


def occurrence_for_send_day(reminder: Reminder, day: date) -> Occurrence | None:
    """The occurrence that should be *sent* on `day` (taking the lead time into account)."""
    due = next_occurrence(reminder, day + timedelta(days=reminder.remind_before_days))
    if due is None:
        return None
    send = due - timedelta(days=reminder.remind_before_days)
    return Occurrence(reminder, due, send) if send == day else None


def due_now(reminders: list[Reminder], now: datetime) -> list[Occurrence]:
    """Active reminders to send today whose send time has been reached."""
    result = []
    for r in reminders:
        if not r.active:
            continue
        occ = occurrence_for_send_day(r, now.date())
        # Lead-time reminders go out at 08:00; same-day reminders 1 hour before the event.
        if occ:
            send_at = datetime.combine(now.date(), r.due.time()) - timedelta(hours=1) if occ.days_left == 0 \
                else datetime.combine(now.date(), datetime.strptime("08:00", "%H:%M").time())
            if now >= send_at:
                result.append(occ)
    return result


def upcoming(reminders: list[Reminder], start: date, days: int = 30) -> list[Occurrence]:
    """Every send event in the next `days` days (for the dashboard calendar)."""
    events = []
    for offset in range(days + 1):
        day = start + timedelta(days=offset)
        for r in reminders:
            if r.active and (occ := occurrence_for_send_day(r, day)):
                events.append(occ)
    return events


def birthdays_on(contacts: list[Contact], day: date) -> list[Contact]:
    """Contacts whose birthday is on `day` (29 Feb birthdays are celebrated on 28 Feb)."""
    result = []
    for c in contacts:
        if not c.birthday:
            continue
        month, d = c.birthday.month, c.birthday.day
        if month == 2 and d == 29 and not calendar.isleap(day.year):
            d = 28
        if (month, d) == (day.month, day.day):
            result.append(c)
    return result
