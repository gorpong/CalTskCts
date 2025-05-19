import unittest
from unittest.mock import patch

from caltskcts.contacts import Contacts

class TestContactsWithMocks(unittest.TestCase):
    """Test suite for the Contacts class using mocks to isolate from file system."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Use patch to mock the file operations
        self.state_file_patcher = patch('caltskcts.contacts.StateManagerBase._load_state')
        self.mock_load_state = self.state_file_patcher.start()
        
        # Mock the _save_state method to prevent actual file writes
        self.save_state_patcher = patch('caltskcts.contacts.StateManagerBase._save_state')
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
    
    def test_add_contact_with_mocked_state(self):
        """Test adding a contact when state is mocked."""
        # Mock add_item to return True (successful add)
        with patch.object(self.contacts, 'add_item', return_value=True):
            result = self.contacts.add_contact(
                first_name="Mocked",
                last_name="Contact",
                email="mocked@example.com"
            )
            self.assertIn("added", result.lower())
    
    def test_add_contact_duplicate_id_with_mock(self):
        """Test that adding a contact with an existing ID fails when using mock."""
        # Mock add_item to return False (ID already exists)
        with patch.object(self.contacts, 'add_item', return_value=False):
            with self.assertRaises(ValueError):
                self.contacts.add_contact(
                    first_name="Duplicate",
                    last_name="ID",
                    contact_id=1
                )
    
    def test_add_contact_validation_edge_cases(self):
        """Test edge cases for contact validation during add."""
        edge_cases = [
            # No first_name (should fail)
            ({"last_name": "Contact"}, ValueError),
            
            # No last_name (should fail)
            ({"first_name": "Test"}, ValueError),
            
            # Extremely long names (should pass validation as there's no length limit)
            ({"first_name": "X" * 1000, "last_name": "Y" * 1000}, None),
            
            # Special characters in names (should pass)
            ({"first_name": "Test With !@#", "last_name": "Special-Characters"}, None),
            
            # Valid email formats
            ({"first_name": "Email", "last_name": "Test", "email": "user@example.com"}, None),
            ({"first_name": "Email", "last_name": "Test", "email": "user.name+tag@example.co.uk"}, None),
            
            # Invalid email formats
            ({"first_name": "Email", "last_name": "Test", "email": "not-an-email"}, ValueError),
            ({"first_name": "Email", "last_name": "Test", "email": "@missing-username.com"}, ValueError),
            ({"first_name": "Email", "last_name": "Test", "email": "missing-domain@"}, ValueError),

            # Valid phone formats with cleaning
            ({"first_name": "Phone", "last_name": "Test", "work_phone": "123-456-7890"}, None),
            ({"first_name": "Phone", "last_name": "Test", "work_phone": "(123) 456-7890"}, None),
            ({"first_name": "Phone", "last_name": "Test", "work_phone": "+12345678901"}, None),
            
            # Invalid phone formats
            ({"first_name": "Phone", "last_name": "Test", "work_phone": "12345"}, ValueError),
            ({"first_name": "Phone", "last_name": "Test", "work_phone": "abc-def-ghij"}, ValueError),
            ({"first_name": "Phone", "last_name": "Test", "work_phone": "123-abc-def0"}, ValueError),
        ]
        
        for contact_data, expected_exception in edge_cases:
            with self.subTest(contact_data=contact_data):
                if expected_exception:
                    with self.assertRaises(expected_exception):
                        self.contacts._validate_item(contact_data)
                else:
                    # This should not raise an exception
                    result = self.contacts._validate_item(contact_data)
                    self.assertTrue(result)
    
    def test_update_contact_edge_cases(self):
        """Test edge cases for contact updates."""
        # Mock get_item to return a valid contact
        with patch.object(self.contacts, 'get_item', return_value={
            "first_name": "Original", 
            "last_name": "Contact",
            "email": "original@example.com", 
            "work_phone": "123-456-7890"
        }):
            # Mock update_item to return True (successful update)
            with patch.object(self.contacts, 'update_item', return_value=True):
                # Test partial updates - only one field changes
                self.contacts.update_contact(1, first_name="Updated")
                
                # Test updating with None values (should not change those fields)
                self.contacts.update_contact(1, email=None, work_phone=None)
                
                # Test empty strings
                self.contacts.update_contact(1, title="", company="")
    
    def test_update_contact_invalid_combinations(self):
        """Test updating with combinations that should be validated correctly."""
        # Mock get_item to return a valid contact
        with patch.object(self.contacts, 'get_item', return_value={
            "first_name": "Original", 
            "last_name": "Contact",
            "email": "original@example.com", 
            "work_phone": "123-456-7890"
        }):
            # Mock update_item to return True (successful update)
            with patch.object(self.contacts, 'update_item', return_value=True):
                # Should fail because invalid email format - missing @
                with self.assertRaises(ValueError):
                    self.contacts.update_contact(1, email="not-email")
                
                # Should fail because invalid phone format
                with self.assertRaises(ValueError):
                    self.contacts.update_contact(1, work_phone="abc-def-ghij")
                
                # Should succeed with proper validation
                self.contacts.update_contact(1, email="updated@example.com")
                self.contacts.update_contact(1, work_phone="987-654-3210")

    def test_phone_validation_formats(self):
        """Test various phone format scenarios."""
        test_cases = [
            # Valid formats
            ("123-456-7890", False),  # Standard format with hyphens
            ("(123) 456-7890", False),  # Format with parentheses and space
            ("+1234567890", False),   # International format
            ("1234567890", False),    # Just digits
            
            # Invalid formats - These all PASS, must fix Contacts._validate_item()
            ("abc-def-ghij", True),   # Letters instead of digits
            ("123-abc-def0", True),   # Mixed letters and digits
            ("", False),              # Empty string (will be ignored in validation)
            ("not a phone", True),    # Nonsensical string
            ("1234567", False),       # Just digits, at least 7, should be valid
            ("123-45", True),         # Incomplete format
        ]
        
        for phone_str, should_raise in test_cases:
            with self.subTest(phone_str=phone_str):
                contact_data = {
                    "first_name": "Phone Test", 
                    "last_name": "Contact",
                    "work_phone": phone_str
                }
                if should_raise:
                    with self.assertRaises(ValueError):
                        self.contacts._validate_item(contact_data)
                else:
                    # This should not raise an exception
                    result = self.contacts._validate_item(contact_data)
                    if result is not None:  # Only check if it returns something
                        self.assertTrue(result)
    
    def test_search_contacts_with_mocked_state(self):
        """Test searching contacts with mocked state."""
        # Create mock contacts in the state
        self.contacts._state = {
            1: {"first_name": "John", "last_name": "Doe", "email": "john@example.com", "company": "TechCorp"},
            2: {"first_name": "Jane", "last_name": "Smith", "email": "jane@example.com", "company": "ProductCo"},
            3: {"first_name": "Robert", "last_name": "Johnson", "email": "robert@example.com", "company": "TechCorp"},
            4: {"first_name": "jennifer", "last_name": "williams", "email": "jennifer@example.com", "company": "Design Co"},
        }
        
        # Test search with matching results
        results = self.contacts.search_contacts("john")
        self.assertEqual(len(results), 2)
        expected_ids = {1, 3}
        actual_ids = {contact["item_id"] for contact in results}
        self.assertEqual(actual_ids, expected_ids)
        
        # Test search with multiple matches (case insensitive)
        results = self.contacts.search_contacts("j")  # Should match all 4
        self.assertEqual(len(results), 4)
        
        # Test search with company match
        results = self.contacts.search_contacts("TechCorp")
        self.assertEqual(len(results), 2)  # John and Robert
        
        # Test search with no matches
        results = self.contacts.search_contacts("NonExistentString")
        self.assertEqual(len(results), 0)
        
        # Test empty search query
        results = self.contacts.search_contacts("")
        self.assertEqual(len(results), 4)  # Should return all contacts
        
        # Test regex special characters
        with self.assertRaises(ValueError):
            self.contacts.search_contacts("[")  # Invalid regex pattern
    
    def test_name_validation_comprehensive(self):
        """Test name validation scenarios."""
        # Test missing first_name
        with self.assertRaises(ValueError):
            self.contacts._validate_item({"last_name": "Contact"})
        
        # Test missing last_name
        with self.assertRaises(ValueError):
            self.contacts._validate_item({"first_name": "Test"})
        
        # Test both names present
        contact_data = {
            "first_name": "Test", 
            "last_name": "Contact"
        }
        result = self.contacts._validate_item(contact_data)
        self.assertTrue(result)
        
        # Test with empty string names (should fail validation)
        contact_data = {
            "first_name": "", 
            "last_name": "Contact"
        }
        with self.assertRaises(ValueError):
            self.contacts._validate_item(contact_data)
        
        contact_data = {
            "first_name": "Test", 
            "last_name": ""
        }
        with self.assertRaises(ValueError):
            self.contacts._validate_item(contact_data)


if __name__ == "__main__":
    unittest.main()
