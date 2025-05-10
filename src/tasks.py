from typing import Dict, List, Optional, Any
from datetime import datetime
from state_manager import StateManagerBase
from validation_utils import (
    validate_required_fields,
    validate_date_format,
    validate_numeric_range,
    validate_enum_value
)

class TaskData(Dict[str, Any]):
    """Type for task data with expected fields."""
    title: str
    desc: str
    dueDate: Optional[str]  # "MM/DD/YYYY" format
    progress: float
    state: str

class Tasks(StateManagerBase[TaskData]):
    """Manages tasks and their due dates, status, and completion progress."""
    
    VALID_STATES = ["Not Started", "In Progress", "Completed", "On Hold", "Cancelled"]
    
    def _validate_item(self, item: Dict[str, Any]) -> bool:
        """
        Validate task data before adding/updating.
        
        Args:
            item: Task data to validate
            
        Returns:
            True if valid
            
        Raises:
            ValueError: If validation fails
        """
        # Check required fields
        validate_required_fields(item, ["title"])
            
        # Validate date format if provided
        if "dueDate" in item and item["dueDate"] is not None:
            validate_date_format(item["dueDate"], "%m/%d/%Y")
        
        # Validate progress range
        if "progress" in item:
            validate_numeric_range(item["progress"], "Progress", 0, 100)
        
        # Validate state if provided
        if "state" in item:
            validate_enum_value(item["state"], self.VALID_STATES, "state")
            
        return True

    def add_task(
        self,
        title: str = "",
        description: str = "",
        due_date: Optional[str] = None,
        progress: float = 0.0,
        state: str = "Not Started",
        task_id: Optional[int] = None,
    ) -> str:
        """
        Add a new task.
        
        Args:
            title: Task title
            description: Task description
            due_date: Due date in MM/DD/YYYY format
            progress: Completion percentage (0-100)
            state: Task state
            task_id: Optional specific ID to use
            
        Returns:
            Success message
            
        Raises:
            ValueError: If task_id already exists or validation fails
        """
        if not task_id:
            task_id = self._get_next_id()
        
        task_data = {
            "title": title,
            "desc": description,
            "dueDate": due_date,
            "progress": progress,
            "state": state,
        }
        
        # Validate before adding
        self._validate_item(task_data)
        
        if self.add_item(task_id, task_data):
            return f"Task {task_id} added"
        else:
            raise ValueError(f"Task with ID {task_id} already exists.")
    
    def update_task(
        self,
        task_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        due_date: Optional[str] = None,
        progress: Optional[float] = None,
        state: Optional[str] = None,
    ) -> str:
        """
        Update an existing task.
        
        Args:
            task_id: ID of task to update
            title: New title
            description: New description
            due_date: New due date
            progress: New progress value
            state: New state
            
        Returns:
            Success message
            
        Raises:
            ValueError: If task doesn't exist or validation fails
        """
        current_data = self.get_item(task_id)
        if not current_data:
            raise ValueError(f"Task with ID {task_id} does not exist.")
        
        # Build updates dictionary with consistency between progress and state
        updates = {}
        if title is not None:
            updates["title"] = title
        if description is not None:
            updates["desc"] = description
        if due_date is not None:
            updates["dueDate"] = due_date
        if progress is not None:
            updates["progress"] = progress
            # Auto-update state if progress is 100%
            if progress == 100.0:
                updates["state"] = "Completed"
        if state is not None:
            updates["state"] = state
            # Auto-update progress if state is "Completed"
            if state == "Completed":
                updates["progress"] = 100.0
                
        # Create merged data for validation
        merged_data = {**current_data, **updates}
        self._validate_item(merged_data)

        if self.update_item(task_id, updates):
            return f"Task {task_id} updated"
        else:
            raise ValueError(f"Failed to update task {task_id}")
    
    def delete_task(self, task_id: int) -> str:
        """
        Delete a task.
        
        Args:
            task_id: ID of task to delete
            
        Returns:
            Success message
            
        Raises:
            ValueError: If task doesn't exist
        """
        if self.delete_item(task_id):
            return f"Task {task_id} deleted"
        else:
            raise ValueError(f"Task with ID {task_id} does not exist.")

    def get_tasks_due_today(self, today: Optional[str] = None) -> List[TaskData]:
        """
        Get all tasks due today or before.
        
        Args:
            today: Optional date in MM/DD/YYYY format, defaults to current date
            
        Returns:
            List of tasks
        """
        if not today:
            today = datetime.now().strftime("%m/%d/%Y")
            
        today_date = datetime.strptime(today, "%m/%d/%Y")
        
        results = []
        for task_id, task in self.items.items():
            if not task["dueDate"] or task["state"] == "Completed":
                continue
                
            task_date = datetime.strptime(task["dueDate"], "%m/%d/%Y")
            if task_date.date() <= today_date.date():
                results.append({"task_id": int(task_id), **task})
                
        return results

    def get_tasks_due_on(self, date: str) -> List[TaskData]:
        """
        Get all tasks due on a specific date.
        
        Args:
            date: Date in MM/DD/YYYY format
            
        Returns:
            List of tasks
        """
        target_date = datetime.strptime(date, "%m/%d/%Y")
        
        results = []
        for task_id, task in self.items.items():
            if not task["dueDate"] or task["state"] == "Completed":
                continue
                
            task_date = datetime.strptime(task["dueDate"], "%m/%d/%Y")
            if task_date.date() == target_date.date():
                results.append({"task_id": int(task_id), **task})
                
        return results

    def get_tasks_due_on_or_before(self, date: str) -> List[TaskData]:
        """
        Get all tasks due on or before a date.
        
        Args:
            date: Date in MM/DD/YYYY format
            
        Returns:
            List of tasks
        """
        target_date = datetime.strptime(date, "%m/%d/%Y")
        
        results = []
        for task_id, task in self.items.items():
            if not task["dueDate"] or task["state"] == "Completed":
                continue
                
            task_date = datetime.strptime(task["dueDate"], "%m/%d/%Y")
            if task_date.date() <= target_date.date():
                results.append({"task_id": int(task_id), **task})
                
        return results

    def get_tasks_with_progress(
        self,
        min_progress: float = 0.0,
        max_progress: float = 100.0
    ) -> List[TaskData]:
        """
        Get tasks filtered by progress range.
        
        Args:
            min_progress: Minimum progress value
            max_progress: Maximum progress value
            
        Returns:
            List of tasks within the progress range
        """
        results = []
        for task_id, task in self.items.items():
            progress = task["progress"]
            if min_progress <= progress <= max_progress:
                results.append({"task_id": int(task_id), **task})
                
        return results

    def get_tasks_by_state(self, state: str = "Not Started") -> List[TaskData]:
        """
        Get tasks matching a state pattern.
        
        Args:
            state: State or state pattern to match
            
        Returns:
            List of matching tasks
        """
        return self.search_items(state, ["state"])
    
    def list_tasks(self) -> Dict[int, Any]:
        """
        List all tasks.
        
        Returns:
            Dictionary of all tasks with integer keys
        """
        return self.list_items()
    
    def get_task(self, task_id: int) -> Optional[TaskData]:
        """
        Get a specific task based on the task's ID.
        
        Args:
            task_id: The ID for the task
        
        Returns:
            Specific task that matches the ID or None if not found
        """
        return self.get_item(task_id)
