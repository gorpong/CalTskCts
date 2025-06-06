from typing import Dict, List, Optional, Any, MutableMapping, Tuple
from datetime import datetime, timedelta
from sqlalchemy import Integer, String, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column
from pydantic import ValidationError
from caltskcts.state_manager import Base, StateManagerBase
from caltskcts.schemas import EventModel

class EventData(Base):
    __tablename__ = "calendars"
    
    id:       Mapped[int]       = mapped_column(Integer, primary_key=True)
    title:    Mapped[str]       = mapped_column(String, nullable=False)
    date:     Mapped[datetime]  = mapped_column(DateTime, nullable=False)
    duration: Mapped[int]       = mapped_column(Integer, nullable=False)
    users:    Mapped[List[str]] = mapped_column(JSON, nullable=False)

class Calendar(StateManagerBase[EventData]):
    """Manages calendar events and scheduling."""
    
    Model = EventData

    def _validate_item(self, item: MutableMapping[str, Any]) -> bool:
        """
        Validate event data before adding/updating. Uses Pydantic for validation
        
        Args:
            item: Event data to validate
            
        Returns:
            True if valid
            
        Raises:
            ValueError: If validation fails
        """
        self.logger.debug("Calling _validate_item")
        try:
            EventModel(**item)
        except ValidationError as ve:
            raise ValueError(str(ve))
        self.logger.debug("Item validated")
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
            
        event_data: MutableMapping[str, Any] = {
            "title": title,
            "date": date,
            "duration": duration,
            "users": users or []
        }
        
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
            
        updates: MutableMapping[str, Any] = {
            k: v 
            for k, v in { # type: ignore
                "title": title,
                "date": date,
                "duration": duration,
                "users": users
            }.items()
            if v is not None
        }

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
        results: List[Dict[str, Any]] = []
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
        
        results: List[Dict[str, Any]] = []
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
            duration_minutes: Required duration in minutes
            
        Returns:
            Available time slot (MM/DD/YYYY HH:MM)
        """
        start = datetime.strptime(start_datetime, "%m/%d/%Y %H:%M")
        
        # Get all booked times sorted by start time
        booked_slots: List[Tuple[datetime, datetime]] = []
        for event in self.items.values():
            event_start = datetime.strptime(event["date"], "%m/%d/%Y %H:%M")
            event_end = event_start + timedelta(minutes=event["duration"])
            booked_slots.append((event_start, event_end))
            
        booked_slots.sort()  # Sort by start time
        
        while True:
            conflict_found = False
            proposed_end = start + timedelta(minutes=duration_minutes)
            
            for event_start, event_end in booked_slots:
                if start < event_end and proposed_end > event_start:
                    # Conflict found, move start to end of this event
                    start = event_end
                    conflict_found = True
                    break
                
            if not conflict_found:
                return start.strftime("%m/%d/%Y %H:%M")

    def list_events(self) -> Dict[int, Any]:
        """
        List all calendar events.
        
        Returns:
            Dictionary of all events with integer keys
        """
        return self.list_items()

    def get_event(self, event_id: int) -> Optional[Dict[int, Any]]:
        """
        Get a specific event based on the event's ID.
        
        Args:
            event_id: The ID for the calendar event
        
        Returns:
            Specific calendar event that matches the ID or None if not found
        """
        return self.get_item(event_id)
