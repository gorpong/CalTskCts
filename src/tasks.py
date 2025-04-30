from typing import Dict, List, Optional
from datetime import datetime
import re
from state_manager import StateManager


class Tasks:
    """The tsk.* functions for managing lists of tasks and their due-dates, status, percentage complete"""
    
    def __init__(self, state_file: str):
        self.state_manager = StateManager(state_file)

    @property
    def tasks(self) -> Dict[str, Dict]:
        """Access tasks data through state manager"""
        return self.state_manager.state

    def add_task(
        self,
        task_id: Optional[int] = None,
        title: str = "",
        description: str = "",
        due_date: Optional[str] = None,
        progress: Optional[float] = 0.0,
        state: Optional[str] = "Not Started",
    ) -> str:
        """Add a new task."""
        if not task_id:
            task_id = self.state_manager.get_next_id()  # Assign next available ID
        task_id_str = str(task_id)  # Normalize to string
        
        if task_id_str in self.tasks:
            raise ValueError(f"Task with ID {task_id} already exists.")
        
        task_data = {
            "title": title,
            "desc": description,
            "dueDate": due_date,
            "progress": progress,
            "state": state,
        }
        self.state_manager.add_item(task_id, task_data)
        return f"Task {task_id} added"
    
    def update_task(self, 
            task_id: int, 
            title: Optional[str] = None, 
            due_date: Optional[str] = None, 
            progress: Optional[float] = None, 
            state: Optional[str] = None, 
            description: Optional[str] = None
    ) -> str:
        """Update an existing task."""
        task_id_str = str(task_id)  # Normalize to string
        if task_id_str not in self.tasks:
            raise ValueError(f"Task with ID {task_id} does not exist.")
        
        updates = {}
        if title is not None:
            updates["title"] = title
        if due_date is not None:
            updates["dueDate"] = due_date
        if progress is not None:
            updates["progress"] = progress
            if progress == 100.0:
                updates["state"] = "Completed"
        if description is not None:
            updates["desc"] = description
        if state is not None:
            updates["state"] = state
            if state.lower() == "completed":
                updates["progress"] = 100.0
        
        self.state_manager.update_item(task_id, updates)
        return f"Task {task_id} updated"

    def delete_task(self, task_id: int) -> str:
        """Delete a task."""
        if self.state_manager.delete_item(task_id):
            return f"Task {task_id} deleted"
        else:
            raise ValueError(f"Event with ID {task_id} does not exist.")

    def list_tasks(self) -> Dict[int, Dict]:
        """List all tasks with integer keys."""
        return self.state_manager.list_items()

    def get_task(self, task_id: int) -> Dict:
        task_data = self.state_manager.get_item(task_id)
        if task_data:
            return task_data
        else:
            return f"Task {task_id} does not exist"
        
    def get_tasks_due_today(self, today: Optional[str] = None) -> List[Dict]:
        """Retrieve all tasks due today or before today."""
        if not today:
            today = datetime.now().strftime("%m/%d/%Y")
        today_date = datetime.strptime(today, "%m/%d/%Y")
        return [
            {"task_id": task_id, **task}
                for task_id, task in self.tasks.items()
                if task["dueDate"]
                    and datetime.strptime(task["dueDate"], "%m/%d/%Y") <= today_date
                    and task["state"].lower() != "completed"
        ]

    def get_tasks_due_tomorrow(self) -> List[Dict]:
        """Retrieve all tasks due tomorrow."""
        tomorrow = (datetime.now() + datetime.timedelta(days=1)).strftime("%m/%d/%Y")
        return [
            {"task_id": task_id, **task}
                for task_id, task in self.tasks.items()
                if task["dueDate"] == tomorrow
        ]

    def get_tasks_due_on(self, date: str) -> List[Dict]:
        """Retrieve all tasks due on a specific day."""
        due_date = datetime.strptime(date, "%m/%d/%Y")
        return [
            {"task_id": task_id, **task}
                for task_id, task in self.tasks.items() 
                if datetime.strptime(task["dueDate"], "%m/%d/%Y") == due_date
                    and task["state"].lower() != "completed"
        ]
    
    def get_tasks_due_on_or_before(self, date: str) -> List[Dict]:
        """Retrieve all tasks due on or before a specific day."""
        due_date = datetime.strptime(date, "%m/%d/%Y")
        return [
            {"task_id": task_id, **task}
                for task_id, task in self.tasks.items()
                if datetime.strptime(task["dueDate"], "%m/%d/%Y") <= due_date
                    and task["state"].lower() != "completed"
        ]

    def get_tasks_with_progress(
        self, 
        min_progress: Optional[float] = None, 
        max_progress: Optional[float] = None
    ) -> List[Dict]:
        """Retrieve tasks filtered by progress."""
        return [
            {"task_id": task_id, **task}
                for task_id, task in self.tasks.items()
                if (min_progress is None or task["progress"] >= min_progress)
                and (max_progress is None or task["progress"] <= max_progress)
        ]

    def get_tasks_by_state(self, state: str = "Not Started") -> List[Dict]:
        """Retrieve all tasks with a specific state or regex states."""
        try:
            query_regex = re.compile(state, re.IGNORECASE)
        except re.error as e:
            raise ValueError(f"Invalid regex pattern: {e}")
        return [
            {"task_id": task_id, **task}
            for task_id, task in self.tasks.items()
            if query_regex.search(task.get("state", "") or "")
        ]
