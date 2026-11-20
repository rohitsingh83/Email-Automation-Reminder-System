"""Recurrence expansion using dateutil.rrule with safety limits and flexible date parsing."""

from datetime import datetime
from typing import List
from dateutil.rrule import rrulestr
import dateutil.parser


def parse_flexible_datetime(dt_str: str) -> datetime:
    """Parse timestamps flexibly supporting ISO 8601 and standard space formats."""
    cleaned = str(dt_str).strip()
    try:
        return datetime.strptime(cleaned, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return dateutil.parser.parse(cleaned)


def expand_schedule(start_str: str, rrule_str: str, max_occurrences: int = 100) -> List[str]:
    """Expand an RFC 5545 recurrence rule from a start timestamp with bounded execution.
    
    Args:
        start_str: Datetime string (e.g. '2026-11-20 19:00:00' or ISO).
        rrule_str: RFC 5545 RRULE string expression.
        max_occurrences: Safety ceiling preventing runaway loops.
        
    Returns:
        List of formatted scheduled occurrence strings.
    """
    try:
        start_dt = parse_flexible_datetime(start_str)
    except Exception:
        return [str(start_str)]
        
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
