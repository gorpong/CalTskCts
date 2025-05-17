# tests/test_contacts_db_with_mocks.py

import unittest
from unittest.mock import patch

from caltskcts.contacts import Contacts, ContactData
from caltskcts.state_manager import StateManagerBase

class TestContactsDBWithMocks(unittest.TestCase):
    """Exercise the DB-backend path of Contacts, mocking out the actual SQL calls."""

    def setUp(self):
        # Use an in-memory SQLite URI so that __init__ picks the DB path
        self.db_uri = "sqlite:///:memory:"

        # Sample contact payload
        self.sample: ContactData = {
            "first_name": "Alice",
            "last_name": "Wonderland",
            "title": "Tester",
            "company": "QA Inc.",
            "work_phone": "555-1234",
            "mobile_phone": "+1-800-999-8888",
            "home_phone": None,
            "email": "alice@example.com",
        }

    @patch.object(StateManagerBase, "_load_state_db", return_value={})
    @patch.object(StateManagerBase, "_save_one_db")
    def test_add_contact_calls_save_one_db(self, mock_save_one, mock_load_db):
        c = Contacts(self.db_uri)
        # add_item should return True and call _save_one_db exactly once
        added = c.add_contact(**self.sample, contact_id=42)
        self.assertTrue(added)
        mock_save_one.assert_called_once_with(42, self.sample)

    @patch.object(StateManagerBase, "_load_state_db")
    @patch.object(StateManagerBase, "_save_one_db")
    def test_update_contact_calls_save_one_db(self, mock_save_one, mock_load_db):
        # pre-load one existing contact ID=7
        original = { "7": dict(self.sample) }
        mock_load_db.return_value = original
        c = Contacts(self.db_uri)

        # update phone number
        new_phone = "000-111-2222"
        updated = c.update_contact(7, work_phone=new_phone)
        self.assertTrue(updated)

        # Expect _save_one_db called with merged payload
        expected = dict(self.sample)
        expected["work_phone"] = new_phone
        mock_save_one.assert_called_once_with(7, expected)

    @patch.object(StateManagerBase, "_load_state_db")
    @patch.object(StateManagerBase, "_delete_one_db")
    def test_delete_contact_calls_delete_one_db(self, mock_delete_one, mock_load_db):
        # pre-load two contacts
        mock_load_db.return_value = { "5": self.sample, "6": self.sample }
        c = Contacts(self.db_uri)

        deleted = c.delete_contact(5)
        self.assertTrue(deleted)
        mock_delete_one.assert_called_once_with(5)

    @patch.object(StateManagerBase, "_load_state_db", return_value={})
    @patch.object(StateManagerBase, "_save_one_db")
    def test_add_duplicate_id_raises_value_error(self, mock_save_one, mock_load_db):
        # Simulate that ID 100 already exists in DB
        mock_load_db.return_value = { "100": self.sample }
        c = Contacts(self.db_uri)
        with self.assertRaises(ValueError):
            # add_contact will detect duplicate and raise
            c.add_contact(**self.sample, contact_id=100)

if __name__ == "__main__":
    unittest.main()
