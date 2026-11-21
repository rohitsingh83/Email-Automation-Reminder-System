"""
Control centre for the Email Automation & Reminder System.

Run:  streamlit run app.py
"""

from datetime import date, datetime, time, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st
import streamlit.components.v1 as components

from src.config import DATA_DIR, SmtpSettings
from src.data_loader import CATEGORIES, REPEATS, load_contacts, load_reminders, resolve_recipients
from src.engine import run_once
from src.log_store import DeliveryLog
from src.mailer import get_mailer
from src.renderer import STYLE, render
from src.scheduler import birthdays_on, due_now, next_occurrence, upcoming

st.set_page_config(page_title="Reminder Control Centre", page_icon="📬", layout="wide")
CAT_COLOURS = {k: v["accent"] for k, v in STYLE.items()}
STATUS_COLOURS = {"sent": "#16A34A", "dry-run": "#0EA5E9", "skipped": "#F59E0B", "failed": "#DC2626"}

st.markdown("""
<style>
.block-container {padding-top: 1.6rem;}
.hero {background: linear-gradient(120deg, #4C1D95 0%, #7C3AED 55%, #C084FC 100%); color: white;
       padding: 1.4rem 1.8rem; border-radius: 16px; margin-bottom: 1.2rem;}
.hero h1 {margin: 0; font-size: 2rem; color: white;}
.hero p {margin: .3rem 0 0 0; opacity: .92;}
.kpi {background: white; border: 1px solid #E9E5FF; border-radius: 14px; padding: 1rem 1.2rem;
      box-shadow: 0 1px 3px rgba(76,29,149,.07);}
.kpi .label {color: #6B7280; font-size: .82rem; text-transform: uppercase; letter-spacing: .05em;}
.kpi .value {font-size: 1.9rem; font-weight: 700; color: #1E1B4B;}
.kpi .sub {color: #6B7280; font-size: .85rem;}
.event {border-left: 5px solid; background: white; border-radius: 10px; padding: .6rem .9rem; margin-bottom: .5rem;
        box-shadow: 0 1px 2px rgba(0,0,0,.05);}
.event .when {color: #6B7280; font-size: .8rem;}
</style>
""", unsafe_allow_html=True)


def kpi(col, label, value, sub=""):
    col.markdown(f'<div class="kpi"><div class="label">{label}</div><div class="value">{value}</div>'
                 f'<div class="sub">{sub}</div></div>', unsafe_allow_html=True)


settings = SmtpSettings()
contacts, contact_problems = load_contacts()
reminders, reminder_problems = load_reminders()

with st.sidebar:
    st.header("⚙️ Settings")
    today = st.date_input("Today's date (change to simulate)", date.today())
    now_time = st.time_input("Current time", time(9, 30))
    now = datetime.combine(today, now_time)
    dry_run = st.toggle("Dry-run mode (save, don't send)", value=True if not settings.configured else settings.dry_run,
                        disabled=not settings.configured)
    if settings.configured:
        st.success(f"SMTP ready: {settings.user}")
    else:
        st.info("SMTP not configured: emails are saved to outputs/sent_emails. "
                "Copy .env.example to .env to send for real.")
    for p in contact_problems + reminder_problems:
        st.warning(p, icon="⚠️")

active = [r for r in reminders if r.active]
events = upcoming(reminders, today, 30)
log = DeliveryLog()
log_df = log.to_dataframe()

st.markdown(f'<div class="hero"><h1>📬 Email Automation & Reminder System</h1>'
            f'<p>{len(active)} active reminders · {len(contacts)} contacts · '
            f'{"dry-run mode" if dry_run else "live SMTP sending"} · {now:%A %d %B %Y, %I:%M %p}</p></div>',
            unsafe_allow_html=True)

week = [e for e in events if e.send_date <= today + timedelta(days=7)]
c1, c2, c3, c4 = st.columns(4)
kpi(c1, "Active reminders", len(active), f"{len(reminders) - len(active)} paused")
kpi(c2, "Emails next 7 days", sum(len(resolve_recipients(e.reminder, contacts)) for e in week), f"{len(week)} reminder events")
kpi(c3, "Delivered so far", int(log_df["status"].isin(["sent", "dry-run"]).sum()) if not log_df.empty else 0,
    f"{int((log_df['status'] == 'failed').sum()) if not log_df.empty else 0} failed")
