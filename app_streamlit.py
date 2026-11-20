"""Interactive Streamlit dashboard for Email Automation & Reminder System."""
from pathlib import Path
import sqlite3
import pandas as pd
import streamlit as st
from src.renderer import render_email
from src.mailer import send_email

ROOT = Path(__file__).resolve().parent

st.set_page_config(
    page_title="Email Automation & Reminder Dashboard",
    layout="wide",
    page_icon="✉️",
)

st.title("✉️ Email Automation & Scheduled Reminder Platform")
st.caption("RFC 5545 RRULE Recurrence, Jinja2 Personalization & Delivery Logging")

# Sidebar
with st.sidebar:
    st.header("⚙️ Dispatch Settings")
    st.info("Operating Mode: **Dry-Run Simulation**\n\nNo actual SMTP traffic will be dispatched unless credentials are configured.")
    st.markdown("---")
    st.markdown("### 📊 System Status")
    st.markdown("- **Engine:** Active")
    st.markdown("- **Database:** SQLite 3")
    st.markdown("- **Templating:** Jinja2")

db_path = ROOT / "db" / "email.db"
contacts_csv = ROOT / "data" / "contacts.csv"
reminders_csv = ROOT / "data" / "reminders.csv"

contacts_df = pd.read_csv(contacts_csv) if contacts_csv.exists() else pd.DataFrame()
reminders_df = pd.read_csv(reminders_csv) if reminders_csv.exists() else pd.DataFrame()

# Top KPIs
col1, col2, col3, col4 = st.columns(4)
total_contacts = len(contacts_df)
opted_out = int((contacts_df["unsubscribed"].astype(str).str.lower() == "true").sum()) if not contacts_df.empty else 0
active_contacts = total_contacts - opted_out
total_reminders = len(reminders_df)

col1.metric("Total Contacts", total_contacts)
col2.metric("Active Recipients", active_contacts)
col3.metric("Opted Out", opted_out, delta=f"-{(opted_out/max(1, total_contacts)*100):.0f}%" if total_contacts else "0")
col4.metric("Active Schedules", total_reminders)

st.markdown("---")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Delivery Logs", 
    "👥 Contacts Directory", 
    "⏰ Recurring Reminders", 
    "📝 Template Previewer",
    "🚀 Test Dispatcher"
])

with tab1:
    st.subheader("Message Delivery Logs & Audit Trail")
    if db_path.exists():
        conn = sqlite3.connect(str(db_path))
        logs_df = pd.read_sql_query("SELECT id, reminder_id, recipient_name, recipient_email, subject, status, error_detail, timestamp FROM message_logs ORDER BY id DESC", conn)
        conn.close()
        if not logs_df.empty:
            st.dataframe(logs_df, use_container_width=True)
            
            # Status summary
            status_counts = logs_df["status"].value_counts()
            st.bar_chart(status_counts)
        else:
            st.info("No message logs found yet. Run `python main.py` to trigger email dispatch.")
    else:
        st.info("Database not initialized yet.")

with tab2:
    st.subheader("Audience Directory & Preferences")
    if not contacts_df.empty:
        st.dataframe(contacts_df, use_container_width=True)

with tab3:
    st.subheader("Configured Reminder Schedules")
    if not reminders_df.empty:
        st.dataframe(reminders_df, use_container_width=True)

with tab4:
    st.subheader("Personalized Email Preview")
    templates_dir = ROOT / "templates"
    if templates_dir.exists():
        templates = [p.name for p in templates_dir.glob("*.html")]
        selected_template = st.selectbox("Select Template", templates)
        
        c_a, c_b = st.columns(2)
        with c_a:
            p_name = st.text_input("Recipient Name", "Rohit Singh")
            p_title = st.text_input("Task / Event Title", "Project Final Review")
        with c_b:
            p_time = st.text_input("Event Timestamp", "2026-11-20 18:30:00")
            p_tz = st.text_input("Timezone", "Asia/Kolkata")
        
        rendered_html = render_email(
            templates_dir,
            selected_template,
            {"name": p_name, "title": p_title, "scheduled_time": p_time, "timezone": p_tz},
        )
        st.markdown("**Rendered HTML:**")
        st.components.v1.html(rendered_html, height=280, scrolling=True)

with tab5:
    st.subheader("Direct Dispatch Simulator (Dry-Run)")
    st.write("Simulate sending a notification to test error handling and delivery tracking.")
    test_email = st.text_input("Recipient Email", "candidate@testdomain.com")
    test_subject = st.text_input("Email Subject", "Test Notification: Automation System Ready")
    
    if st.button("🚀 Trigger Test Send"):
        status, err = send_email(test_email, test_subject, "<p>This is a simulated verification test.</p>", dry_run=True)
        if status == "sent (dry-run)":
            st.success(f"Successfully simulated dispatch to {test_email}! Status: {status}")
        else:
            st.error(f"Failed to dispatch: {err}")
