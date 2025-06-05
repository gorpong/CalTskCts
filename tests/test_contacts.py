import os
import tempfile
import unittest
from unittest.mock import patch

from caltskcts.contacts import Contacts

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
        msg = str(context.exception)
        self.assertIn("first_name", msg)
        self.assertIn("Field required", msg)
    
    def test_validate_item_missing_last_name(self):
        """Test validation of contact data with missing last name."""
        invalid_item = {
            "first_name": "Test",
            "email": "test@example.com"
        }
        with self.assertRaises(ValueError) as context:
            self.contacts._validate_item(invalid_item)
        msg = str(context.exception)
        self.assertIn("last_name", msg)
        self.assertIn("Field required", msg)
    
    def test_validate_item_invalid_email_format(self):
        """Test validation of contact data with invalid email format."""
        invalid_item = {
            "first_name": "Test",
            "last_name": "Contact",
            "email": "not-an-email"
        }
        with self.assertRaises(ValueError) as context:
            self.contacts._validate_item(invalid_item)
        msg = str(context.exception)
        self.assertIn("email", msg)
        self.assertIn("pattern", msg)
    
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
        msg = str(context.exception)
        self.assertIn("work_phone", msg)
        self.assertIn("phone", msg)
        
        # Test with invalid mobile phone
        invalid_item = {
            "first_name": "Test",
            "last_name": "Contact",
            "mobile_phone": "abc-def-ghij"
        }
        with self.assertRaises(ValueError) as context:
            self.contacts._validate_item(invalid_item)
        msg = str(context.exception)
        self.assertIn("mobile_phone", msg)
        self.assertIn("phone", msg)
    
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

    def test_special_characters_in_names(self):
        """Test handling of special characters in names."""
        special_name_cases = [
            # Normal names - should pass
            ("John", "Doe", True),
            
            # Special characters in first name
            ("John-Paul", "Doe", True),
            ("O'Connor", "Smith", True),
            ("Jean-Claude", "Van Damme", True),
            ("María", "González", True),  # Unicode characters
            ("Wang", "Xiao-Ming", True),
            
            # Special characters that might cause issues
            # These should pass as there are no validation rules for special chars
            ("Bobby Tables; DROP TABLE users;", "Doe", True),
            ("Alice<script>alert('XSS')</script>", "Smith", True),
            ("Test with spaces", "Smith", True),
            
            # Empty strings - should fail
            ("", "Doe", False),
            ("John", "", False),
        ]
        
        for first_name, last_name, should_pass in special_name_cases:
            with self.subTest(first_name=first_name, last_name=last_name):
                contact_data = {
                    "first_name": first_name, 
                    "last_name": last_name
                }
                if should_pass:
                    try:
                        result = self.contacts._validate_item(contact_data)
                        self.assertTrue(result)
                    except ValueError as e:
                        self.fail(f"Validation failed for '{first_name} {last_name}': {str(e)}")
                else:
                    with self.assertRaises(ValueError):
                        self.contacts._validate_item(contact_data)
    
    def test_unusual_email_formats(self):
        """Test validation of unusual but technically valid email formats."""
        unusual_emails = [
            # Standard formats
            ("user@example.com", True),
            ("user.name@example.com", True),
            ("user+tag@example.com", True),
            
            # Less common but valid formats
            ("user.name+tag@example.co.uk", True),
            ("user-name@example.com", True),
            ("user_name@example.com", True),
            
            # Edge cases that are still valid
            ('"very.unusual.\"@\".unusual.com"@example.com', True),  # Hard to read but valid
            ('"very.(),:;<>[]\\\".VERY.\"very@\\ \"very\".unusual"@strange.example.com', True),  # Complex
            ('"customer/department=shipping"@example.com', True),  # Uses special characters
            
            # Invalid formats - These SHOULD FAIL, but Contacts._validate_item() is broken
            ("not-an-email", False),
            ("@missingusername.com", False),
            ("missing-domain@", False),
            ("spaces in@example.com", False),
            ("duplicate@example@com", False),
        ]
        
        for email, is_valid in unusual_emails:
            with self.subTest(email=email):
                contact_data = {
                    "first_name": "Test", 
                    "last_name": "Contact", 
                    "email": email
                }
                if is_valid:
                    try:
                        result = self.contacts._validate_item(contact_data)
                        self.assertTrue(result)
                    except ValueError as e:
                        self.fail(f"Validation failed for '{email}': {str(e)}")
                else:
                    with self.assertRaises(ValueError):
                        self.contacts._validate_item(contact_data)
    
    def test_various_phone_formats_with_cleaning(self):
        """Test different phone formats that get cleaned during validation."""
        test_formats = [
            # Standard formats with cleaning
            ("123-456-7890", "1234567890"),
            ("(123) 456-7890", "1234567890"),
            ("+1-123-456-7890", "+11234567890"),
            ("123.456.7890", "1234567890"),
            ("123 456 7890", "1234567890"),
            
            # Edge cases - all invalid
            ("+", None),               # Just the + symbol, not valid
            ("+1", None),              # + with one digit
            ("abcd", None),            # Only invalid chars are invalid
            ("123+456", None),         # Valid with + in the middle
            
            # Invalid formats - these should fail validation
            ("abc-def-ghij", None),    # All letters
            ("123-abc-def0", None),    # Mixed letters and digits
            ("123_456_7890", None),    # Using underscore instead of hyphen
            
            # Boundary cases
            ("0", None),                # Single digit, needs 7-15
            ("0000000000", "0000000000"),  # Many zeros, can't really catch
            ("9" * 20, None),           # Very long number, > 15
        ]
        
        for input_format, expected_result in test_formats:
            with self.subTest(input_format=input_format):
                contact_data = {
                    "first_name": "Phone", 
                    "last_name": "Test", 
                    "work_phone": input_format
                }
                
                if expected_result is not None:
                    try:
                        self.contacts._validate_item(contact_data)
                        # If we get here, validation didn't raise an exception
                        # We could check the stored value, but that would require access
                        # to implementation details not exposed in the interface
                    except ValueError as e:
                        self.fail(f"Validation failed for '{input_format}': {str(e)}")
                else:
                    with self.assertRaises(ValueError):
                        self.contacts._validate_item(contact_data)
    
    def test_search_with_boundary_cases(self):
        """Test search functionality with boundary cases."""
        # Set up test data with various edge cases
        self.contacts._state = {
            "1": {"first_name": "John", "last_name": "Doe", "email": "john@example.com", "company": "TechCorp"},
            "2": {"first_name": "jane", "last_name": "smith", "email": "jane@example.com", "company": "productco"},
            "3": {"first_name": "ROBERT", "last_name": "JOHNSON", "email": "robert@EXAMPLE.com", "company": "TECHCORP"},
            "4": {"first_name": "Empty", "last_name": "Fields", "email": "", "home_phone": ""},
        }
        
        # Case sensitivity - should be case insensitive
        results = self.contacts.search_contacts("JOHN")
        self.assertEqual(len(results), 2) # Both John Doe and ROBERT JOHNSON
        results = self.contacts.search_contacts("john")
        self.assertEqual(len(results), 2)
        
        # Should find lowercase field values with uppercase search
        results = self.contacts.search_contacts("TECHCORP")
        self.assertEqual(len(results), 2)  # Should find Robert and John
        
        # Partial matching
        results = self.contacts.search_contacts("jo")  # Should match John and Robert
        self.assertEqual(len(results), 2)
        
        # Empty field handling - should not match empty fields
        results = self.contacts.search_contacts("")
        self.assertEqual(len(results), 4)  # Should find all contacts
        
    def test_regex_special_characters_in_search(self):
        """Test search with regex special characters."""
        self.contacts._state = {
            "1": {"first_name": "Special", "last_name": "Chars", "work_phone": "123-456-7890"},
            "2": {"first_name": "Regular", "last_name": "Contact", "work_phone": "(999) 888-7777"},
        }
        
        # Test with regex special characters
        results = self.contacts.search_contacts("\\d")  # Should match all digits
        self.assertEqual(len(results), 2)
        
        # Test with dot character which matches any character
        results = self.contacts.search_contacts(".")
        self.assertEqual(len(results), 2)
        
        # Test with character class
        results = self.contacts.search_contacts("[SsR]")  # Should match S or s or R
        self.assertEqual(len(results), 2)
        
        # Test with invalid regex pattern
        with self.assertRaises(ValueError) as context:
            self.contacts.search_contacts("[")  # Unclosed character class
        self.assertTrue("Invalid regex pattern" in str(context.exception))
    
    def test_field_with_and_without_values(self):
        """Test validation and operation with fields having different presence states."""
        # Test contact with only required fields
        self.contacts._validate_item({
            "first_name": "Minimal", 
            "last_name": "Contact"
        })
        
        # Test contact with all fields filled
        self.contacts._validate_item({
            "first_name": "Full", 
            "last_name": "Information",
            "title": "Developer",
            "company": "Example Inc.",
            "work_phone": "123-456-7890",
            "mobile_phone": "+1-987-654-3210",
            "home_phone": "555-123-4567",
            "email": "full@example.com"
        })
        
        # Test with None values for optional fields
        # In the implementation, None values are filtered out before validation
        # So this test is more about how the update process might handle None values
        with patch.object(self.contacts, 'get_item', return_value={
            "first_name": "Original", 
            "last_name": "Contact",
            "title": "Original Title",
            "company": "Original Company"
        }):
            with patch.object(self.contacts, 'update_item', return_value=True):
                # This should work because None values are filtered out
                self.contacts.update_contact(1, title=None, company=None)

if __name__ == "__main__":
    unittest.main()