bdays = [c for c in contacts if c.birthday and any(birthdays_on([c], today + timedelta(days=d)) for d in range(31))]
kpi(c4, "Birthdays (30 days)", len(bdays), ", ".join(c.first_name for c in bdays[:3]) or "none")
st.write("")

tab_dash, tab_rem, tab_con, tab_tpl, tab_send, tab_log = st.tabs(
    ["🗓️ Schedule", "⏰ Reminders", "👥 Contacts", "🎨 Template studio", "🚀 Send centre", "📜 Delivery log"])

# ------------------------------------------------------------------ schedule
with tab_dash:
    left, right = st.columns([2, 1])
    if events:
        ev = pd.DataFrame([{"Reminder": e.reminder.title, "Category": e.reminder.category,
                            "Send on": pd.Timestamp(e.send_date), "Event": pd.Timestamp(e.due_date),
                            "Finish": pd.Timestamp(e.due_date) + pd.Timedelta(hours=20),
                            "Recipients": len(resolve_recipients(e.reminder, contacts))} for e in events
                           if e.reminder.repeat != "daily"])
        fig = px.timeline(ev, x_start="Send on", x_end="Finish", y="Reminder", color="Category",
                          color_discrete_map=CAT_COLOURS, hover_data=["Event", "Recipients"],
                          title="Next 30 days: each bar runs from the day the reminder is sent to the event (daily reminders hidden)")
        fig.update_yaxes(autorange="reversed", title=None)
        fig.update_layout(height=420, margin=dict(l=10, r=10, t=50, b=10), legend_title=None)
        left.plotly_chart(fig, width="stretch")

        per_day = ev.groupby("Send on")["Recipients"].sum().reset_index()
        bar = px.bar(per_day, x="Send on", y="Recipients", title="Emails per day",
                     color_discrete_sequence=["#7C3AED"])
        bar.update_layout(height=260, margin=dict(l=10, r=10, t=50, b=10))
        left.plotly_chart(bar, width="stretch")

    with right:
        st.markdown("#### Coming up")
        for e in [x for x in events if x.reminder.repeat != "daily"][:8]:
            colour = CAT_COLOURS[e.reminder.category]
            people = ", ".join(c.first_name for c in resolve_recipients(e.reminder, contacts))
            st.markdown(f'<div class="event" style="border-color:{colour}"><b>{STYLE[e.reminder.category]["icon"]} '
                        f'{e.reminder.title}</b><div class="when">send {e.send_date:%a %d %b} → event '
                        f'{e.due_date:%a %d %b} {e.reminder.due:%H:%M}</div><div class="when">to {people}</div></div>',
                        unsafe_allow_html=True)
        for c in bdays:
            nxt = next(today + timedelta(days=d) for d in range(31) if birthdays_on([c], today + timedelta(days=d)))
            st.markdown(f'<div class="event" style="border-color:{CAT_COLOURS["birthday"]}"><b>🎉 {c.name}\'s birthday'
                        f'</b><div class="when">{nxt:%a %d %b}, automatic greeting</div></div>', unsafe_allow_html=True)

