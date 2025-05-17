import unittest
from unittest.mock import patch
from datetime import datetime

from caltskcts.tasks import Tasks

class TestTasksWithMocks(unittest.TestCase):
    """Test suite for the Tasks class using mocks to isolate from file system."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Use patch to mock the file operations
        self.state_file_patcher = patch('tasks.StateManagerBase._load_state')
        self.mock_load_state = self.state_file_patcher.start()
        
        # Mock the _save_state method to prevent actual file writes
        self.save_state_patcher = patch('tasks.StateManagerBase._save_state')
        self.mock_save_state = self.save_state_patcher.start()
        
        # Setup empty initial state
        self.mock_load_state.return_value = {}
        self.mock_save_state.return_value = None
        
        # Initialize Tasks with our mocked file operations
        self.tasks = Tasks("/fake/path/to/state.json")
    
    def tearDown(self):
        """Tear down test fixtures after each test method."""
        self.state_file_patcher.stop()
        self.save_state_patcher.stop()
    
    def test_add_task_with_mocked_state(self):
        """Test adding a task when state is mocked."""
        # Mock add_item to return True (successful add)
        with patch.object(self.tasks, 'add_item', return_value=True):
            result = self.tasks.add_task(
                title="Mocked Task",
                due_date="05/15/2023",
                description="This task was added with mocked state"
            )
            self.assertIn("added", result.lower())
    
    def test_add_task_duplicate_id_with_mock(self):
        """Test that adding a task with an existing ID fails when using mock."""
        # Mock add_item to return False (ID already exists)
        with patch.object(self.tasks, 'add_item', return_value=False):
            with self.assertRaises(ValueError):
                self.tasks.add_task(
                    title="Duplicate ID",
                    due_date="05/15/2023",
                    description="This will fail due to mocked duplicate ID",
                    task_id=1
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
    
    def test_update_task_edge_cases(self):
        """Test edge cases for task updates."""
        # Mock get_item to return a valid task
        with patch.object(self.tasks, 'get_item', return_value={
            "title": "Original", 
            "desc": "Original description", 
            "dueDate": "05/15/2023",
            "progress": 50.0, 
            "state": "In Progress"
        }):
            # Mock update_item to return True (successful update)
            with patch.object(self.tasks, 'update_item', return_value=True):
                # Test partial updates - only one field changes
                self.tasks.update_task(1, title="Updated Title Only")
                
                # Test updating with None values (should not change those fields)
                self.tasks.update_task(1, description=None, progress=None, state=None)
                
                # Test empty strings
                self.tasks.update_task(1, description="")
    
    def test_update_task_invalid_combinations(self):
        """Test updating with combinations that should be validated correctly."""
        # Mock get_item to return a valid task
        with patch.object(self.tasks, 'get_item', return_value={
            "title": "Original", 
            "desc": "Original description", 
            "dueDate": "05/15/2023",
            "progress": 50.0, 
            "state": "In Progress"
        }):
            # Mock update_item to return True (successful update)
            with patch.object(self.tasks, 'update_item', return_value=True):
                # Test progress 100 with state that's not Completed
                self.tasks.update_task(1, progress=100.0, state="In Progress")
                
                # Test state Completed with progress that's not 100
                self.tasks.update_task(1, state="Completed", progress=99.0)
                
                # Test state Completed auto-updates progress
                self.tasks.update_task(1, state="Completed")
                
                # Test progress 100 auto-updates state
                self.tasks.update_task(1, progress=100.0)
    
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
