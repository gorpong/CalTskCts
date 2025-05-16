"""
Validation utilities for StateManagerBase subclasses.
Contains common validation functions that can be reused across different
item types (Calendar events, Contacts, Tasks, etc.)
"""
from typing import Any, List, Optional, Type, Mapping, Tuple, Union
from datetime import datetime
import re

def validate_required_fields(item: Mapping[str, Any], required_fields: List[str]) -> None:
    """
    Validate that all required fields are present and non-empty.
    
    Args:
        item: The item data to validate
        required_fields: List of field names that are required
    
    Raises:
        ValueError: If a required field is missing or empty
    """
    for field in required_fields:
        if field not in item or not item[field]:
            raise ValueError(f"Missing required field: {field}")


def validate_date_format(date_str: str, date_format: str) -> None:
    """
    Validate that a date string matches the expected format.
    
    Args:
        date_str: Date string to validate
        date_format: Expected date format (e.g. "%m/%d/%Y" or "%m/%d/%Y %H:%M")
    
    Raises:
        ValueError: If date format is invalid
    """
    try:
        datetime.strptime(date_str, date_format)
    except (TypeError, ValueError):
        readable_format = date_format.replace("%m", "MM").replace("%d", "DD").replace("%Y", "YYYY")
        readable_format = readable_format.replace("%H", "HH").replace("%M", "MM")
        raise ValueError(f"Invalid date format. Use {readable_format}")

def validate_numeric_range(
    value: Any, 
    field_name: str, 
    min_value: Optional[float] = None,
    max_value: Optional[float] = None,
    numeric_type: Union[Type[Any], Tuple[Type[Any], ...]] = (int, float)
) -> None:
    """
    Validate that `value` is an instance of `numeric_type` and, if provided, 
    lies between the inclusive [min_value, max_value] range.
    
    Args:
        value: Value to validate
        field_name: Name of the field for error messages
        min_value: Minimum allowed value
        max_value: Maximum allowed value
        numeric_type: Expected numeric type (int or float)
    
    Raises:
        ValueError: If value is not a number or outside range
    """
    if not isinstance(value, numeric_type):
        raise ValueError(f"{field_name} must be a number")
    
    if min_value is not None and value < min_value:
        if max_value is None:
            raise ValueError(f"{field_name} must be a number larger than {min_value}")
        else:
            raise ValueError(f"{field_name} must be a number between {min_value} and {max_value}")
    if max_value is not None and value > max_value:
        if min_value is None:
            raise ValueError(f"{field_name} must be a number less than {max_value}")
        else:
            raise ValueError(f"{field_name} must be a number between {min_value} and {max_value}")

def validate_list_type(value: Any, field_name: str) -> None:
    """
    Validate that a value is a list.
    
    Args:
        value: Value to validate
        field_name: Name of the field for error messages
    
    Raises:
        ValueError: If value is not a list
    """
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a list")


def validate_email_format(email: str) -> None:
    """
    Validate email address format.
    
    Args:
        email: Email address to validate
    
    Raises:
        ValueError: If email format is invalid
    """
    if email and not re.fullmatch(r'^(".*?"|[\w\.+-]+)@[\w\.-]+\.\w{2,}$', email):
        raise ValueError("Invalid email format")


def validate_phone_format(phone: str, field_name: str) -> None:
    """
    Validate phone number format with constraints.
    
    Args:
        phone: Phone number to validate
        field_name: Name of the field for error messages
    
    Raises:
        ValueError: If phone format is invalid or has incorrect number of digits
    """
    if not re.fullmatch(r"^\+?[\d\s\.\-\(\)]+$", phone):
        raise ValueError(f"Invalid phone number format in {field_name}")
    
    # Phone number must have between 7 and 15 digits
    digit_count = len(re.sub(r"\D", "", phone))
    if not (7 <= digit_count <= 15):
        raise ValueError(f"{field_name} must have between 7 and 15 digits")


def validate_enum_value(value: str, allowed_values: List[str], field_name: str) -> None:
    """
    Validate that a string value is in the list of allowed values.
    
    Args:
        value: Value to validate
        allowed_values: List of allowed values
        field_name: Name of the field for error messages
    
    Raises:
        ValueError: If value is not in the allowed values list
    """
    if value not in allowed_values:
        raise ValueError(f"Invalid {field_name}. Must be one of: {', '.join(allowed_values)}")


def validate_condition(condition: bool, error_message: str) -> None:
    """
    Validate a condition and raise an error if it's false.
    
    Args:
        condition: Boolean condition to validate
        error_message: Error message to use if condition is false
    
    Raises:
        ValueError: If condition is false
    """
    if not condition:
        raise ValueError(error_message)
