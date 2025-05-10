import os
import tempfile
import unittest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from calendars import Calendar, EventData

class TestCalendar(unittest.TestCase):
    """Test suite for the Calendar class."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create a temporary file for state management
        self.temp_file = tempfile.NamedTemporaryFile(delete=False)
        self.temp_file_path = self.temp_file.name
        self.temp_file.close()
        
        # Create a Calendar instance with the temporary file
        self.calendar = Calendar(self.temp_file_path)
        
        # Create some sample events for testing
        self.calendar.add_event(
            title="Team Meeting",
            date="05/15/2023 09:00",
            duration=60,
            users=["John", "Jane", "Bob"]
        )
        
        self.calendar.add_event(
            title="Client Call",
            date="05/15/2023 14:00",
            duration=30,
            users=["Jane", "Client"]
        )
        
        self.calendar.add_event(
            title="Project Review",
            date="05/20/2023 11:00",
            duration=90,
            users=["John", "Bob", "Manager"]
        )
    
    def tearDown(self):
        """Tear down test fixtures after each test method."""
        if os.path.exists(self.temp_file_path):
            os.remove(self.temp_file_path)
    
    def test_validate_item_valid_data(self):
        """Test validation of event data with valid input."""
        valid_item = {
            "title": "Test Event",
            "date": "12/31/2023 10:00",
            "duration": 60,
            "users": ["User1", "User2"]
        }
        self.assertTrue(self.calendar._validate_item(valid_item))
    
    def test_validate_item_missing_title(self):
        """Test validation of event data with missing title."""
        invalid_item = {
            "date": "12/31/2023 10:00",
            "duration": 60,
            "users": ["User1", "User2"]
        }
        with self.assertRaises(ValueError) as context:
            self.calendar._validate_item(invalid_item)
        self.assertEqual(str(context.exception), "Missing required field: title")
    
    def test_validate_item_invalid_date_format(self):
        """Test validation of event data with invalid date format."""
        invalid_item = {
            "title": "Test Event",
            "date": "2023-12-31 10:00",  # Wrong format
            "duration": 60,
            "users": ["User1", "User2"]
        }
        with self.assertRaises(ValueError) as context:
            self.calendar._validate_item(invalid_item)
        self.assertEqual(str(context.exception), "Invalid date format. Use MM/DD/YYYY HH:MM")
    
    def test_validate_item_invalid_duration(self):
        """Test validation of event data with invalid duration."""
        # Test with negative duration
        invalid_item = {
            "title": "Test Event",
            "date": "12/31/2023 10:00",
            "duration": -30,
            "users": ["User1", "User2"]
        }
        with self.assertRaises(ValueError) as context:
            self.calendar._validate_item(invalid_item)
        self.assertEqual(str(context.exception), "Duration must be a number larger than 1")
        
        # Test with non-integer duration
        invalid_item["duration"] = "60 minutes"
        with self.assertRaises(ValueError) as context:
            self.calendar._validate_item(invalid_item)
        self.assertEqual(str(context.exception), "Duration must be a number")
    
    def test_validate_item_invalid_users(self):
        """Test validation of event data with invalid users list."""
        invalid_item = {
            "title": "Test Event",
            "date": "12/31/2023 10:00",
            "duration": 60,
            "users": "User1, User2"  # String instead of list
        }
        with self.assertRaises(ValueError) as context:
            self._validate_helper(invalid_item)
        self.assertEqual(str(context.exception), "Users must be a list")
    
    def _validate_helper(self, item):
        """Helper function to validate items, with better error handling."""
        return self.calendar._validate_item(item)
    
    def test_add_event_basic(self):
        """Test adding a basic event."""
        result = self.calendar.add_event(
            title="New Event", 
            date="05/25/2023 10:00",
            duration=45,
            users=["Alice", "Bob"]
        )
        self.assertIn("Added", result)
        
        # Verify event was added correctly
        events = self.calendar.list_events()
        self.assertEqual(len(events), 4)  # 3 from setUp + 1 new one
        
        # Retrieve the event and check its properties
        event_id = 4  # Since we already have 3 events from setUp
        event = self.calendar.get_event(event_id)
        self.assertEqual(event["title"], "New Event")
        self.assertEqual(event["date"], "05/25/2023 10:00")
        self.assertEqual(event["duration"], 45)
        self.assertEqual(event["users"], ["Alice", "Bob"])
    
    def test_add_event_with_custom_id(self):
        """Test adding an event with a custom ID."""
        result = self.calendar.add_event(
            title="Custom ID Event",
            date="05/25/2023 15:30",
            duration=60,
            users=["User1"],
            event_id=100
        )
        self.assertIn("Added", result)
        
        # Verify event was added with the custom ID
        event = self.calendar.get_event(100)
        self.assertIsNotNone(event)
        self.assertEqual(event["title"], "Custom ID Event")
    
    def test_add_event_duplicate_id(self):
        """Test adding an event with a duplicate ID raises ValueError."""
        with self.assertRaises(ValueError) as context:
            self.calendar.add_event(
                title="Duplicate ID Event",
                date="05/25/2023 15:30",
                duration=60,
                users=["User1"],
                event_id=1  # ID 1 already exists from setUp
            )
        self.assertIn("already exists", str(context.exception))
    
    def test_update_event_basic(self):
        """Test updating an existing event."""
        # First get the original event
        original_event = self.calendar.get_event(1)
        self.assertEqual(original_event["title"], "Team Meeting")
        
        # Update the event
        result = self.calendar.update_event(
            event_id=1,
            title="Updated Meeting",
            date="05/16/2023 09:30",
            duration=90,
            users=["John", "Jane", "Bob", "Manager"]
        )
        self.assertIn("updated", result.lower())
        
        # Verify the event was updated
        updated_event = self.calendar.get_event(1)
        self.assertEqual(updated_event["title"], "Updated Meeting")
        self.assertEqual(updated_event["date"], "05/16/2023 09:30")
        self.assertEqual(updated_event["duration"], 90)
        self.assertEqual(updated_event["users"], ["John", "Jane", "Bob", "Manager"])
    
    def test_update_event_partial(self):
        """Test partially updating an event."""
        # Update only the title and duration
        result = self.calendar.update_event(
            event_id=2,
            title="Updated Client Call",
            duration=45
        )
        self.assertIn("updated", result.lower())
        
        # Verify only specified fields were updated
        updated_event = self.calendar.get_event(2)
        self.assertEqual(updated_event["title"], "Updated Client Call")
        self.assertEqual(updated_event["duration"], 45)
        self.assertEqual(updated_event["date"], "05/15/2023 14:00")  # Unchanged
        self.assertEqual(updated_event["users"], ["Jane", "Client"])  # Unchanged
    
    def test_update_event_nonexistent(self):
        """Test updating a non-existent event raises ValueError."""
        with self.assertRaises(ValueError) as context:
            self.calendar.update_event(
                event_id=999,
                title="Non-existent Event"
            )
        self.assertIn("does not exist", str(context.exception))
    
    def test_update_event_validation_failure(self):
        """Test updating an event with invalid data raises ValueError."""
        with self.assertRaises(ValueError) as context:
            self.calendar.update_event(
                event_id=1,
                date="invalid-date"
            )
        self.assertEqual(str(context.exception), "Invalid date format. Use MM/DD/YYYY HH:MM")
    
    def test_delete_event(self):
        """Test deleting an event."""
        # Verify the event exists first
        self.assertIsNotNone(self.calendar.get_event(1))
        
        # Delete the event
        result = self.calendar.delete_event(1)
        self.assertIn("deleted", result.lower())
        
        # Verify the event was deleted
        self.assertIsNone(self.calendar.get_event(1))
        events = self.calendar.list_events()
        self.assertEqual(len(events), 2)  # Original 3 - 1 deleted
    
    def test_delete_event_nonexistent(self):
        """Test deleting a non-existent event raises ValueError."""
        with self.assertRaises(ValueError) as context:
            self.calendar.delete_event(999)
        self.assertIn("does not exist", str(context.exception))
    
    def test_get_events_by_date(self):
        """Test retrieving events by date."""
        # Get events on 05/15/2023 (should have 2 events)
        events = self.calendar.get_events_by_date("05/15/2023")
        self.assertEqual(len(events), 2)
        
        # Verify the events are correct
        titles = [event["title"] for event in events]
        self.assertIn("Team Meeting", titles)
        self.assertIn("Client Call", titles)
        
        # Test with date with no events
        empty_events = self.calendar.get_events_by_date("05/16/2023")
        self.assertEqual(len(empty_events), 0)
    
    def test_get_events_between(self):
        """Test retrieving events between two dates."""
        # Get events between 05/14/2023 and 05/16/2023
        events = self.calendar.get_events_between("05/14/2023", "05/16/2023")
        self.assertEqual(len(events), 2)
        
        # Verify the events are correct (excludes Project Review which is on 05/20)
        titles = [event["title"] for event in events]
        self.assertIn("Team Meeting", titles)
        self.assertIn("Client Call", titles)
        
        # Test with more specific times
        events = self.calendar.get_events_between("05/15/2023 13:00", "05/15/2023 15:00")
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["title"], "Client Call")
        
        # Test with no events in range
        empty_events = self.calendar.get_events_between("05/16/2023", "05/19/2023")
        self.assertEqual(len(empty_events), 0)
    
    def test_find_next_available(self):
        """Test finding the next available time slot."""
        # Find next available time of 30 minutes after 05/15/2023 08:00
        next_time = self.calendar.find_next_available("05/15/2023 08:00", 30)
        self.assertEqual(next_time, "05/15/2023 08:00")
        
        # Find next available time of 60 minutes after a meeting starts
        next_time = self.calendar.find_next_available("05/15/2023 09:00", 60)
        self.assertEqual(next_time, "05/15/2023 10:00")
        
        # Find next available time of 45 minutes after second meeting
        next_time = self.calendar.find_next_available("05/15/2023 14:00", 45)
        self.assertEqual(next_time, "05/15/2023 14:30")
    
    def test_list_events(self):
        """Test listing all events."""
        events = self.calendar.list_events()
        self.assertEqual(len(events), 3)
        
        # Verify the returned dictionary has integer keys
        for key in events.keys():
            self.assertIsInstance(key, int)
    
    def test_get_event(self):
        """Test retrieving a specific event by ID."""
        # Get an existing event
        event = self.calendar.get_event(1)
        self.assertIsNotNone(event)
        self.assertEqual(event["title"], "Team Meeting")
        
        # Try to get a non-existent event
        non_existent = self.calendar.get_event(999)
        self.assertIsNone(non_existent)


if __name__ == "__main__":
    unittest.main()
