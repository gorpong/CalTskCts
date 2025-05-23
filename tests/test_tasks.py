import os
import tempfile
import unittest
from datetime import datetime
from unittest.mock import patch

from caltskcts.tasks import Tasks

class TestTasks(unittest.TestCase):
    """Test suite for the Tasks class."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create a temporary file for state management
        self.temp_file = tempfile.NamedTemporaryFile(delete=False)
        self.temp_file_path = self.temp_file.name
        self.temp_file.close()
        
        # Create a Tasks instance with the temporary file
        self.tasks = Tasks(self.temp_file_path)
        
        # Create some sample tasks for testing
        self.tasks.add_task(
            title="Test Task",
            description="This is a test task",
            due_date="05/15/2023",
            progress=0.0,
            state="Not Started"
        )
        
        self.tasks.add_task(
            title="In Progress Task",
            description="This task is in progress",
            due_date="05/20/2023",
            progress=50.0,
            state="In Progress"
        )
        
        self.tasks.add_task(
            title="Completed Task",
            description="This task is completed",
            due_date="05/10/2023",
            progress=100.0,
            state="Completed"
        )
    
    def tearDown(self):
        """Tear down test fixtures after each test method."""
        # Remove the temporary file
        if os.path.exists(self.temp_file_path):
            os.remove(self.temp_file_path)
    
    def test_validate_item_valid_data(self):
        """Test validation of task data with valid input."""
        valid_item = {
            "title": "Test Task",
            "desc": "Test Description",
            "dueDate": "12/31/2023",
            "progress": 50.0,
            "state": "In Progress"
        }
        self.assertTrue(self.tasks._validate_item(valid_item))
    
    def test_validate_item_missing_title(self):
        """Test validation of task data with missing title."""
        invalid_item = {
            "desc": "Test Description",
            "dueDate": "12/31/2023",
            "progress": 50.0,
            "state": "In Progress"
        }
        with self.assertRaises(ValueError) as context:
            self.tasks._validate_item(invalid_item)
        self.assertEqual(str(context.exception), "Missing required field: title")

    def test_validate_item_invalid_date_format(self):
        """Test validation of task data with invalid date format."""
        invalid_item = {
            "title": "Test Task",
            "desc": "Test Description",
            "dueDate": "2023-12-31",  # Wrong format
            "progress": 50.0,
            "state": "In Progress"
        }
        with self.assertRaises(ValueError) as context:
            self.tasks._validate_item(invalid_item)
        self.assertEqual(str(context.exception), "Invalid date format. Use MM/DD/YYYY")
    
    def test_validate_item_invalid_progress(self):
        """Test validation of task data with invalid progress value."""
        # Test with negative progress
        invalid_item = {
            "title": "Test Task",
            "desc": "Test Description",
            "dueDate": "12/31/2023",
            "progress": -10.0,
            "state": "In Progress"
        }
        with self.assertRaises(ValueError) as context:
            self.tasks._validate_item(invalid_item)
        self.assertEqual(str(context.exception), "Progress must be a number between 0 and 100")
        
        # Test with progress > 100
        invalid_item["progress"] = 110.0
        with self.assertRaises(ValueError) as context:
            self.tasks._validate_item(invalid_item)
        self.assertEqual(str(context.exception), "Progress must be a number between 0 and 100")
        
        # Test with non-numeric progress
        invalid_item["progress"] = "50%"
        with self.assertRaises(ValueError) as context:
            self.tasks._validate_item(invalid_item)
        self.assertEqual(str(context.exception), "Progress must be a number")
    
    def test_validate_item_invalid_state(self):
        """Test validation of task data with invalid state."""
        invalid_item = {
            "title": "Test Task",
            "desc": "Test Description",
            "dueDate": "12/31/2023",
            "progress": 50.0,
            "state": "Invalid State"
        }
        with self.assertRaises(ValueError) as context:
            self.tasks._validate_item(invalid_item)
        self.assertIn("Invalid state. Must be one of:", str(context.exception))

    def test_add_task_basic(self):
        """Test adding a basic task."""
        result = self.tasks.add_task(
            title="New Task", 
            due_date="05/15/2023",
            description="Description"
        )
        self.assertIn("added", result.lower())
        
        # Verify task was added correctly
        tasks = self.tasks.list_tasks()
        self.assertEqual(len(tasks), 4)  # 3 from setUp + 1 new one
    
    def test_add_task_with_custom_id(self):
        """Test adding a task with a custom ID."""
        result = self.tasks.add_task(
            title="Custom ID Task",
            description="Using a custom ID",
            due_date="05/15/2023",
            task_id=100
        )
        self.assertIn("added", result.lower())
        
        # Verify task has correct ID
        task = self.tasks.get_task(100)
        self.assertIsNotNone(task)
        self.assertEqual(task["title"], "Custom ID Task")
    
    def test_add_task_duplicate_id_fails(self):
        """Test that adding a task with an existing ID fails."""
        with self.assertRaises(ValueError):
            self.tasks.add_task(title="Duplicate ID", task_id=1)
    
    def test_add_task_invalid_date_format(self):
        """Test that adding a task with invalid date format fails."""
        with self.assertRaises(ValueError):
            self.tasks.add_task(
                title="Invalid Date Task",
                description="Will fail due to date format",
                due_date="2023-05-15"  # Wrong format (should be MM/DD/YYYY)
            )
    
    def test_add_task_validation_edge_cases(self):
        """Test edge cases for task validation during add."""
        edge_cases = [
            # No title (should fail)
            ({"desc": "Empty title", "progress": 0.0, "state": "Not Started"}, ValueError),
            
            # Extremely long title (should pass validation as there's no length limit)
            ({"title": "X" * 1000, "desc": "Long title", "progress": 0.0, "state": "Not Started"}, None),
            
            # Special characters in title (should pass)
            ({"title": "Task with !@#$%^&*()", "desc": "Special chars", "progress": 0.0, "state": "Not Started"}, None),
            
            # Decimal progress values (should pass)
            ({"title": "Decimal Progress", "desc": "Floating point", "progress": 33.33, "state": "Not Started"}, None),
            
            # Progress boundary cases
            ({"title": "Min Progress", "desc": "Zero progress", "progress": 0, "state": "Not Started"}, None),
            ({"title": "Max Progress", "desc": "Hundred progress", "progress": 100, "state": "Not Started"}, None),
            ({"title": "Just Under Max", "desc": "99.99 progress", "progress": 99.99, "state": "Not Started"}, None),
            ({"title": "Just Over Min", "desc": "0.01 progress", "progress": 0.01, "state": "Not Started"}, None),
            ({"title": "Negative Progress", "desc": "Should fail", "progress": -1, "state": "Not Started"}, ValueError),
            ({"title": "Overflow Progress", "desc": "Should fail", "progress": 101, "state": "Not Started"}, ValueError),
        ]
        
        for task_data, expected_exception in edge_cases:
            with self.subTest(task_data=task_data):
                if expected_exception:
                    with self.assertRaises(expected_exception):
                        self.tasks._validate_item(task_data)
                else:
                    # This should not raise an exception
                    result = self.tasks._validate_item(task_data)
                    self.assertTrue(result)

    def test_add_task_invalid_progress_fails(self):
        """Test that adding a task with invalid progress fails."""
        with self.assertRaises(ValueError):
            self.tasks.add_task(
                title="Invalid Progress Task",
                description="Will fail due to progress value",
                progress=150.0  # Out of range
            )
    
    def test_add_task_invalid_state_fails(self):
        """Test that adding a task with invalid state fails."""
        with self.assertRaises(ValueError):
            self.tasks.add_task(
                title="Invalid State Task",
                description="Will fail due to state value",
                state="Invalid State"
            )
    
    def test_update_task_basic(self):
        """Test updating a task with basic fields."""
        result = self.tasks.update_task(1, title="Updated Title")
        self.assertIn("updated", result.lower())
        
        # Verify update was applied
        task = self.tasks.get_task(1)
        self.assertEqual(task["title"], "Updated Title")
        self.assertEqual(task["desc"], "This is a test task")  # Unchanged
    
    def test_update_task_nonexistent_id_fails(self):
        """Test that updating a nonexistent task fails."""
        with self.assertRaises(ValueError):
            self.tasks.update_task(999, title="Should Fail")
    
    def test_update_task_invalid_date_format(self):
        """Test that updating a task with invalid date format fails."""
        with self.assertRaises(ValueError):
            self.tasks.update_task(1, due_date="2023-05-15")  # Wrong format
    
    def test_update_task_invalid_progress_fails(self):
        """Test that updating a task with invalid progress fails."""
        with self.assertRaises(ValueError):
            self.tasks.update_task(1, progress=150.0)  # Out of range
    
    def test_update_task_invalid_state_fails(self):
        """Test that updating a task with invalid state fails."""
        with self.assertRaises(ValueError):
            self.tasks.update_task(1, state="Invalid State")
    
    def test_update_task_auto_complete_from_progress(self):
        """Test that updating progress to 100 auto-updates state to Completed."""
        result = self.tasks.update_task(1, progress=100.0)
        self.assertIn("updated", result.lower())
        
        task = self.tasks.get_task(1)
        self.assertEqual(task["state"], "Completed")
    
    def test_update_task_auto_complete_from_state(self):
        """Test that updating state to Completed auto-updates progress to 100."""
        result = self.tasks.update_task(1, state="Completed")
        self.assertIn("updated", result.lower())
        
        task = self.tasks.get_task(1)
        self.assertEqual(task["progress"], 100.0)
    
    def test_update_with_none_values_succeeds(self):
        """Test that updating with None values explicitly passed succeeds."""
        result = self.tasks.update_task(1, description=None, progress=None, state=None)
        self.assertIn("updated", result.lower())
        
        task = self.tasks.get_task(1)
        self.assertEqual(task["progress"], 0.0)
        self.assertEqual(task["state"], "Not Started")
        self.assertEqual(task["dueDate"], "05/15/2023")

    def test_update_with_empty_strings_succeeds(self):
        """Test that updating with an empty string to certain fields succeeds."""
        result = self.tasks.update_task(1, description="")
        self.assertIn("updated", result.lower())
        
        task = self.tasks.get_task(1)
        self.assertEqual(len(task["desc"]), 0)
        
    def test_delete_task(self):
        """Test deleting a task."""
        result = self.tasks.delete_task(1)
        self.assertIn("deleted", result.lower())
        
        # Verify task was deleted
        self.assertIsNone(self.tasks.get_task(1))
    
    def test_delete_nonexistent_task_fails(self):
        """Test that deleting a nonexistent task fails."""
        with self.assertRaises(ValueError):
            self.tasks.delete_task(999)
    
    def test_get_tasks_due_today(self):
        """Test getting tasks due today or before."""
        # Mock today's date to make test deterministic
        with patch('caltskcts.tasks.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2023, 5, 17, 12, 0)
            mock_datetime.strptime.side_effect = datetime.strptime
            
            due_tasks = self.tasks.get_tasks_due_today()
            
            # Should include tasks due on or before May 17, 2023 (but not completed)
            task_ids = [task["task_id"] for task in due_tasks]
            self.assertIn(1, task_ids)  # Due May 15
            self.assertNotIn(2, task_ids)  # Due May 20 (but after our mock date)
            self.assertNotIn(3, task_ids)  # Completed task is filtered out
    
    def test_get_tasks_due_on(self):
        """Test getting tasks due on a specific date."""
        # Test with a specific date
        due_tasks = self.tasks.get_tasks_due_on("05/15/2023")
        task_ids = [task["task_id"] for task in due_tasks]
        self.assertIn(1, task_ids)
        self.assertNotIn(2, task_ids)  # Different due date
        self.assertNotIn(3, task_ids)  # Completed task or different date
    
    def test_get_tasks_due_on_or_before(self):
        """Test getting tasks due on or before a specific date."""
        # Mock to test with a specific date
        due_tasks = self.tasks.get_tasks_due_on_or_before("05/15/2023")
        task_ids = [task["task_id"] for task in due_tasks]
        # Should include task 1 (May 15) but not task 3 (Completed)
        self.assertIn(1, task_ids)
        self.assertNotIn(3, task_ids)
    
    def test_get_tasks_with_progress(self):
        """Test getting tasks filtered by progress range."""
        # Get tasks with progress between 40 and 60
        progress_tasks = self.tasks.get_tasks_with_progress(40.0, 60.0)
        task_ids = [task["task_id"] for task in progress_tasks]
        self.assertIn(2, task_ids)  # Has 50% progress
        self.assertNotIn(1, task_ids)  # Has 0% progress
        self.assertNotIn(3, task_ids)  # Has 100% progress
    
    def test_get_tasks_by_state(self):
        """Test filtering tasks by state."""
        # Get all tasks with state "Not Started"
        not_started_tasks = self.tasks.get_tasks_by_state("Not Started")
        task_ids = [task["item_id"] for task in not_started_tasks]
        self.assertIn(1, task_ids)
        self.assertNotIn(2, task_ids)  # "In Progress"
        self.assertNotIn(3, task_ids)  # "Completed"
    
    def test_list_tasks(self):
        """Test listing all tasks."""
        all_tasks = self.tasks.list_tasks()
        # Should have 3 tasks from setUp
        self.assertEqual(len(all_tasks), 3)
        self.assertIn(1, all_tasks)
        self.assertIn(2, all_tasks)
        self.assertIn(3, all_tasks)
    
    def test_get_task(self):
        """Test getting a specific task."""
        task = self.tasks.get_task(1)
        self.assertIsNotNone(task)
        self.assertEqual(task["title"], "Test Task")
        self.assertEqual(task["desc"], "This is a test task")
    
    def test_get_nonexistent_task(self):
        """Test getting a task with a nonexistent ID returns None."""
        task = self.tasks.get_task(999)
        self.assertIsNone(task)
    
    def test_validate_item_complete_validation(self):
        """Test comprehensive validation of task data."""
        # Valid task data
        valid_task = {
            "title": "Valid Task",
            "desc": "This is valid",
            "dueDate": "12/31/2023",
            "progress": 75.0,
            "state": "In Progress"
        }
        
        # Should not raise exception
        result = self.tasks._validate_item(valid_task)
        self.assertTrue(result)
        
        # Invalid cases - each should raise ValueError
        
        # Missing title
        with self.assertRaises(ValueError):
            self.tasks._validate_item({"desc": "No title"})
        
        # Invalid date format
        with self.assertRaises(ValueError):
            self.tasks._validate_item({**valid_task, "dueDate": "2023-12-31"})
        
        # Invalid progress (out of range)
        with self.assertRaises(ValueError):
            self.tasks._validate_item({**valid_task, "progress": 150.0})
        
        # Invalid state
        with self.assertRaises(ValueError):
            self.tasks._validate_item({**valid_task, "state": "Unknown"})

    def test_date_validation_formats(self):
        """Test various date format scenarios."""
        test_cases = [
            # Valid formats
            ("01/01/2023", False),  # Standard MM/DD/YYYY
            ("12/31/2023", False),  # End of year
            ("02/29/2024", False),  # Leap year
            
            # Invalid formats
            ("2023/01/01", True),   # YYYY/MM/DD
            ("01-01-2023", True),   # MM-DD-YYYY
            ("01/01/23", True),     # MM/DD/YY
            ("January 1, 2023", True),  # Named month
            ("2023-01-01", True),   # ISO format
            ("", True),             # Empty string
            ("not a date", True),   # Nonsensical string
        ]
        
        for date_str, should_raise in test_cases:
            with self.subTest(date_str=date_str):
                task_data = {
                    "title": "Date Test", 
                    "desc": "Testing date format",
                    "dueDate": date_str,
                    "progress": 0.0, 
                    "state": "Not Started"
                }
                if should_raise:
                    with self.assertRaises(ValueError):
                        self.tasks._validate_item(task_data)
                else:
                    # This should not raise an exception
                    result = self.tasks._validate_item(task_data)
                    self.assertTrue(result)
    
    def test_state_validation_comprehensive(self):
        """Test all possible state values and invalid states."""
        # All valid states defined in Tasks.VALID_STATES
        for state in self.tasks.VALID_STATES:
            with self.subTest(state=state):
                task_data = {
                    "title": f"State Test - {state}", 
                    "desc": f"Testing state: {state}",
                    "progress": 0.0, 
                    "state": state
                }
                # Should not raise an exception
                result = self.tasks._validate_item(task_data)
                self.assertTrue(result)
        
        # Test invalid states
        invalid_states = [
            "Not started",            # Incorrect capitalization
            "In progress",            # Incorrect capitalization
            "partially completed",    # Case sensitivity
            "Pending",                # Similar but not exactly matching
            "",                       # Empty string
            "Complete",               # Common misspelling
            "Done",                   # Common alternative
            "Cancelled With Typo",    # Extra words
        ]
        
        for state in invalid_states:
            with self.subTest(state=state):
                task_data = {
                    "title": f"Invalid State Test - {state}", 
                    "desc": f"Testing invalid state: {state}",
                    "progress": 0.0, 
                    "state": state
                }
                with self.assertRaises(ValueError):
                    self.tasks._validate_item(task_data)
    
    def test_get_tasks_with_custom_date(self):
        """Test the date-based task retrieval methods with mocked state."""
        # Create mock tasks with different due dates in the state
        self.tasks._state = {
            "1": {"title": "Past Due", "desc": "Due yesterday", "dueDate": "05/10/2023", "progress": 0.0, "state": "Not Started"},
            "2": {"title": "Due Today", "desc": "Due right now", "dueDate": "05/15/2023", "progress": 0.0, "state": "Not Started"},
            "3": {"title": "Future Due", "desc": "Due tomorrow", "dueDate": "05/20/2023", "progress": 0.0, "state": "Not Started"},
            "4": {"title": "Completed", "desc": "Already done", "dueDate": "05/05/2023", "progress": 100.0, "state": "Completed"},
        }
        
        # Test get_tasks_due_today with May 15, 2023 as today
        with patch('caltskcts.tasks.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2023, 5, 15, 12, 0)
            mock_datetime.strptime.side_effect = datetime.strptime
            
            due_today_tasks = self.tasks.get_tasks_due_today()
            # Should include tasks 1 (past due) and 2 (due today) but not completed or future tasks
            task_ids = [task["task_id"] for task in due_today_tasks]
            self.assertIn(1, task_ids)  # Past due task
            self.assertIn(2, task_ids)  # Due today
            self.assertNotIn(3, task_ids)  # Future task
            self.assertNotIn(4, task_ids)  # Completed task
    
    def test_search_edge_cases(self):
        """Test edge cases for the search_items method."""
        # Create some test data
        self.tasks._state = {
            "1": {"title": "Important Task", "desc": "Critical issue", "dueDate": "05/10/2023", "state": "In Progress"},
            "2": {"title": "Urgent Task", "desc": "Must be done soon", "dueDate": "05/15/2023", "state": "Not Started"},
            "3": {"title": "Regular Task", "desc": "Normal work", "dueDate": "05/05/2023", "state": "Completed"},
            "4": {"title": "Special-Task", "desc": "With-hyphens", "dueDate": "06/20/2023", "state": "On Hold"},
            "5": {"title": "task123", "desc": "Mixed content", "dueDate": "05/17/2023", "state": "In Progress"},
        }
        
        # Test empty search query, get back everything
        results = self.tasks.search_items("", ["title"])
        self.assertEqual(len(results), 5)
        
        # Test search with no matches
        results = self.tasks.search_items("NonExistentString", ["title", "desc", "state"])
        self.assertEqual(len(results), 0)
        
        # Test case insensitivity 
        results = self.tasks.search_items("urgent", ["title"])
        self.assertGreater(len(results), 0)
        self.assertEqual(results[0]["title"], "Urgent Task")
        
        # Test regex special characters
        results = self.tasks.search_items("Special-Task", ["title"])
        self.assertEqual(len(results), 1)
        
        # Test invalid regex pattern
        with self.assertRaises(ValueError):
            self.tasks.search_items("[", ["title"])  # Unclosed character class

if __name__ == "__main__":
    unittest.main()