# ------------------------------------------------------------------ reminders
with tab_rem:
    st.markdown("Edit reminders directly in the table and click **Save**. Recipients can be emails separated by `;` "
                "or a whole group like `group:team`.")
    rem_df = pd.read_csv(DATA_DIR / "reminders.csv", dtype=str).fillna("")
    edited = st.data_editor(
        rem_df, num_rows="dynamic", width="stretch", hide_index=True, key="rem_editor",
        column_config={
            "category": st.column_config.SelectboxColumn(options=sorted(CATEGORIES)),
            "repeat": st.column_config.SelectboxColumn(options=sorted(REPEATS)),
            "active": st.column_config.SelectboxColumn(options=["yes", "no"]),
        })
    if st.button("💾 Save reminders", type="primary"):
        edited.to_csv(DATA_DIR / "reminders.csv", index=False)
        st.success("Saved data/reminders.csv")
        st.rerun()

    with st.expander("➕ Quick add a reminder"):
        with st.form("add_reminder", clear_on_submit=True):
            a, b, c = st.columns(3)
            title = a.text_input("Title", placeholder="Submit tax return")
            category = b.selectbox("Category", sorted(CATEGORIES))
            repeat = c.selectbox("Repeat", ["none", "daily", "weekly", "monthly", "yearly"])
            a, b, c = st.columns(3)
            due_d = a.date_input("Due date", today + timedelta(days=3))
            due_t = b.time_input("Time", time(10, 0))
            before = c.number_input("Remind days before", 0, 30, 1)
            groups = sorted({x.group for x in contacts})
            recipients = st.multiselect("Recipients", [f"group:{g}" for g in groups] + [x.email for x in contacts])
            details = st.text_input("Details (use | to separate lines)")
            if st.form_submit_button("Add reminder", type="primary") and title and recipients:
                new_id = f"R{len(rem_df) + 1:03d}"
                row = {"id": new_id, "title": title, "category": category, "recipients": ";".join(recipients),
                       "due_date": due_d.isoformat(), "due_time": due_t.strftime("%H:%M"), "repeat": repeat,
                       "remind_before_days": str(before), "details": details, "active": "yes"}
                pd.concat([rem_df, pd.DataFrame([row])]).to_csv(DATA_DIR / "reminders.csv", index=False)
                st.success(f"Added {new_id}: {title}")
                st.rerun()

    st.markdown("#### Next occurrence of each reminder")
    nxt_rows = []
    for r in reminders:
        n = next_occurrence(r, today)
        nxt_rows.append({"ID": r.id, "Title": r.title, "Repeat": r.repeat, "Active": "✅" if r.active else "⏸️",
                         "Next event": n.strftime("%a %d %b %Y") if n else "finished",
                         "Recipients": len(resolve_recipients(r, contacts))})
    st.dataframe(pd.DataFrame(nxt_rows), hide_index=True, width="stretch")

# ------------------------------------------------------------------ contacts
with tab_con:
    con_df = pd.read_csv(DATA_DIR / "contacts.csv", dtype=str).fillna("")
    cl, cr = st.columns([2, 1])
    with cl:
        edited_c = st.data_editor(con_df, num_rows="dynamic", width="stretch", hide_index=True,
                                  column_config={"subscribed": st.column_config.SelectboxColumn(options=["yes", "no"])})
        if st.button("💾 Save contacts", type="primary"):
            edited_c.to_csv(DATA_DIR / "contacts.csv", index=False)
            st.success("Saved data/contacts.csv")
            st.rerun()
    with cr:
        grp = con_df.groupby("group").size().reset_index(name="contacts")
        pie = px.pie(grp, names="group", values="contacts", hole=.5, title="Contacts by group",
                     color_discrete_sequence=px.colors.sequential.Purples_r)
        pie.update_layout(height=300, margin=dict(l=10, r=10, t=50, b=10))
        st.plotly_chart(pie, width="stretch")
        unsub = con_df[con_df["subscribed"].str.lower() != "yes"]["name"].tolist()
        st.metric("Unsubscribed", len(unsub), help=", ".join(unsub))
        if contact_problems:
            st.error(f"{len(contact_problems)} contact(s) have an invalid email and will be skipped.")

