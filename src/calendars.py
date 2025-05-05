from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from state_manager import StateManagerBase
import re
import os


class EventData(Dict[str, Any]):
    """Type for event data with expected fields."""
    title: str
    date: str  # "MM/DD/YYYY HH:MM" format
    duration: int  # minutes
    users: List[str]


class Calendar(StateManagerBase[EventData]):
    """Manages calendar events and scheduling."""
    
    def _validate_item(self, item: Dict[str, Any]) -> bool:
        """
        Validate event data before adding/updating.
        
        Args:
            item: Event data to validate
            
        Returns:
            True if valid
            
        Raises:
            ValueError: If validation fails
        """
        # Check required fields
        if "title" not in item:
            raise ValueError("Title is required")
            
        # Validate date and time format
        if "date" in item:
            try:
                datetime.strptime(item["date"], "%m/%d/%Y %H:%M")
            except ValueError:
                raise ValueError("Invalid date format. Use MM/DD/YYYY HH:MM")
        
        # Validate duration
        if "duration" in item:
            if not isinstance(item["duration"], int) or item["duration"] <= 0:
                raise ValueError("Duration must be a positive integer")
        
        # Validate users list
        if "users" in item and not isinstance(item["users"], list):
            raise ValueError("Users must be a list")
            
        return True

    def add_event(
        self,
        title: str = "",
        date: str = "",
        duration: int = 30,
        users: Optional[List[str]] = None,
        event_id: Optional[int] = None,
    ) -> str:
        """
        Add an event to the calendar.
        
        Args:
            title: Event title
            date: Event date and time (MM/DD/YYYY HH:MM)
            duration: Duration in minutes
            users: List of users to invite
            event_id: Optional specific ID to use
            
        Returns:
            Success message
            
        Raises:
            ValueError: If event_id exists or validation fails
        """
        if not event_id:
            event_id = self._get_next_id()
            
        event_data = {
            "title": title,
            "date": date,
            "duration": duration,
            "users": users or []
        }
        
        # Validate before adding
        self._validate_item(event_data)
        
        if self.add_item(event_id, event_data):
            return f"Event {event_id} Added"
        else:
            raise ValueError(f"Event with ID {event_id} already exists.")
            
    def update_event(
        self,
        event_id: int,
        title: Optional[str] = None,
        date: Optional[str] = None,
        duration: Optional[int] = None,
        users: Optional[List[str]] = None,
    ) -> str:
        """
        Update an existing event.
        
        Args:
            event_id: ID of event to update
            title: New title
            date: New date and time
            duration: New duration
            users: New user list
            
        Returns:
            Success message
            
        Raises:
            ValueError: If event doesn't exist or validation fails
        """
        current_data = self.get_item(event_id)
        if not current_data:
            raise ValueError(f"Event with ID {event_id} does not exist.")
            
        updates = {
            k: v for k, v in {
                "title": title,
                "date": date,
                "duration": duration,
                "users": users
            }.items() if v is not None
        }
        
        # Create merged data for validation
        merged_data = {**current_data, **updates}
        self._validate_item(merged_data)
        
        if self.update_item(event_id, updates):
            return f"Event {event_id} updated"
        else:
            raise ValueError(f"Failed to update event {event_id}")
    
    def delete_event(self, event_id: int) -> str:
        """
        Delete an event.
        
        Args:
            event_id: ID of event to delete
            
        Returns:
            Success message
            
        Raises:
            ValueError: If event doesn't exist
        """
        if self.delete_item(event_id):
            return f"Event {event_id} deleted"
        else:
            raise ValueError(f"Event with ID {event_id} does not exist.")
    
    def get_events_by_date(self, date: str) -> List[Dict[str, Any]]:
        """
        Find all events on a specific date.
        
        Args:
            date: Date in MM/DD/YYYY format
            
        Returns:
            List of events on that date
        """
        results = []
        for event_id, event in self.items.items():
            if event["date"].startswith(date):
                results.append({"event_id": int(event_id), **event})
        return results
    
    def get_events_between(self, start_datetime: str, end_datetime: str) -> List[Dict[str, Any]]:
        """
        Get all events between two dates (inclusive).
        
        Args:
            start_datetime: Start date/time (MM/DD/YYYY [HH:MM])
            end_datetime: End date/time (MM/DD/YYYY [HH:MM])
            
        Returns:
            List of events in the date range
        """
        # Add default times if not provided
        if len(start_datetime.split()) == 1:
            start_datetime += " 00:00"
        if len(end_datetime.split()) == 1:
            end_datetime += " 23:59"
            
        start = datetime.strptime(start_datetime, "%m/%d/%Y %H:%M")
        end = datetime.strptime(end_datetime, "%m/%d/%Y %H:%M")
        
        results = []
        for event_id, event in self.items.items():
            event_time = datetime.strptime(event["date"], "%m/%d/%Y %H:%M")
            if start <= event_time <= end:
                results.append({"event_id": int(event_id), **event})
        
        return results
    
    def find_next_available(self, start_datetime: str, duration_minutes: int = 30) -> str:
        """
        Find the next available time slot.
        
        Args:
            start_datetime: Starting point to search from (MM/DD/YYYY HH:MM)
            duration_minutes: Required duration
            
        Returns:
            Available time slot (MM/DD/YYYY HH:MM)
        """
        start = datetime.strptime(start_datetime, "%m/%d/%Y %H:%M")
        
        # Get all booked times sorted by start time
        booked_slots = []
        for event in self.items.values():
            event_start = datetime.strptime(event["date"], "%m/%d/%Y %H:%M")
            event_duration = event["duration"]
            booked_slots.append((event_start, event_duration))
            
        booked_slots.sort()  # Sort by start time
        
        # Check each booked slot for gaps
        for booked_start, booked_duration in booked_slots:
            if booked_start >= start:
                gap_duration = (booked_start - start).total_seconds() / 60
                if gap_duration >= duration_minutes:
                    return start.strftime("%m/%d/%Y %H:%M")
                start = booked_start + timedelta(minutes=booked_duration)
        
        # If we get here, return the last available time
        return start.strftime("%m/%d/%Y %H:%M")

    def list_events(self) -> Dict[int, Any]:
        """
        List all calendar events.
        
        Returns:
            List of all tasks
        """
        return self.list_items()

    def get_event(self, event_id: int) -> Dict[int, Any]:
        """
        Get a specific event based on the event's ID.
        
        Args:
            event_id: The ID for the calendar event
        
        Returns:
            Specific calendar event that matches the ID
        """
        return self.get_item(event_id)