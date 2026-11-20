"""Recurrence expansion using dateutil.rrule with safety limits."""

from datetime import datetime
from typing import List
from dateutil.rrule import rrulestr


def expand_schedule(start_str: str, rrule_str: str, max_occurrences: int = 100) -> List[str]:
    """Expand an RFC 5545 recurrence rule from a start timestamp.
    
    Args:
        start_str: Datetime string formatted as '%Y-%m-%d %H:%M:%S'.
        rrule_str: RRULE string expression, e.g., 'FREQ=DAILY;COUNT=3'.
        max_occurrences: Safety ceiling for infinite recurrence rules.
        
    Returns:
        List of expanded scheduled occurrence strings.
    """
    start_dt = datetime.strptime(start_str, "%Y-%m-%d %H:%M:%S")
    if not rrule_str or str(rrule_str).lower() == "nan" or str(rrule_str).strip() == "":
        return [start_dt.strftime("%Y-%m-%d %H:%M:%S")]
    
    try:
        rule = rrulestr(rrule_str, dtstart=start_dt)
        results = []
        for i, dt in enumerate(rule):
            if i >= max_occurrences:
                break
            results.append(dt.strftime("%Y-%m-%d %H:%M:%S"))
        return results if results else [start_dt.strftime("%Y-%m-%d %H:%M:%S")]
    except Exception:
        return [start_dt.strftime("%Y-%m-%d %H:%M:%S")]
