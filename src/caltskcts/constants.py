from enum import Enum

class TaskState(str, Enum):
    NOT_STARTED  = "Not Started"
    IN_PROGRESS  = "In Progress"
    COMPLETED    = "Completed"
    ON_HOLD      = "On Hold"
    CANCELLED    = "Cancelled"

VALID_TASK_STATES = [s.value for s in TaskState]
