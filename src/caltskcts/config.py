import os

def get_database_uri():
    return os.getenv("DATABASE_URI", "sqlite:///./data/app.db")

def get_calendar_uri():
    return os.getenv("CALTSKCTS_CALENDAR_FILE", "_calendar.json")

def get_contacts_uri():
    return os.getenv("CALTSKCTS_CONTACTS_FILE", "_contacts.json")

def get_tasks_uri():
    return os.getenv("CALTSKCTS_TASKS_FILE", "_tasks.json")
