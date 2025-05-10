import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock

from contacts import Contacts, ContactData

class TestContacts(unittest.TestCase):
    """Test suite for the Contacts class."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create a temporary file for state management
        self.temp_file = tempfile.NamedTemporaryFile(delete=False)
        self.temp_file_path = self.temp_file.name
        self.temp_file.close()
        
        # Create a Contacts instance with the temporary file
        self.contacts = Contacts(self.temp_file_path)
        
        # Create some sample contacts for testing
        self.contacts.add_contact(
            first_name="John",
            last_name="Doe",
            title="Software Engineer",
            company="TechCorp",
            work_phone="123-456-7890",
            mobile_phone="+1-987-654-3210",
            email="john.doe@example.com"
        )
        
        self.contacts.add_contact(
            first_name="Jane",
            last_name="Smith",
            title="Product Manager",
            company="ProductCo",
            work_phone="555-123-4567",
            mobile_phone="+1-555-987-6543",
            email="jane.smith@example.com"
        )
        
        self.contacts.add_contact(
            first_name="Robert",
            last_name="Johnson",
            title="DevOps Engineer",
            company="TechCorp",
            work_phone="555-987-6543",
            home_phone="555-000-1111",
            email="robert.johnson@example.com"
        )
    
    def tearDown(self):
        """Tear down test fixtures after each test method."""
        if os.path.exists(self.temp_file_path):
            os.remove(self.temp_file_path)
    
    def test_validate_item_valid_data(self):
        """Test validation of contact data with valid input."""
        valid_item = {
            "first_name": "Test",
            "last_name": "Contact",
            "email": "test@example.com",
            "work_phone": "123-456-7890",
            "mobile_phone": "+1-987-654-3210"
        }
        self.assertTrue(self.contacts._validate_item(valid_item))
    
    def test_validate_item_missing_first_name(self):
        """Test validation of contact data with missing first name."""
        invalid_item = {
            "last_name": "Contact",
            "email": "test@example.com"
        }
        with self.assertRaises(ValueError) as context:
            self.contacts._validate_item(invalid_item)
        self.assertEqual(str(context.exception), "Missing required field: first_name")
    
    def test_validate_item_missing_last_name(self):
        """Test validation of contact data with missing last name."""
        invalid_item = {
            "first_name": "Test",
            "email": "test@example.com"
        }
        with self.assertRaises(ValueError) as context:
            self.contacts._validate_item(invalid_item)
        self.assertEqual(str(context.exception), "Missing required field: last_name")
    
    def test_validate_item_invalid_email_format(self):
        """Test validation of contact data with invalid email format."""
        invalid_item = {
            "first_name": "Test",
            "last_name": "Contact",
            "email": "not-an-email"
        }
        with self.assertRaises(ValueError) as context:
            self.contacts._validate_item(invalid_item)
        self.assertEqual(str(context.exception), "Invalid email format")
    
    def test_validate_item_invalid_phone_format(self):
        """Test validation of contact data with invalid phone number format."""
        # Test with invalid work phone
        invalid_item = {
            "first_name": "Test",
            "last_name": "Contact",
            "work_phone": "not-a-phone"
        }
        with self.assertRaises(ValueError) as context:
            self.contacts._validate_item(invalid_item)
        self.assertEqual(str(context.exception), "Invalid phone number format in work_phone")
        
        # Test with invalid mobile phone
        invalid_item = {
            "first_name": "Test",
            "last_name": "Contact",
            "mobile_phone": "abc-def-ghij"
        }
        with self.assertRaises(ValueError) as context:
            self.contacts._validate_item(invalid_item)
        self.assertEqual(str(context.exception), "Invalid phone number format in mobile_phone")
    
    def test_add_contact_basic(self):
        """Test adding a basic contact."""
        result = self.contacts.add_contact(
            first_name="New",
            last_name="Contact"
        )
        self.assertIn("added", result.lower())
        
        # Verify contact was added correctly
        contacts = self.contacts.list_contacts()
        self.assertEqual(len(contacts), 4)  # 3 from setUp + 1 new one
        self.assertEqual(contacts[4]["first_name"], "New")
    
    def test_add_contact_with_custom_id(self):
        """Test adding a contact with a custom ID."""
        result = self.contacts.add_contact(
            first_name="Custom",
            last_name="ID",
            email="custom@example.com",
            contact_id=100
        )
        self.assertIn("added", result.lower())
        
        # Verify contact has correct ID
        contact = self.contacts.get_contact(100)
        self.assertIsNotNone(contact)
        self.assertEqual(contact["first_name"], "Custom")
        self.assertEqual(contact["last_name"], "ID")
    
    def test_add_contact_duplicate_id_fails(self):
        """Test that adding a contact with an existing ID fails."""
        with self.assertRaises(ValueError):
            self.contacts.add_contact(first_name="Duplicate", last_name="ID", contact_id=1)
    
    def test_add_contact_invalid_email_fails(self):
        """Test that adding a contact with invalid email format fails."""
        with self.assertRaises(ValueError):
            self.contacts.add_contact(
                first_name="Bad",
                last_name="Email",
                email="not-an-email"
            )
    
    def test_add_contact_invalid_phone_fails(self):
        """Test that adding a contact with invalid phone format fails."""
        with self.assertRaises(ValueError):
            self.contacts.add_contact(
                first_name="Bad",
                last_name="Phone",
                mobile_phone="abc-def"  # Invalid phone format
            )
    
    def test_update_contact_basic(self):
        """Test updating a contact with basic fields."""
        result = self.contacts.update_contact(1, first_name="Jonathan")
        self.assertIn("updated", result.lower())
        
        # Verify update was applied
        contact = self.contacts.get_contact(1)
        self.assertEqual(contact["first_name"], "Jonathan")
        self.assertEqual(contact["last_name"], "Doe")  # Unchanged
    
    def test_update_contact_nonexistent_id_fails(self):
        """Test that updating a nonexistent contact fails."""
        with self.assertRaises(ValueError):
            self.contacts.update_contact(999, first_name="Should Fail")
    
    def test_update_contact_invalid_email_fails(self):
        """Test that updating a contact with invalid email format fails."""
        with self.assertRaises(ValueError):
            self.contacts.update_contact(1, email="not-an-email")
    
    def test_update_contact_invalid_phone_fails(self):
        """Test that updating a contact with invalid phone format fails."""
        with self.assertRaises(ValueError):
            self.contacts.update_contact(1, mobile_phone="abc-def")  # Invalid format
    
    def test_delete_contact(self):
        """Test deleting a contact."""
        result = self.contacts.delete_contact(1)
        self.assertIn("deleted", result.lower())
        
        # Verify contact was deleted
        self.assertIsNone(self.contacts.get_contact(1))
    
    def test_delete_nonexistent_contact_fails(self):
        """Test that deleting a nonexistent contact fails."""
        with self.assertRaises(ValueError):
            self.contacts.delete_contact(999)
    
    def test_search_contacts_by_name(self):
        """Test searching contacts by name."""
        results = self.contacts.search_contacts("John")
        self.assertEqual(len(results), 2)   # John Smith and Robert Johnson
        expected_ids = {1, 3}
        actual_ids = {contact["item_id"] for contact in results}
        self.assertEqual(actual_ids, expected_ids)
    
    def test_search_contacts_by_company(self):
        """Test searching contacts by company."""
        results = self.contacts.search_contacts("TechCorp")
        self.assertEqual(len(results), 2)  # Should find John and Robert
    
    def test_search_contacts_by_phone(self):
        """Test searching contacts by phone number."""
        results = self.contacts.search_contacts("987")
        # Should find all 3 (All have 987 in their phone numbers)
        self.assertEqual(len(results), 3)
    
    def test_search_contacts_case_insensitive(self):
        """Test that search is case insensitive."""
        results = self.contacts.search_contacts("jane")  # Lowercase
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["first_name"], "Jane")
    
    def test_list_contacts(self):
        """Test listing all contacts."""
        all_contacts = self.contacts.list_contacts()
        # Should have 3 contacts from setUp
        self.assertEqual(len(all_contacts), 3)
        
        # Verify contact IDs exist
        self.assertIn(1, all_contacts)
        self.assertIn(2, all_contacts)
        self.assertIn(3, all_contacts)
    
    def test_get_contact(self):
        """Test getting a specific contact."""
        contact = self.contacts.get_contact(1)
        self.assertIsNotNone(contact)
        self.assertEqual(contact["first_name"], "John")
        self.assertEqual(contact["last_name"], "Doe")
    
    def test_get_nonexistent_contact(self):
        """Test getting a contact with a nonexistent ID returns None."""
        contact = self.contacts.get_contact(999)
        self.assertIsNone(contact)


if __name__ == "__main__":
    unittest.main()
