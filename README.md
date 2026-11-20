# Email Automation & Reminder System

A Python automation service that reads contact & reminder CSVs, expands recurring schedules (`RRULE`), personalizes HTML emails with Jinja2, respects opt-out flags, logs deliveries to SQLite and `.log` files, and supports safe dry-run simulation mode.

## Setup & How to Run
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python main.py
python -m unittest discover -s tests -v
```
