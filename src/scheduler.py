"""Recurrence expansion using dateutil.rrule."""

from datetime import datetime
from typing import List
from dateutil.rrule import rrulestr


def expand_schedule(start_str: str, rrule_str: str) -> List[str]:
    start_dt = datetime.strptime(start_str, "%Y-%m-%d %H:%M:%S")
    if not rrule_str or str(rrule_str).lower() == "nan":
        return [start_dt.strftime("%Y-%m-%d %H:%M:%S")]
    rule = rrulestr(rrule_str, dtstart=start_dt)
    return [dt.strftime("%Y-%m-%d %H:%M:%S") for dt in rule]
