"""Interactive Streamlit dashboard for Email Automation & Reminder System."""
from pathlib import Path
import sqlite3
import pandas as pd
import streamlit as st
from src.renderer import render_email

ROOT = Path(__file__).resolve().parent
st.set_page_config(page_title="Email Automation & Reminder System", layout="wide", page_icon="✉️")
st.title("✉️ Email Automation & Reminder System")

# Overview Metrics
db_path = ROOT / "db" / "email.db"
contacts_csv = ROOT / "data" / "contacts.csv"
reminders_csv = ROOT / "data" / "reminders.csv"

contacts_df = pd.read_csv(contacts_csv) if contacts_csv.exists() else pd.DataFrame()
reminders_df = pd.read_csv(reminders_csv) if reminders_csv.exists() else pd.DataFrame()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Contacts", len(contacts_df))
opted_out = int((contacts_df["unsubscribed"].astype(str).str.lower() == "true").sum()) if not contacts_df.empty else 0
col2.metric("Opted Out", opted_out)
col3.metric("Active Contacts", len(contacts_df) - opted_out)
col4.metric("Configured Reminders", len(reminders_df))

st.markdown("---")
tab1, tab2, tab3, tab4 = st.tabs(["📊 Dispatch Logs", "👥 Contacts", "⏰ Reminders", "📝 Template Preview"])

with tab1:
    st.subheader("Message Delivery Logs")
    if db_path.exists():
        conn = sqlite3.connect(str(db_path))
        logs_df = pd.read_sql_query("SELECT id, reminder_id, recipient_name, recipient_email, subject, status, error_detail, timestamp FROM message_logs ORDER BY id DESC", conn)
        conn.close()
        if not logs_df.empty:
            st.dataframe(logs_df, use_container_width=True)
        else:
            st.info("No message logs found yet. Run `python main.py` to trigger email dispatch.")
    else:
        st.info("Database not found. Run `python main.py` first.")

with tab2:
    st.subheader("Subscribed & Opted-out Contacts")
    if not contacts_df.empty:
        st.dataframe(contacts_df, use_container_width=True)

with tab3:
    st.subheader("Configured Reminder Schedules")
    if not reminders_df.empty:
        st.dataframe(reminders_df, use_container_width=True)

with tab4:
    st.subheader("Preview Personalized Email Templates")
    templates_dir = ROOT / "templates"
    if templates_dir.exists():
        templates = [p.name for p in templates_dir.glob("*.html")]
        selected_template = st.selectbox("Select Template", templates)
        preview_name = st.text_input("Candidate / Recipient Name", "Aarav Sharma")
        preview_title = st.text_input("Event / Task Title", "Project Review Sync")
        preview_time = st.text_input("Scheduled Time", "2026-11-20 19:00:00")
        
        rendered_html = render_email(
            templates_dir,
            selected_template,
            {"name": preview_name, "title": preview_title, "scheduled_time": preview_time, "timezone": "Asia/Kolkata"},
        )
        st.markdown("**Rendered Output Preview:**")
        st.components.v1.html(rendered_html, height=300, scrolling=True)

