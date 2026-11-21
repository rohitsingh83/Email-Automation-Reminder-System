"""
Turn a reminder + contact into a personalised email using Jinja2 templates.

Each category has its own template (templates/<category>.html) that extends
base.html, plus a colour, icon and subject line.
"""

import re
from dataclasses import dataclass
from datetime import date
from html import unescape

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .config import TEMPLATE_DIR

STYLE = {
    "meeting":  {"accent": "#2563EB", "icon": "📅", "label": "Meeting reminder"},
    "bill":     {"accent": "#DC2626", "icon": "💳", "label": "Payment due"},
    "deadline": {"accent": "#7C3AED", "icon": "⏰", "label": "Deadline approaching"},
    "renewal":  {"accent": "#D97706", "icon": "🔄", "label": "Renewal reminder"},
    "general":  {"accent": "#0F766E", "icon": "🔔", "label": "Reminder"},
    "birthday": {"accent": "#DB2777", "icon": "🎉", "label": "Happy birthday"},
}

env = Environment(loader=FileSystemLoader(TEMPLATE_DIR), autoescape=select_autoescape(["html"]))


@dataclass
class RenderedEmail:
    subject: str
    html: str
    text: str


def subject_line(category: str, title: str, days_left: int) -> str:
    when = "today" if days_left == 0 else "tomorrow" if days_left == 1 else f"in {days_left} days"
    return {
        "meeting": f"📅 Reminder: {title} {when}",
        "bill": f"💳 Payment due {when}: {title}",
        "deadline": f"⏰ {title}: due {when}",
        "renewal": f"🔄 Renewal {when}: {title}",
        "birthday": f"🎉 Happy Birthday, {title}!",
    }.get(category, f"🔔 Reminder: {title} ({when})")


def html_to_text(html: str) -> str:
    """Plain-text version for email clients that don't show HTML."""
    text = re.sub(r"<(br|/p|/tr|/div)[^>]*>", "\n", html)
    text = re.sub(r"<[^>]+>", "", text)
    return re.sub(r"\n\s*\n+", "\n\n", unescape(text)).strip()


def render(category: str, *, title: str, first_name: str, due: date | None = None, due_time: str = "",
           days_left: int = 0, details: list[str] | None = None, reminder_id: str = "-",
           sender_name: str = "Reminder Bot") -> RenderedEmail:
    style = STYLE.get(category, STYLE["general"])
    template = env.get_template(f"{category}.html")
    html = template.render(**style, title=title, first_name=first_name, days_left=days_left,
                           due_label=due.strftime("%A, %d %B %Y") if due else "", due_time=due_time,
                           details=details or [], reminder_id=reminder_id, sender_name=sender_name)
    subject_title = first_name if category == "birthday" else title
    return RenderedEmail(subject_line(category, subject_title, days_left), html, html_to_text(html))