# ------------------------------------------------------------------ template studio
with tab_tpl:
    a, b = st.columns([1, 2])
    with a:
        category = st.selectbox("Template", list(STYLE), index=list(STYLE).index("deadline"), format_func=lambda c: f"{STYLE[c]['icon']} {c.title()}")
        t_title = st.text_input("Title", "Python project submission" if category != "birthday" else "Ananya")
        t_name = st.text_input("Recipient first name", "Ananya")
        t_due = st.date_input("Event date", today + timedelta(days=2), key="tpl_date")
        t_time = st.time_input("Event time", time(23, 59), key="tpl_time")
        t_details = st.text_area("Details (one per line)", "Upload your GitHub link\nAdd LinkedIn and Instagram screenshots")
    email = render(category, title=t_title, first_name=t_name, due=t_due, due_time=t_time.strftime("%I:%M %p"),
                   days_left=max((t_due - today).days, 0), details=[d for d in t_details.splitlines() if d.strip()],
                   reminder_id="PREVIEW", sender_name=settings.sender_name)
    with b:
        st.markdown(f"**Subject:** {email.subject}")
        components.html(email.html, height=620, scrolling=True)
        with st.expander("Plain-text version (for email apps without HTML)"):
            st.code(email.text, language=None)

# ------------------------------------------------------------------ send centre
with tab_send:
    due = due_now(reminders, now)
    birthdays_today = birthdays_on(contacts, today) if now.hour >= 8 else []
    st.markdown(f"#### Due at {now:%d %b %Y %I:%M %p}")
    if not due and not birthdays_today:
        st.info("Nothing is due at this date/time. Change the date in the sidebar to simulate another day.")
    for occ in due:
        people = resolve_recipients(occ.reminder, contacts)
        st.markdown(f"- **{occ.reminder.title}** ({occ.reminder.category}) → {', '.join(p.name for p in people)}"
                    f" · event {occ.due_date:%d %b}")
    for c in birthdays_today:
        st.markdown(f"- 🎉 **Birthday greeting** → {c.name}")

    if st.button("🚀 Run automation now", type="primary", disabled=not (due or birthdays_today)):
        mailer = get_mailer(settings, force_dry_run=dry_run)
        results = run_once(now, reminders, contacts, mailer, log, settings)
        res = pd.DataFrame([r.__dict__ for r in results])
        st.dataframe(res, hide_index=True, width="stretch")
        st.success(f"Done: {sum(res['status'].isin(['sent', 'dry-run']))} delivered, "
                   f"{sum(res['status'] == 'skipped')} skipped, {sum(res['status'] == 'duplicate')} duplicates prevented.")

    st.divider()
    st.markdown("#### Send a test email")
    to = st.text_input("Your email address", placeholder="you@gmail.com")
    if st.button("Send test", disabled=not to):
        mailer = get_mailer(settings, force_dry_run=dry_run)
        test = render("general", title="Test email", first_name="there", due=today, due_time=now.strftime("%I:%M %p"),
                      details=["If you can read this, everything works."], sender_name=settings.sender_name)
        try:
            st.success(mailer.send(test, "Test", to, "test"))
        except Exception as exc:
            st.error(str(exc))

# ------------------------------------------------------------------ log
with tab_log:
    log_df = log.to_dataframe()
    if log_df.empty:
        st.info("No deliveries yet. Run the automation from the Send centre or with `python main.py run`.")
    else:
        l1, l2 = st.columns(2)
        stat = log_df.groupby("status").size().reset_index(name="count")
        p1 = px.pie(stat, names="status", values="count", hole=.5, color="status",
                    color_discrete_map=STATUS_COLOURS, title="Delivery status")
        p1.update_layout(height=300, margin=dict(l=10, r=10, t=50, b=10))
        l1.plotly_chart(p1, width="stretch")
        cat = log_df.groupby("category").size().reset_index(name="emails")
        p2 = px.bar(cat, x="category", y="emails", color="category", color_discrete_map=CAT_COLOURS,
                    title="Emails by category")
        p2.update_layout(height=300, showlegend=False, margin=dict(l=10, r=10, t=50, b=10))
        l2.plotly_chart(p2, width="stretch")
        status_filter = st.multiselect("Status", sorted(log_df["status"].unique()), default=sorted(log_df["status"].unique()))
        view = log_df[log_df["status"].isin(status_filter)]
        st.dataframe(view.drop(columns=["id"]), hide_index=True, width="stretch")
        st.download_button("⬇️ Download log (CSV)", view.to_csv(index=False), "delivery_log.csv", "text/csv")
log.close()
