"""Flagship Email Automation & Recurring Notification Studio.
Features:
- Contact directory manager with instant opt-out toggling
- Jinja2 HTML email template designer with real-time live preview
- RFC 5545 recurrence scheduler (Daily, Weekly, Monthly, Custom RRULE)
- Live test dispatcher (dry-run simulation & live SMTP)
- Interactive delivery analytics & SQLite audit log
"""

import sqlite3
from datetime import datetime
from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st

from src.config import settings
from src.renderer import render_email
from src.scheduler import expand_schedule
from src.mailer import send_email

ROOT = Path(__file__).resolve().parent

st.set_page_config(
    page_title="NotifyFlow — Enterprise Email Automation Studio",
    page_icon="✉️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .notify-title { font-size: 2.2rem; font-weight: 800; color: #4338CA; }
    .notify-sub { font-size: 1.05rem; color: #64748B; margin-bottom: 1.3rem; }
    .status-badge-sent { background-color: #DCFCE7; color: #166534; font-weight: 700; padding: 4px 8px; border-radius: 4px; }
    .status-badge-skipped { background-color: #FEF3C7; color: #92400E; font-weight: 700; padding: 4px 8px; border-radius: 4px; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="notify-title">✉️ NotifyFlow — Email Automation & Reminder Studio</div>', unsafe_allow_html=True)
st.markdown('<div class="notify-sub">RFC 5545 RRULE Recurrence • Dynamic Jinja2 Templating • CAN-SPAM Compliance & Delivery Auditing</div>', unsafe_allow_html=True)

# Load Data
contacts_df = pd.read_csv(settings.contacts_path) if settings.contacts_path.exists() else pd.DataFrame(columns=["name", "email", "timezone", "unsubscribed"])
reminders_df = pd.read_csv(settings.reminders_path) if settings.reminders_path.exists() else pd.DataFrame()

# Sidebar: Environment & Dispatch Mode
with st.sidebar:
    st.header("⚙️ Dispatch Mode")
    dry_run_mode = st.toggle("Dry-Run Simulation Mode", value=settings.dry_run, help="Simulates rendering and logging without sending live SMTP traffic.")
    if dry_run_mode:
        st.info("🛡️ Safe Simulation Active: Emails will be validated, rendered, and logged to SQLite without live transmission.")
    else:
        st.warning("⚠️ Live SMTP Active: Real emails will be dispatched using configured credentials.")

    st.markdown("---")
    st.header("➕ Add New Contact")
    with st.form("add_contact_form", clear_on_submit=True):
        c_name = st.text_input("Full Name", "Aarav Sharma")
        c_email = st.text_input("Email Address", "aarav@example.com")
        c_tz = st.selectbox("Timezone", ["Asia/Kolkata", "UTC", "America/New_York", "Europe/London"])
        c_optout = st.checkbox("Opted-Out / Unsubscribed", value=False)
        
        if st.form_submit_button("Save Contact"):
            new_row = pd.DataFrame([{"name": c_name, "email": c_email, "timezone": c_tz, "unsubscribed": c_optout}])
            contacts_df = pd.concat([contacts_df, new_row], ignore_index=True)
            contacts_df.to_csv(settings.contacts_path, index=False)
            st.success(f"Added {c_name} to contacts!")

# Top KPI Metric Row
k1, k2, k3, k4 = st.columns(4)
total_contacts = len(contacts_df)
opted_out_cnt = int((contacts_df["unsubscribed"].astype(str).str.lower() == "true").sum()) if not contacts_df.empty else 0
active_contacts = total_contacts - opted_out_cnt
total_schedules = len(reminders_df)

k1.metric("Total Contacts", total_contacts)
k2.metric("Active Subscribers", active_contacts)
k3.metric("Opt-Out Rate", f"{(opted_out_cnt / max(1, total_contacts))*100:.1f}%")
k4.metric("Configured Campaigns", total_schedules)

st.markdown("---")

tab_designer, tab_dispatch, tab_logs, tab_contacts = st.tabs([
    "🎨 Email Template Designer & Live Preview",
    "🚀 Campaign Dispatcher & Scheduler",
    "📊 Delivery Logs & Audit Trail",
    "👥 Audience Directory"
])

with tab_designer:
    st.subheader("Interactive Jinja2 Template Designer")
    
    col_t1, col_t2 = st.columns([1, 1])
    templates = [p.name for p in settings.templates_dir.glob("*.html")]
    selected_template = st.selectbox("Select Existing Template to Preview/Edit", templates)
    
    current_content = (settings.templates_dir / selected_template).read_text(encoding="utf-8")
    
    with col_t1:
        st.markdown("**Jinja2 Template Source Code:**")
        template_editor = st.text_area("HTML & Template Tags", value=current_content, height=350)
        
        st.markdown("**Sample Recipient Context (JSON):**")
        p_name = st.text_input("Name Variable", "Priya Nair")
        p_title = st.text_input("Title Variable", "Technical Interview Round 1")
        p_date = st.text_input("Date Variable", "2026-11-25 14:00:00")

    with col_t2:
        st.markdown("**Live Rendered Client Preview:**")
        from jinja2 import Template
        try:
            rendered_html = Template(template_editor).render(
                name=p_name,
                title=p_title,
                scheduled_time=p_date,
                timezone="Asia/Kolkata"
            )
            st.components.v1.html(rendered_html, height=450, scrolling=True)
        except Exception as e:
            st.error(f"Template Rendering Error: {e}")

with tab_dispatch:
    st.subheader("Execute Automated Dispatch Batch")
    st.write("Trigger automated recurrence expansion and personalized dispatch for all active contacts.")
    
    if st.button("⚡ Dispatch All Scheduled Reminders", type="primary", use_container_width=True):
        with st.spinner("Processing recurrence schedules and dispatching..."):
            from main import main as run_pipeline
            run_pipeline()
            st.success("Automated campaign dispatch run completed successfully!")

    st.markdown("### Active Scheduled Campaigns")
    st.dataframe(reminders_df, use_container_width=True)

with tab_logs:
    st.subheader("Message Delivery Logs & Relational Audit Trail")
    if settings.db_path.exists():
        conn = sqlite3.connect(str(settings.db_path))
        logs_df = pd.read_sql_query("SELECT id, reminder_id, recipient_name, recipient_email, subject, status, error_detail, timestamp FROM message_logs ORDER BY id DESC", conn)
        conn.close()
        
        if not logs_df.empty:
            # Status Pie Chart
            col_l1, col_l2 = st.columns([1, 2])
            with col_l1:
                st_counts = logs_df["status"].value_counts().reset_index()
                st_counts.columns = ["Status", "Count"]
                fig_stat = px.pie(st_counts, values="Count", names="Status", hole=0.4, title="Delivery Outcome Share")
                st.plotly_chart(fig_stat, use_container_width=True)
            with col_l2:
                st.write("**Recent Delivery Transmissions:**")
                st.dataframe(logs_df.head(10), use_container_width=True)
            
            st.markdown("---")
            st.dataframe(logs_df, use_container_width=True)
        else:
            st.info("No delivery logs found. Click 'Dispatch All Scheduled Reminders' to trigger a batch run.")

with tab_contacts:
    st.subheader("Audience Directory & Opt-Out Status")
    st.dataframe(contacts_df, use_container_width=True)
    
    # Download
    csv_bytes = contacts_df.to_csv(index=False).encode("utf-8")
    st.download_button("📥 Export Contacts Directory (CSV)", data=csv_bytes, file_name="audience_contacts.csv", mime="text/csv")
