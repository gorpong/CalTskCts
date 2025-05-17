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


if __name__ == "__main__":
    unittest.main()
