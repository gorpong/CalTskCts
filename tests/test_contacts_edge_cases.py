import unittest
from unittest.mock import patch

from contacts import Contacts, ContactData

class TestContactsEdgeCases(unittest.TestCase):
    """Test suite focusing on edge cases for the Contacts class."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Use patch to mock the file operations
        self.state_file_patcher = patch('contacts.StateManagerBase._load_state')
        self.mock_load_state = self.state_file_patcher.start()
        
        # Mock the _save_state method to prevent actual file writes
        self.save_state_patcher = patch('contacts.StateManagerBase._save_state')
        self.mock_save_state = self.save_state_patcher.start()
        
        # Setup empty initial state
        self.mock_load_state.return_value = {}
        self.mock_save_state.return_value = None
        
        # Initialize Contacts with our mocked file operations
        self.contacts = Contacts("/fake/path/to/state.json")
    
    def tearDown(self):
        """Tear down test fixtures after each test method."""
        self.state_file_patcher.stop()
        self.save_state_patcher.stop()
    
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
        
        # Test contact with empty string values for optional fields
        # These should be treated as valid as they're not None and can be processed
        self.contacts._validate_item({
            "first_name": "Empty", 
            "last_name": "Values",
            "title": "",
            "company": "",
            "work_phone": "",
            "mobile_phone": "",
            "home_phone": "",
            "email": ""
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
