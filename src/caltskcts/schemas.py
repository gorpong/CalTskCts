from pydantic import (
    BaseModel,
    ConfigDict,
    confloat,
    constr,
    conint,
    field_validator,
    model_validator,
)
from typing import List, Optional
from datetime import datetime, date
import re
from caltskcts.constants import VALID_TASK_STATES

# --- Contact schema ---

PhoneStr = constr(
    pattern=r'^\+?[\d\-\(\)\s\.]+$',  # digits, spaces, hyphens, dots, parentheses, optional leading '+'
)
EmailSimple = constr(
    pattern=r'^(".*?"|[\w\.+-]+)@[\w\.-]+\.\w{2,}$'
)

class ContactModel(BaseModel):
    first_name:   constr(min_length=1, strip_whitespace=True) # type: ignore
    last_name:    constr(min_length=1, strip_whitespace=True) # type: ignore
    title:        Optional[str] = None
    company:      Optional[str] = None
    work_phone:   Optional[PhoneStr] = None # type: ignore
    mobile_phone: Optional[PhoneStr] = None # type: ignore
    home_phone:   Optional[PhoneStr] = None # type: ignore

    email: Optional[EmailSimple] = None # type: ignore

    model_config = ConfigDict(
        str_strip_whitespace=True,
        from_attributes=True,   # allows ORM→Pydantic if you pass an ORM instance
    )

    @field_validator("work_phone", "mobile_phone", "home_phone", mode="before")
    @classmethod
    def check_phone_digits(cls, v, info) -> str:
        """
        If a phone string is provided (already matched PhoneStr's pattern),
        ensure it has 7-15 digits once non-digits are stripped.
        """
        if v is None:
            return v
        # Count digits only
        digits = re.sub(r"\D", "", v)
        if not (7 <= len(digits) <= 15):
            raise ValueError(f"{info.field_name} must have between 7 and 15 digits")
        return v

    @field_validator("email", mode="before")
    @classmethod
    def check_email_basic(cls, v, info) -> str:
        """
        If an email string is provided, ensure it matches the simple regex.
        (The EmailSimple constr above already enforces the same pattern,
        but this double-checks or can provide a custom message.)
        """
        if v is None:
            return v
        return v


# --- Calendar/Event schema ---

class EventModel(BaseModel):
    title:    constr(min_length=1, strip_whitespace=True)
    date:     Optional[datetime] = None
    duration: Optional[conint(strict=True, gt=0)] = None
    users:    Optional[List[constr(min_length=1, strip_whitespace=True)]] = None

    model_config = ConfigDict(
        str_strip_whitespace=True,
        from_attributes=True,
    )

    @field_validator("date", mode="before")
    @classmethod
    def parse_date_string(cls, v) -> datetime:
         if isinstance(v, str):
            try:
                return datetime.strptime(v, "%m/%d/%Y %H:%M")
            except ValueError:
                raise ValueError("Invalid date format. Use MM/DD/YYYY HH:MM")
        if isinstance(v, datetime):
            return v
        raise ValueError("Invalid date type; must be string or datetime")


# --- Task schema ---

class TaskModel(BaseModel):
    title:    constr(min_length=1, strip_whitespace=True) # type: ignore
    desc:     Optional[str] = None
    dueDate:  Optional[date] = None
    progress: Optional[confloat(ge=0, le=100)] = None     # type: ignore
    state:    Optional[constr(min_length=1, strip_whitespace=True)] = None # type: ignore

    model_config = ConfigDict(
        str_strip_whitespace=True,
        from_attributes=True,
    )

    @field_validator("dueDate", mode="before")
    @classmethod
    def parse_due_date(cls, v) -> date:
        if isinstance(v, str):
            try:
                return datetime.strptime(v, "%m/%d/%Y").date()
            except ValueError:
                raise ValueError("Invalid date format. Use MM/DD/YYYY")
        elif isinstance(v, date):
            return v
        elif v is None:
            return v
        raise ValueError("Invalid date type; must be string or date")

    @field_validator("state", mode="before")
    @classmethod
    def check_valid_state(cls, v) -> str:
        """
        Enforce that state is a valid state
        """
        if isinstance(v, str):
            if v not in VALID_TASK_STATES:
                raise ValueError(f"Invalid state. Must be one of {', '.join(VALID_TASK_STATES)}")
            else:
                return v
        elif v is None:
            return v
        raise ValueError(f"Invalid state type({type(v)}); must be string")

    @model_validator(mode="after")
    @classmethod
    def sync_progress_state(cls, model_instance: "TaskModel") -> "TaskModel":
        """
        Enforce or auto-fill the relationship:
          - If both 'progress' and 'state' provided → ensure consistency.
          - If only one provided → set the other appropriately when needed.
        """
        prog = model_instance.progress
        st   = model_instance.state

        if prog == 100 and st != "Completed":
            model_instance.state = "Completed"
        if st == "Completed" and prog != 100:
            model_instance.progress = 100

        return model_instance
