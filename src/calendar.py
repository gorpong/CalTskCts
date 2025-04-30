from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from state_manager import StateManager


class Calendar:
    """The cal.* functions for managing events on a calendar"""

    def __init__(self, state_file: str):
        self.state_manager = StateManager(state_file)

    @property
    def events(self) -> Dict[str, Dict]:
        """Access events data through state manager"""
        return self.state_manager.state

    def add_event(
        self,
        event_id: Optional[int] = None,
        title: str = "",
        date: str = "",
        duration: int = 30,
        users: Optional[List[str]] = None,
    ) -> str:
        """
        Add an event to the calendar, it will allow multiple bookings for a
        particular time period so you should first call the cal.find_next_available
        function to find an open slot
        
        Args:
            event_id (int): The new event_id you want to add, if there is already an event with that id, this will fail and you should use cal.update_event, so normal usage is to not include this and let the system determine its own next ID
            title (str): The title of the event, what others will see when they get an invitation
            date (str): The date and time in format 'MM/DD/YYYY hh:mm' format for the start of the meeting
            duration (int): The number of minutes for the meeting you want to schedule
            users (list): The users to add to the invitation list for the meeting, if none given then just creates a block of time without sending invitations to anyone
        
        """
        if not event_id:
            event_id = self.state_manager.get_next_id()  # Assign next available ID
        event_id = str(event_id)  # Normalize to string
        
        if event_id in self.events:
            raise ValueError(f"Event with ID {event_id} already exists.")
        
        event_data = {"title": title, "date": date, "duration": duration, "users": users or []}
        self.state_manager.add_item(int(event_id), event_data)
        return f"Event {event_id} Added"
    
    def update_event(
        self,
        event_id: int,
        title: Optional[str] = None,
        date: Optional[str] = None,
        duration: Optional[int] = None,
        users: Optional[List[str]] = None,
    ) -> str:
        """Update an existing event."""
        event_id_str = str(event_id)  # Normalize to string
        if event_id_str not in self.events:
            raise ValueError(f"Event with ID {event_id} does not exist.")
        
        updates = {}
        if title is not None:
            updates["title"] = title
        if date is not None:
            updates["date"] = date
        if duration is not None:
            updates["duration"] = duration
        if users is not None:
            updates["users"] = users
            
        self.state_manager.update_item(event_id, updates)
        return f"Event {event_id} updated"

    def delete_event(self, event_id: int) -> str:
        """Delete an event."""
        if self.state_manager.delete_item(event_id):
            return f"Event {event_id} deleted"
        else:
            raise ValueError(f"Event with ID {event_id} does not exist.")

    def list_events(self) -> Dict[int, Dict]:
        """List all events with integer keys."""
        return self.state_manager.list_items()

    def get_event(self, event_id: int) -> Dict:
        event_data = self.state_manager.get_item(event_id)
        if event_data:
            return event_data
        else:
            return f"Event {event_id} not found"
        
    def get_events_by_date(self, date: str) -> List[Dict]:
        """Find all events on a specific date."""
        return [
            {"event_id": event_id, **event}
            for event_id, event in self.events.items()
            if event["date"].startswith(date)  # Match date portion
        ]
    
    def get_events_between(self, start_datetime: str, end_datetime: str) -> List[Dict]:
        """Get all of the events (inclusive) between two dates."""
        # Ensure datetime strings include time; add defaults if missing
        if len(start_datetime.split()) == 1:  # If only date is provided
            start_datetime += " 00:00"
        if len(end_datetime.split()) == 1:  # If only date is provided
            end_datetime += " 23:59"

        # Convert start and end datetimes
        start, end = map(lambda dt: datetime.strptime(dt, "%m/%d/%Y %H:%M"), [start_datetime, end_datetime])

        # Filter events using pre-parsed datetimes
        return [
            {"event_id": event_id, **event}
            for event_id, event in self.events.items()
            if start <= datetime.strptime(event["date"], "%m/%d/%Y %H:%M") <= end
        ]

    def find_next_available(self, start_datetime: str, duration_minutes: int = 30) -> Optional[Tuple[str, str]]:
        """Find the next available time slot of the given duration."""
        # Convert start_datetime to datetime object
        start = datetime.strptime(start_datetime, "%m/%d/%Y %H:%M")

        # Collect all booked times
        booked_slots = sorted(
            [
                (datetime.strptime(event["date"], "%m/%d/%Y %H:%M"), event["duration"])
                for event in self.events.values()
            ]
        )

        # Iterate to find the next available slot
        for booked, booked_duration in booked_slots:
            if booked >= start:
                # Calculate the end time of the current event
                booked_end = booked + timedelta(minutes=booked_duration)
                # Check if there's a gap for the required duration
                if (booked - start).total_seconds() >= duration_minutes * 60:
                    return (
                        start.strftime("%m/%d/%Y %H:%M")
                    )
                # Move start to after this booked slot
                start = booked_end

        # If no booked slots conflict, return the next available slot
        return (start.strftime("%m/%d/%Y %H:%M"))
