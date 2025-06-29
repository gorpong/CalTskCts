from typing import Dict, List, Optional, Any, MutableMapping
from datetime import datetime, date
from sqlalchemy import Integer, Float, String, Date
from sqlalchemy.orm import Mapped, mapped_column
from pydantic import ValidationError
from caltskcts.state_manager import Base, StateManagerBase
from caltskcts.schemas import TaskModel

class TaskData(Base):
    __tablename__ = "tasks"

    id:       Mapped[int]            = mapped_column(Integer, primary_key=True)
    title:    Mapped[str]            = mapped_column(String,  nullable=False)
    desc:     Mapped[Optional[str]]  = mapped_column(String,  nullable=True)
    dueDate:  Mapped[Optional[date]] = mapped_column(Date,    nullable=True)
    progress: Mapped[float]          = mapped_column(Float,   nullable=False, default=0.0)
    state:    Mapped[str]            = mapped_column(String,  nullable=False)
    
class Tasks(StateManagerBase[TaskData]):
    """Manages tasks and their due dates, status, and completion progress."""
    
    Model = TaskData
    
    def _validate_item(self, item: MutableMapping[str, Any]) -> bool:
        """
        Validate task data before adding/updating.
        
        Args:
            item: Task data to validate
            
        Returns:
            True if valid
            
        Raises:
            ValueError: If validation fails
        """
        self.logger.debug("Calling _validate_item")
        try:
            model = TaskModel(**item)
        except ValidationError as ve:
            self.logger.error("Validation Error!", str(ve))
            raise ValueError(str(ve))
        normalized = model.model_dump()
        item.clear()
        item.update(normalized)
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
        if  task_id is None:
            task_id = self._get_next_id()
        
        task_data: MutableMapping[str, Any] = {
            "title": title,
            "desc": description,
            "dueDate": due_date,
            "progress": progress,
            "state": state,
        }
        
        if self.add_item(task_id, task_data): # type: ignore
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
        
        updates: Dict[str, Any] = {
            k: v for k, v in {
                "title":    title,
                "desc":     description,
                "dueDate":  due_date,
                "progress": progress,
                "state":    state,
            }.items() if v is not None
        }
        merged_data = {**current_data, **updates}
        try:
            validated_data = TaskModel(**merged_data).model_dump()
        except ValidationError as ve:
            raise ValueError(str(ve))

        if self.update_item(task_id, validated_data):  # type: ignore
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

    def get_tasks_due_today(self, today: Optional[str] = None) -> List[Dict[str, Any]]:
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
        
        results: List[Any] = []
        for task_id, task in self.items.items():
            if not task["dueDate"] or task["state"] == "Completed":
                continue
                
            task_date = datetime.strptime(task["dueDate"], "%m/%d/%Y")
            if task_date.date() <= today_date.date():
                results.append({"task_id": int(task_id), **task})
                
        return results

    def get_tasks_due_on(self, date: str) -> List[Dict[str, Any]]:
        """
        Get all tasks due on a specific date.
        
        Args:
            date: Date in MM/DD/YYYY format
            
        Returns:
            List of tasks
        """
        target_date = datetime.strptime(date, "%m/%d/%Y")
        
        results: List[Any] = []
        for task_id, task in self.items.items():
            if not task["dueDate"] or task["state"] == "Completed":
                continue
                
            task_date = datetime.strptime(task["dueDate"], "%m/%d/%Y")
            if task_date.date() == target_date.date():
                results.append({"task_id": int(task_id), **task})
                
        return results

    def get_tasks_due_on_or_before(self, date: str) -> List[Dict[str, Any]]:
        """
        Get all tasks due on or before a date.
        
        Args:
            date: Date in MM/DD/YYYY format
            
        Returns:
            List of tasks
        """
        target_date = datetime.strptime(date, "%m/%d/%Y")
        
        results: List[Any] = []
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
    ) -> List[Dict[str, Any]]:
        """
        Get tasks filtered by progress range.
        
        Args:
            min_progress: Minimum progress value
            max_progress: Maximum progress value
            
        Returns:
            List of tasks within the progress range
        """
        results: List[Any] = []
        for task_id, task in self.items.items():
            progress = task["progress"]
            if min_progress <= progress <= max_progress:
                results.append({"task_id": int(task_id), **task})
                
        return results

    def get_tasks_by_state(self, state: str = "Not Started") -> List[Dict[str, Any]]:
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
    
    def get_task(self, task_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a specific task based on the task's ID.
        
        Args:
            task_id: The ID for the task
        
        Returns:
            Specific task that matches the ID or None if not found
        """
        return self.get_item(task_id)
