# tests/test_db_persistence.py

import os
import tempfile
import unittest

from caltskcts.contacts import Contacts
from caltskcts.calendars import Calendar
from caltskcts.tasks    import Tasks

class TestDBPersistence(unittest.TestCase):
    """Verify that data written to the DB by one manager instance
    is correctly read back by a fresh instance on the same file."""

    def setUp(self):
        # make a real sqlite file
        tf = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tf.close()
        self.db_path = tf.name
        # SQLAlchemy URI for file-based SQLite
        self.db_uri  = f"sqlite:///{self.db_path}"

    def tearDown(self):
        try:
            os.remove(self.db_path)
        except OSError:
            pass

    def test_contacts_roundtrip(self):
        # Step 1: write
        c1 = Contacts(self.db_uri)
        # add two contacts
        c1.add_contact(first_name="Alice", last_name="A", email="a@example.com", contact_id=1)
        c1.add_contact(first_name="Bob",   last_name="B", email="b@example.com", contact_id=2)
        # verify in-memory
        expected = {
            1: {"id": 1, "first_name":"Alice","last_name":"A","title":None,"company":None,
                "work_phone":None,"mobile_phone":None,"home_phone":None,"email":"a@example.com"},
            2: {"id": 2, "first_name":"Bob",  "last_name":"B","title":None,"company":None,
                "work_phone":None,"mobile_phone":None,"home_phone":None,"email":"b@example.com"},
        }
        self.assertEqual(c1.list_contacts(), expected)

        # Step 2: read back in a fresh instance
        c2 = Contacts(self.db_uri)
        self.assertEqual(c2.list_contacts(), expected)

    def test_calendar_roundtrip(self):
        cal1 = Calendar(self.db_uri)
        cal1.add_event(title="Mtg", date="05/01/2025 09:00", duration=30, users=["X"], event_id=10)
        cal1.add_event(title="Call",date="05/02/2025 14:30", duration=45, users=["Y"], event_id=20)

        exp = {
            10: {"id": 10, "title":"Mtg","date":"05/01/2025 09:00","duration":30,"users":["X"]},
            20: {"id": 20, "title":"Call","date":"05/02/2025 14:30","duration":45,"users":["Y"]},
        }
        self.assertEqual(cal1.list_events(), exp)

        cal2 = Calendar(self.db_uri)
        self.assertEqual(cal2.list_events(), exp)

    def test_tasks_roundtrip(self):
        t1 = Tasks(self.db_uri)
        t1.add_task(title="T1", description="D1", due_date="05/10/2025",
                    progress=0, state="Not Started", task_id=5)
        t1.add_task(title="T2", description="D2", due_date="06/01/2025",
                    progress=50, state="In Progress",  task_id=6)

        exp = {
            5: {"id": 5, "title":"T1","desc":"D1","dueDate":"05/10/2025","progress":0,"state":"Not Started"},
            6: {"id": 6, "title":"T2","desc":"D2","dueDate":"06/01/2025","progress":50,"state":"In Progress"},
        }
        self.assertEqual(t1.list_tasks(), exp)

        t2 = Tasks(self.db_uri)
        self.assertEqual(t2.list_tasks(), exp)


if __name__ == "__main__":
    unittest.main()
