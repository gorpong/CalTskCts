# src/caltskcts/schemas.py

from pydantic import (
    BaseModel,
    Field,
    ConfigDict,
    constr,
    conint,
    field_validator,
    model_validator,
)
from typing import List, Optional
from datetime import datetime, date
import re

# --- Contact schema ---

PhoneStr = constr(
    pattern=r'^\+?[\d\-\(\)\s\.]+$',  # digits, spaces, hyphens, dots, parentheses, optional leading '+'
)
EmailSimple = constr(
    pattern=r'^(".*?"|[\w\.+-]+)@[\w\.-]+\.\w{2,}$'
)

class ContactModel(BaseModel):
    first_name: constr(min_length=1, strip_whitespace=True)
    last_name:  constr(min_length=1, strip_whitespace=True)
    title:      Optional[str] = None
    company:    Optional[str] = None

    work_phone:   Optional[PhoneStr] = None
    mobile_phone: Optional[PhoneStr] = None
    home_phone:   Optional[PhoneStr] = None

    email: Optional[EmailSimple] = None

    model_config = ConfigDict(
        str_strip_whitespace=True,
        from_attributes=True,   # allows ORM→Pydantic if you pass an ORM instance
    )

    @field_validator("work_phone", "mobile_phone", "home_phone", mode="before")
    @classmethod
    def check_phone_digits(cls, v, info):
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
    def check_email_basic(cls, v, info):
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
    title: constr(min_length=1, strip_whitespace=True)
    date: datetime                     # Pydantic will parse via validator
    duration: conint(strict=True, gt=0)  # positive integer
    users: List[constr(min_length=1, strip_whitespace=True)]  # list of non‐empty strings

    model_config = ConfigDict(
        str_strip_whitespace=True,
        from_attributes=True,
    )

    @field_validator("date", mode="before")
    @classmethod
    def parse_date_string(cls, v):
        if isinstance(v, str):
            try:
                return datetime.strptime(v, "%m/%d/%Y %H:%M")
            except ValueError:
                raise ValueError("Invalid date format. Use MM/DD/YYYY HH:MM")
        if isinstance(v, datetime):
            return v
        raise ValueError("Invalid date type; must be string or datetime")

    @model_validator(mode="after")
    @classmethod
    def format_date_output(cls, values):
        # Convert the 'date' back into the same string format when serialized
        date_obj = values.get("date")
        if isinstance(date_obj, datetime):
            values["date"] = date_obj.strftime("%m/%d/%Y %H:%M")
        return values


# --- Task schema ---

class TaskModel(BaseModel):
    title: constr(min_length=1, strip_whitespace=True)
    desc: Optional[str] = None
    dueDate: date                      # Pydantic will parse via validator
    progress: conint(ge=0, le=100)     # integer 0–100
    state: constr(min_length=1, strip_whitespace=True)

    model_config = ConfigDict(
        str_strip_whitespace=True,
        from_attributes=True,
    )

    @field_validator("dueDate", mode="before")
    @classmethod
    def parse_due_date_string(cls, v):
        if isinstance(v, str):
            try:
                return datetime.strptime(v, "%m/%d/%Y").date()
            except ValueError:
                raise ValueError("Invalid date format. Use MM/DD/YYYY")
        if isinstance(v, date):
            return v
        raise ValueError("Invalid date type; must be string or date")

    @model_validator(mode="after")
    @classmethod
    def sync_progress_state(cls, values):
        """
        Enforce or auto‐fill the relationship:
          - If both 'progress' and 'state' provided → ensure consistency.
          - If only one provided → set the other appropriately when needed.
        """
        prog = values.get("progress")
        st = values.get("state")

        # If both provided, enforce consistency
        if prog is not None and st is not None:
            if prog == 100 and st != "Completed":
                raise ValueError("If progress=100, state must be 'Completed'")
            if st == "Completed" and prog < 100:
                raise ValueError("If state='Completed', progress must be 100")
            return values

        # If only progress=100 → auto‐fill state
        if prog == 100 and st is None:
            values["state"] = "Completed"
            return values

        # If only state="Completed" → auto‐fill progress=100
        if st == "Completed" and prog is None:
            values["progress"] = 100
            return values

        return values
