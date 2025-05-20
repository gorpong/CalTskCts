# tests/test_contacts_db_with_mocks.py

import unittest
from typing import Dict, Any
from unittest.mock import patch

from caltskcts.contacts import Contacts, ContactData
from caltskcts.state_manager import StateManagerBase

class DummySession:
    """Minimal session‐like object for testing."""
    def __init__(self, store: Dict[int, Any] = None):
        self.store = store or {}
        self.added = []
        self.deleted = []
        self.commits = 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        pass

    def add(self, obj):
        self.added.append(obj)

    def commit(self):
        self.commits += 1

    def refresh(self, obj):
        pass

    def get(self, model, item_id):
        return self.store.get(item_id)

    def delete(self, obj):
        self.deleted.append(obj)


class TestContactsDBWithMocks(unittest.TestCase):
    """Exercise the DB‐backend path of Contacts by stubbing out the session."""

    def setUp(self):
        self.db_uri = "sqlite:///:memory:"
        self.sample: Dict[str, Any] = {
            "first_name": "Alice",
            "last_name":  "Wonderland",
            "title":      "Tester",
            "company":    "QA Inc.",
            "work_phone": "555-1234",
            "mobile_phone":"+1-800-999-8888",
            "home_phone": None,
            "email":      "alice@example.com",
        }

    @patch.object(StateManagerBase, "_load_state_db", return_value={})
    def test_add_contact_calls_session_add_and_commit(self, _):
        dummy = DummySession()
        c = Contacts(self.db_uri)
        # overwrite the instance's SessionLocal factory
        c.SessionLocal = lambda: dummy

        msg = c.add_contact(**self.sample, contact_id=42)
        self.assertTrue("added" in msg.lower())

        # Verify exactly one object was added
        self.assertEqual(len(dummy.added), 1)
        inst = dummy.added[0]
        self.assertIsInstance(inst, ContactData)
        self.assertEqual(inst.id, 42)
        for k, v in self.sample.items():
            self.assertEqual(getattr(inst, k), v)

        # commit must have been called once
        self.assertEqual(dummy.commits, 1)

    @patch.object(StateManagerBase, "_load_state_db")
    def test_update_contact_calls_session_commit(self, mock_load_db):
        original = ContactData(id=7, **self.sample)
        mock_load_db.return_value = {7: original}

        dummy = DummySession(store={7: original})
        c = Contacts(self.db_uri)
        c.SessionLocal = lambda: dummy

        msg = c.update_contact(7, work_phone="000-111-2222")
        self.assertTrue("updated" in msg.lower())

        # The original instance was mutated
        self.assertEqual(original.work_phone, "000-111-2222")
        self.assertEqual(dummy.commits, 1)

    @patch.object(StateManagerBase, "_load_state_db")
    def test_delete_contact_calls_session_delete_and_commit(self, mock_load_db):
        inst5 = ContactData(id=5, **self.sample)
        mock_load_db.return_value = {5: inst5}

        dummy = DummySession(store={5: inst5})
        c = Contacts(self.db_uri)
        c.SessionLocal = lambda: dummy

        msg = c.delete_contact(5)
        self.assertTrue("deleted" in msg.lower())

        self.assertEqual(dummy.deleted, [inst5])
        self.assertEqual(dummy.commits, 1)

    @patch.object(StateManagerBase, "_load_state_db", return_value={100: ContactData(id=100, **{})})
    def test_add_duplicate_id_raises_value_error(self, _):
        dummy = DummySession()
        c = Contacts(self.db_uri)
        c.SessionLocal = lambda: dummy

        with self.assertRaises(ValueError):
            c.add_contact(**self.sample, contact_id=100)


if __name__ == "__main__":
    unittest.main()
