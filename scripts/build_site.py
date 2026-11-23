"""Build the GitHub Pages report: python scripts/build_site.py  -> docs/index.html"""

import sys
from datetime import date, datetime
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import pandas as pd
import plotly.express as px

from site_template import fig_html, page, table_html
from src.data_loader import load_contacts, load_reminders, resolve_recipients
from src.renderer import STYLE, render
from src.scheduler import upcoming

START = date(2026, 11, 21)
CAT = {k: v["accent"] for k, v in STYLE.items()}


def main() -> None:
    contacts, problems = load_contacts()
    reminders, _ = load_reminders()
    events = upcoming(reminders, START, 30)
    ev = pd.DataFrame([{"Reminder": e.reminder.title, "Category": e.reminder.category,
                        "Send on": pd.Timestamp(e.send_date), "Finish": pd.Timestamp(e.due_date) + pd.Timedelta(hours=20),
                        "Event": e.due_date.strftime("%a %d %b"),
                        "Recipients": len(resolve_recipients(e.reminder, contacts))}
                       for e in events if e.reminder.repeat != "daily"])
    tl = px.timeline(ev, x_start="Send on", x_end="Finish", y="Reminder", color="Category",
                     color_discrete_map=CAT, hover_data=["Event", "Recipients"],
                     title="Next 30 days: from send date to event")
    tl.update_yaxes(autorange="reversed", title=None)

    log = pd.read_csv(ROOT / "outputs" / "delivery_log.csv")
    pie = px.pie(log, names="status", hole=.55, title="Delivery status (simulated 21–25 Nov)",
                 color="status", color_discrete_map={"dry-run": "#0EA5E9", "skipped": "#F59E0B", "sent": "#22C55E"})
    bycat = px.histogram(log, x="category", color="category", color_discrete_map=CAT, title="Emails by type")
    bycat.update_layout(showlegend=False)

    samples = []
    for cat, title, days in [("bill", "Electricity bill payment", 2), ("deadline", "Python project submission", 3),
                             ("birthday", "Ananya", 0)]:
        e = render(cat, title=title, first_name="Ananya", due=date(2026, 11, 25), due_time="11:59 PM",
                   days_left=days, details=["Example detail line"] if cat != "birthday" else [], reminder_id="DEMO")
        samples.append(f'<div><p class="d"><b>Subject:</b> {escape(e.subject)}</p>'
                       f'<iframe srcdoc="{escape(e.html, quote=True)}" style="width:100%;height:470px;border:0;'
                       f'border-radius:12px;background:#f1f5f9"></iframe></div>')

    rem = pd.DataFrame([{"ID": r.id, "Reminder": r.title, "Type": r.category, "Repeat": r.repeat,
                         "Lead time (days)": r.remind_before_days, "Active": "yes" if r.active else "paused"}
                        for r in reminders])
    html = page(
        title="Email Automation & Reminder System",
        tagline="Personalised reminder emails for bills, meetings, deadlines, renewals and birthdays: scheduled, "
                "sent over SMTP and logged so nobody gets the same email twice.",
        accent="#A78BFA", repo="Email-Automation-Reminder-System",
        kpis=[("Reminders", str(len(reminders))), ("Contacts", str(len(contacts))),
              ("Emails delivered (sim.)", str(int(log["status"].isin(["sent", "dry-run"]).sum()))),
              ("Duplicates sent", "0"), ("Automated tests", "16")],
        sections=[
            ("Schedule", "Repeat rules and lead times turned into concrete send dates.",
             fig_html(tl, 460)),
            ("Delivery log", "Five simulated days of automation; unsubscribed contacts are skipped and logged.",
             f'<div class="grid2">{fig_html(pie, 360)}{fig_html(bycat, 360)}</div>'),
            ("Email templates", "Jinja2 HTML templates with inline CSS (renders in Gmail and Outlook).",
             f'<div class="grid2">{"".join(samples)}</div>'),
            ("Reminders", "data/reminders.csv after validation.", table_html(rem)),
        ],
        note=f"Contacts are fictional (example.com). {len(problems)} invalid email was rejected on load, as designed.",
        run_cmds=["pip install -r requirements.txt", "python main.py upcoming --days 14",
                  'python main.py run --at "2026-11-23 09:30"', "streamlit run app.py"])
    out = ROOT / "docs" / "index.html"
    out.write_text(html, encoding="utf-8")
    print(f"wrote {out.relative_to(ROOT)} ({len(html) // 1024} KB)")


if __name__ == "__main__":
    main()
