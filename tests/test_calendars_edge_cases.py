import os
import tempfile
import unittest

from caltskcts.calendars import Calendar

class TestCalendarEdgeCases(unittest.TestCase):
    """Test suite for edge cases in the Calendar class."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create a temporary file for state management
        self.temp_file = tempfile.NamedTemporaryFile(delete=False)
        self.temp_file_path = self.temp_file.name
        self.temp_file.close()
        
        # Create a Calendar instance with the temporary file
        self.calendar = Calendar(self.temp_file_path)
    
    def tearDown(self):
        """Tear down test fixtures after each test method."""
        # Remove the temporary file
        if os.path.exists(self.temp_file_path):
            os.remove(self.temp_file_path)
    
    def test_update_event_empty_state(self):
        """Test updating an event when state is empty."""
        with self.assertRaises(ValueError) as context:
            self.calendar.update_event(1, title="Non-existent Event")
        self.assertIn("does not exist", str(context.exception))
    
    def test_delete_event_empty_state(self):
        """Test deleting an event when state is empty."""
        with self.assertRaises(ValueError) as context:
            self.calendar.delete_event(1)
        self.assertIn("does not exist", str(context.exception))
    
    def test_get_events_by_date_empty_state(self):
        """Test getting events by date when state is empty."""
        events = self.calendar.get_events_by_date("01/01/2023")
        self.assertEqual(len(events), 0)
        self.assertIsInstance(events, list)
    
    def test_get_events_between_empty_state(self):
        """Test getting events between dates when state is empty."""
        events = self.calendar.get_events_between("01/01/2023", "01/31/2023")
        self.assertEqual(len(events), 0)
        self.assertIsInstance(events, list)
    
    def test_find_next_available_empty_state(self):
        """Test finding next available time when state is empty."""
        start_time = "01/01/2023 09:00"
        next_time = self.calendar.find_next_available(start_time, 30)
        self.assertEqual(next_time, start_time)
    
    def test_list_events_empty_state(self):
        """Test listing all events when state is empty."""
        events = self.calendar.list_events()
        self.assertEqual(len(events), 0)
        self.assertIsInstance(events, dict)
    
    def test_get_event_empty_state(self):
        """Test getting a specific event when state is empty."""
        event = self.calendar.get_event(1)
        self.assertIsNone(event)
    
    def test_get_events_between_with_partial_dates(self):
        """Test getting events between dates when only dates (no times) are provided."""
        self.calendar.add_event(
            title="Morning Meeting",
            date="05/15/2023 09:00",
            duration=60,
            users=["Alice"]
        )
        self.calendar.add_event(
            title="Evening Meeting",
            date="05/15/2023 17:00",
            duration=60,
            users=["Bob"]
        )
        
        # Only providing dates, not times
        events = self.calendar.get_events_between("05/15/2023", "05/15/2023")
        self.assertEqual(len(events), 2)
        
        # Providing partial date/times
        events = self.calendar.get_events_between("05/15/2023", "05/15/2023 12:00")
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["title"], "Morning Meeting")
    
    def test_find_next_available_with_overlapping_events(self):
        """Test finding next available time with overlapping events."""

        # Add several events
        self.calendar.add_event(
            title="Event 1",
            date="01/01/2023 09:00",
            duration=60,
            users=["Alice"]
        )
        self.calendar.add_event(
            title="Event 2",
            date="01/01/2023 10:30",
            duration=60,
            users=["Bob"]
        )
        
        # Should find slot between events
        next_time = self.calendar.find_next_available("01/01/2023 08:00", 60)
        self.assertEqual(next_time, "01/01/2023 08:00")
        
        # Starting during first event, should find time at end of first event
        # THIS SHOULD BE CORRECT, but it isn't due to underlying issue in
        # find_next_available where it skips over currently active meetings when
        # you're requesting a next available slot AFTER it starts. Fix that
        # code and then remove the @pytest.mark.xfail and this should work
        next_time = self.calendar.find_next_available("01/01/2023 09:30", 30)
        self.assertEqual(next_time, "01/01/2023 10:00") # SHOULD be 10, but
        
        # Not enough time between events for requested duration
        next_time = self.calendar.find_next_available("01/01/2023 10:00", 60)
        self.assertEqual(next_time, "01/01/2023 11:30")
    
    def test_validate_item_edge_cases(self):
        """Test validation with edge cases for event data."""
        # Title is a required field
        invalid_item = {
            "date": "05/15/2023 09:00",
            "duration": 60,
            "users": []
        }
        with self.assertRaises(ValueError):
            self.calendar._validate_item(invalid_item)
        
        # Test with minimum valid values
        valid_item = {
            "title": "Minimal Event",
            "date": "01/01/2023 00:00",
            "duration": 1,
            "users": []
        }
        self.assertTrue(self.calendar._validate_item(valid_item))
        
        # Test with missing optional fields
        partial_item = {
            "title": "Partial Event"
        }
        # This should pass as other fields are optional
        self.assertTrue(self.calendar._validate_item(partial_item))
    
    def test_add_event_with_unicode_characters(self):
        """Test adding an event with Unicode characters in the title."""
        result = self.calendar.add_event(
            title="Café Meeting ☕",
            date="05/15/2023 09:00",
            duration=60,
            users=["José", "François"]
        )
        self.assertIn("Added", result)
        
        # Verify event was stored correctly
        event = self.calendar.get_event(1)
        self.assertEqual(event["title"], "Café Meeting ☕")
        self.assertEqual(event["users"], ["José", "François"])
    
    def test_state_file_persistence(self):
        """Test that calendar state is persisted to file."""
        # Add an event
        self.calendar.add_event(
            title="Persistent Event",
            date="05/15/2023 09:00",
            duration=60,
            users=["User1"]
        )
        
        # Create a new calendar instance that reads from the same file
        new_calendar = Calendar(self.temp_file_path)
        
        # Verify the event was loaded
        event = new_calendar.get_event(1)
        self.assertIsNotNone(event)
        self.assertEqual(event["title"], "Persistent Event")
    
    def test_add_event_with_no_users(self):
        """Test adding an event with an empty users list."""
        result = self.calendar.add_event(
            title="Solo Event",
            date="05/15/2023 09:00",
            duration=60,
            users=[]
        )
        self.assertIn("Added", result)
        
        event = self.calendar.get_event(1)
        self.assertEqual(event["users"], [])
        
    def test_add_event_duration_edge_cases(self):
        """Test adding events with edge case durations."""
        # Minimum duration
        result = self.calendar.add_event(
            title="Very Short Event",
            date="05/15/2023 09:00",
            duration=1  # 1 minute
        )
        self.assertIn("Added", result)
        
        # Very long duration
        result = self.calendar.add_event(
            title="Very Long Event",
            date="05/15/2023 10:00",
            duration=1440  # 24 hours
        )
        self.assertIn("Added", result)


if __name__ == "__main__":
    unittest.main()
