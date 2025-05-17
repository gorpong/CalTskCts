import os
import tempfile
import unittest
import json
from datetime import datetime
from unittest.mock import patch, mock_open

from caltskcts.calendars import Calendar


class TestCalendarsWithMocks(unittest.TestCase):
    """Test suite for the Calendar class using mocks."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create a temporary file path for testing
        self.temp_file = tempfile.NamedTemporaryFile(delete=False)
        self.temp_file_path = self.temp_file.name
        self.temp_file.close()
        
        # Set up patches
        self.json_load_patcher = patch('json.load')
        self.json_dump_patcher = patch('json.dump')
        self.mock_json_load = self.json_load_patcher.start()
        self.mock_json_dump = self.json_dump_patcher.start()
        
        # Default mock return for json.load
        self.mock_json_load.return_value = {}
        
    def tearDown(self):
        """Tear down test fixtures after each test method."""
        # Remove the temporary file
        if os.path.exists(self.temp_file_path):
            os.remove(self.temp_file_path)
            
        # Stop patchers
        self.json_load_patcher.stop()
        self.json_dump_patcher.stop()
    
    @patch('builtins.open', new_callable=mock_open)
    def test_initialization(self, mock_open):
        """Test calendar initialization with mocked open."""
        calendar = Calendar(self.temp_file_path)
        
        # Check that the file was opened for reading
        mock_open.assert_called_with(self.temp_file_path, 'r')
        
        # Verify json.load was called
        self.mock_json_load.assert_called_once()
    
    @patch('builtins.open', new_callable=mock_open)
    def test_add_event_saves_state(self, mock_open):
        """Test that adding an event saves the state."""
        # Configure mock to return empty state on load
        self.mock_json_load.return_value = {}
        
        calendar = Calendar(self.temp_file_path)
        
        # Reset mock_open to track new calls
        mock_open.reset_mock()
        
        # Add an event
        calendar.add_event(
            title="Test Event",
            date="05/15/2023 09:00",
            duration=60,
            users=["User1"]
        )
        
        # Check that file was opened for writing
        mock_open.assert_called_with(self.temp_file_path, 'w')
        
        # Verify json.dump was called to save the state
        self.mock_json_dump.assert_called_once()
    
    @patch('builtins.open', new_callable=mock_open)
    def test_load_state_file_not_found(self, mock_open):
        """Test loading state when the file doesn't exist."""
        # Make open raise FileNotFoundError
        mock_open.side_effect = FileNotFoundError()
        
        calendar = Calendar(self.temp_file_path)
        
        # Verify that json.load was not called
        self.mock_json_load.assert_not_called()
        
        # Verify internal state is empty
        self.assertEqual(len(calendar.items), 0)
    
    @patch('builtins.open', new_callable=mock_open)
    def test_load_state_invalid_json(self, mock_open):
        """Test loading state with invalid JSON data."""
        # Make json.load raise JSONDecodeError
        self.mock_json_load.side_effect = json.JSONDecodeError(
            "Expecting value", doc="{invalid json}", pos=0
        )
        
        calendar = Calendar(self.temp_file_path)
        
        # Verify internal state is empty despite error
        self.assertEqual(len(calendar.items), 0)
    
    @patch('builtins.open', new_callable=mock_open)
    def test_save_state_failure(self, mock_open):
        """Test handling of save state failures."""
        # Configure mock to return empty state on load
        self.mock_json_load.return_value = {}
        
        # Make json.dump raise an exception
        self.mock_json_dump.side_effect = IOError("Disk full")
        
        calendar = Calendar(self.temp_file_path)
        
        # Adding an event should trigger a save
        with self.assertRaises(IOError):
            calendar.add_event(
                title="Test Event",
                date="05/15/2023 09:00",
                duration=60,
                users=["User1"]
            )
    
    @patch('builtins.open', new_callable=mock_open)
    def test_get_next_id(self, mock_open):
        """Test getting the next ID with various state scenarios."""
        # Test with empty state
        self.mock_json_load.return_value = {}
        calendar = Calendar(self.temp_file_path)
        self.assertEqual(calendar._get_next_id(), 1)
        
        # Test with existing IDs
        self.mock_json_load.return_value = {"1": {}, "5": {}, "3": {}}
        calendar = Calendar(self.temp_file_path)
        self.assertEqual(calendar._get_next_id(), 6)  # Max ID (5) + 1
    
    @patch('caltskcts.calendars.datetime')
    @patch('builtins.open', new_callable=mock_open)
    def test_find_next_available_with_datetime_mock(self, mock_open, mock_datetime):
        """Test find_next_available with mocked datetime functionality."""
        # Configure mock for datetime.strptime to pass validation
        mock_datetime.strptime.side_effect = lambda *args: datetime.strptime(*args)
        
        # Configure mock state with events
        self.mock_json_load.return_value = {
            "1": {
                "title": "Event 1",
                "date": "05/15/2023 09:00",
                "duration": 60,
                "users": ["User1"]
            },
            "2": {
                "title": "Event 2",
                "date": "05/15/2023 11:00",
                "duration": 60,
                "users": ["User2"]
            }
        }
        
        calendar = Calendar(self.temp_file_path)
        
        # Test finding available time between events
        next_time = calendar.find_next_available("05/15/2023 08:00", 60)
        self.assertEqual(next_time, "05/15/2023 08:00")  # Before first event
        
        # Test finding available time after an event
        next_time = calendar.find_next_available("05/15/2023 09:00", 60)
        self.assertEqual(next_time, "05/15/2023 10:00")  # After first event
    
    @patch('builtins.open', new_callable=mock_open)
    def test_get_events_by_date_mock(self, mock_open):
        """Test get_events_by_date with mocked state."""
        # Configure mock state with events on same day
        self.mock_json_load.return_value = {
            "1": {
                "title": "Morning Event",
                "date": "05/15/2023 09:00",
                "duration": 60,
                "users": ["User1"]
            },
            "2": {
                "title": "Afternoon Event",
                "date": "05/15/2023 14:00",
                "duration": 60,
                "users": ["User2"]
            },
            "3": {
                "title": "Next Day Event",
                "date": "05/16/2023 10:00",
                "duration": 60,
                "users": ["User3"]
            }
        }
        
        calendar = Calendar(self.temp_file_path)
        
        # Test filtering events for a specific date
        events = calendar.get_events_by_date("05/15/2023")
        
        # Verify we got two events with the correct titles
        self.assertEqual(len(events), 2)
        
        titles = [event["title"] for event in events]
        self.assertIn("Morning Event", titles)
        self.assertIn("Afternoon Event", titles)
        self.assertNotIn("Next Day Event", titles)
    
    @patch('builtins.open', new_callable=mock_open)
    def test_get_events_between_mock(self, mock_open):
        """Test get_events_between with mocked state."""
        # Configure mock state with events on different days
        self.mock_json_load.return_value = {
            "1": {
                "title": "Day 1 Event",
                "date": "05/15/2023 09:00",
                "duration": 60,
                "users": ["User1"]
            },
            "2": {
                "title": "Day 2 Event",
                "date": "05/16/2023 14:00",
                "duration": 60,
                "users": ["User2"]
            },
            "3": {
                "title": "Day 3 Event",
                "date": "05/17/2023 10:00",
                "duration": 60,
                "users": ["User3"]
            }
        }
        
        calendar = Calendar(self.temp_file_path)
        
        # Test filtering events between two dates
        events = calendar.get_events_between("05/15/2023", "05/16/2023")
        
        # Verify we got two events with the correct titles
        self.assertEqual(len(events), 2)
        
        titles = [event["title"] for event in events]
        self.assertIn("Day 1 Event", titles)
        self.assertIn("Day 2 Event", titles)
        self.assertNotIn("Day 3 Event", titles)
    
    @patch('builtins.open', new_callable=mock_open)
    def test_update_event_mock(self, mock_open):
        """Test updating an event with mocked state."""
        # Configure mock state with an existing event
        self.mock_json_load.return_value = {
            "1": {
                "title": "Original Event",
                "date": "05/15/2023 09:00",
                "duration": 60,
                "users": ["User1"]
            }
        }
        
        calendar = Calendar(self.temp_file_path)
        
        # Reset mock_open to track new calls
        mock_open.reset_mock()
        
        # Update the event
        calendar.update_event(
            event_id=1,
            title="Updated Event",
            date="05/15/2023 10:00"
        )
        
        # Check that file was opened for writing
        mock_open.assert_called_with(self.temp_file_path, 'w')
        
        # Verify json.dump was called with updated data
        # Extract the updated state that was passed to json.dump
        updated_state = self.mock_json_dump.call_args[0][0]
        self.assertEqual(updated_state["1"]["title"], "Updated Event")
        self.assertEqual(updated_state["1"]["date"], "05/15/2023 10:00")
        self.assertEqual(updated_state["1"]["duration"], 60)  # Unchanged
    
    @patch('builtins.open', new_callable=mock_open)
    def test_delete_event_mock(self, mock_open):
        """Test deleting an event with mocked state."""
        # Configure mock state with events
        self.mock_json_load.return_value = {
            "1": {"title": "Event 1"},
            "2": {"title": "Event 2"}
        }
        
        calendar = Calendar(self.temp_file_path)
        
        # Reset mock_open to track new calls
        mock_open.reset_mock()
        
        # Delete an event
        result = calendar.delete_event(1)
        
        # Check result
        self.assertIn("deleted", result.lower())
        
        # Check that file was opened for writing
        mock_open.assert_called_with(self.temp_file_path, 'w')
        
        # Verify json.dump was called with updated state
        updated_state = self.mock_json_dump.call_args[0][0]
        self.assertNotIn("1", updated_state)
        self.assertIn("2", updated_state)
    
    @patch('builtins.open', new_callable=mock_open)
    def test_validation_behavior_with_mocks(self, mock_open):
        """Test validation behavior with various mock inputs."""
        calendar = Calendar(self.temp_file_path)
        
        # Test missing title
        with self.assertRaises(ValueError) as context:
            calendar._validate_item({"date": "05/15/2023 09:00"})
        self.assertEqual(str(context.exception), "Missing required field: title")
        
        # Test invalid date with specific mock
        with patch('caltskcts.calendars.datetime') as mock_datetime:
            mock_datetime.strptime.side_effect = ValueError("Invalid date")
            with self.assertRaises(ValueError) as context:
                calendar._validate_item({
                    "title": "Test Event",
                    "date": "invalid-date"
                })
            self.assertEqual(str(context.exception), "Invalid date format. Use MM/DD/YYYY HH:MM")


if __name__ == "__main__":
    unittest.main()
