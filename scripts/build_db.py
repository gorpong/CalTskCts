# build_db.py
# Script to create a new-style SQLite (or PostgreSQL) database
# from your existing JSON templates (_contacts.json, _calendar.json, _tasks.json).

import json
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import your ORM models and Base metadata
from caltskcts.state_manager import Base
from caltskcts.contacts import ContactData
from caltskcts.calendars import EventData
from caltskcts.tasks import TaskData
from caltskcts.config import DATABASE_URI

# Helper to load JSON file
def load_json(path: str) -> dict:
    with open(path, 'r') as f:
        return json.load(f)

# Parse a datetime string "MM/DD/YYYY HH:MM" into a datetime (for calendar events)
def parse_datetime(dt_str: str) -> datetime:
    return datetime.strptime(dt_str, "%m/%d/%Y %H:%M")

# Parse a date string "MM/DD/YYYY" into a datetime (for tasks without time)
def parse_date(dt_str: str) -> datetime:
    return datetime.strptime(dt_str, "%m/%d/%Y")

# Main loader
def main():
    # 1) Create engine and tables
    engine = create_engine(DATABASE_URI, future=True)
    Session = sessionmaker(bind=engine, future=True)
    Base.metadata.create_all(engine)

    session = Session()
    try:
        # 2) Load Contacts
        contacts = load_json('templates/_contacts.json')
        for key, rec in contacts.items():
            cid = int(key)
            obj = ContactData(id=cid, **rec)
            session.merge(obj)

        # 3) Load Calendars
        calendars = load_json('templates/_calendar.json')
        for key, rec in calendars.items():
            bid = int(key)
            obj = EventData(
                id=bid,
                title=rec['title'],
                date=parse_datetime(rec['date']),  # parse with time
                duration=rec['duration'],
                users=rec['users'],
            )
            session.merge(obj)

        # 4) Load Tasks
        tasks = load_json('templates/_tasks.json')
        for key, rec in tasks.items():
            tid = int(key)
            due = rec.get('dueDate')
            obj = TaskData(
                id=tid,
                title=rec.get('title'),
                desc=rec.get('desc'),
                dueDate=parse_date(due).date() if due else None,  # parse date only
                progress=rec.get('progress'),
                state=rec.get('state'),
            )
            session.merge(obj)

        # 5) Commit all
        session.commit()
        print("Database populated successfully.")
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == '__main__':
    main()
