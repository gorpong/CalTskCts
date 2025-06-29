import csv
import re
from pathlib import Path

import pytest

from caltskcts.import_export import (
    export_contacts_csv,
    import_contacts_csv,
    export_events_ics,
    import_events_ics,
    export_tasks_csv,
    import_tasks_csv,
    _extract_id,
)
from caltskcts.contacts import Contacts
from caltskcts.calendars import Calendar
from caltskcts.tasks import Tasks
from caltskcts.schemas import ContactModel, EventModel, TaskModel

def sqlite_uri(path: Path) -> str:
    """Helper to build a file-backed SQLite URI."""
    return f"sqlite:///{path}"

def test_contacts_csv_roundtrip(tmp_path):
    db1 = tmp_path / "c1.db"
    db2 = tmp_path / "c2.db"
    uri1 = sqlite_uri(db1)
    uri2 = sqlite_uri(db2)

    # Add one contact to the first DB
    mgr1 = Contacts(uri1)
    msg = mgr1.add_contact(first_name="Alice", last_name="Smith", email="alice@example.com")
    assert isinstance(msg, str) and "added" in msg.lower()
    cid = _extract_id(msg)
    assert cid == 1

    # Export to CSV
    csv_path = tmp_path / "contacts.csv"
    export_contacts_csv(uri1, csv_path)

    # Check CSV header against ContactModel fields
    with csv_path.open(newline="") as f:
        reader = csv.reader(f)
        header = next(reader)
    expected = ["id"] + list(ContactModel.model_fields.keys())
    assert header == expected

    # Import into second, empty DB
    imported = import_contacts_csv(uri2, csv_path)
    assert imported == [1]

    # Verify data round‐tripped correctly
    mgr2 = Contacts(uri2)
    items = mgr2.list_items()
    assert 1 in items
    rec = items[1]
    assert rec["first_name"] == "Alice"
    assert rec["last_name"]  == "Smith"
    assert rec["email"]      == "alice@example.com"

def test_contacts_import_bad_header(tmp_path):
    bad = tmp_path / "bad_contacts.csv"
    bad.write_text("foo,bar,baz\n1,Alice\n")
    with pytest.raises(ValueError):
        import_contacts_csv("sqlite:///:memory:", bad)

def test_events_ics_roundtrip(tmp_path):
    db1 = tmp_path / "e1.db"
    db2 = tmp_path / "e2.db"
    uri1 = sqlite_uri(db1)
    uri2 = sqlite_uri(db2)

    # Add one event
    cal1 = Calendar(uri1)
    msg = cal1.add_event(
        title="Meeting",
        date="06/15/2025 09:00",
        duration=45,
        users=["Bob", "Carol"],
    )
    assert isinstance(msg, str)
    eid = _extract_id(msg)
    assert eid == 1

    # Export to ICS
    ics_path = tmp_path / "events.ics"
    export_events_ics(uri1, ics_path)

    # Import into fresh DB
    imported = import_events_ics(uri2, ics_path)
    assert imported == [1]

    # Verify data
    cal2 = Calendar(uri2)
    items = cal2.list_items()
    assert 1 in items
    ev = items[1]
    assert ev["title"]    == "Meeting"
    assert ev["date"]     == "06/15/2025 09:00"
    assert ev["duration"] == 45
    assert ev["users"]    == ["Bob", "Carol"]

def test_events_import_empty_ics(tmp_path):
    empty = tmp_path / "empty.ics"
    empty.write_bytes(b"")
    # Should not error, but return empty list
    result = import_events_ics("sqlite:///:memory:", empty)
    assert result == []

def test_tasks_csv_roundtrip(tmp_path):
    db1 = tmp_path / "t1.db"
    db2 = tmp_path / "t2.db"
    uri1 = sqlite_uri(db1)
    uri2 = sqlite_uri(db2)

    # Add one task
    t1 = Tasks(uri1)
    msg = t1.add_task(
        title="Task1",
        description="Do X",
        due_date="06/20/2025",
        progress=10.0,
        state="Not Started",
    )
    assert isinstance(msg, str)
    tid = _extract_id(msg)
    assert tid == 1

    # Export to CSV
    csv_path = tmp_path / "tasks.csv"
    export_tasks_csv(uri1, csv_path)

    # Check header against TaskModel fields
    text = csv_path.read_text().splitlines()
    header = text[0].split(",")
    expected = ["id"] + list(TaskModel.model_fields.keys())
    assert header == expected

    # Import into fresh DB
    imported = import_tasks_csv(uri2, csv_path)
    assert imported == [1]

    # Verify data
    t2 = Tasks(uri2)
    items = t2.list_items()
    assert 1 in items
    task = items[1]
    assert task["title"]    == "Task1"
    assert task["desc"]     == "Do X"
    assert task["dueDate"]  == "06/20/2025"
    assert task["progress"] == 10.0
    assert task["state"]    == "Not Started"

def test_tasks_import_bad_header(tmp_path):
    bad = tmp_path / "bad_tasks.csv"
    bad.write_text("x,y,z\n")
    with pytest.raises(ValueError):
        import_tasks_csv("sqlite:///:memory:", bad)
