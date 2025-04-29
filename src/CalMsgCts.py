import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import re

class Calendar:
    """ The cal.* functions for managing events on a calendar"""

    def __init__(self, state_file: str):
        self.state_file = state_file
        self.events: Dict[str, Dict] = self.__load_state()

    def __load_state(self) -> Dict[str, Dict]:
        """Load events from the state file."""
        try:
            with open(self.state_file, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}  # No state file, start with empty calendar

    def ____save_state(self) -> None:
        """Save events to the state file."""
        with open(self.state_file, "w") as f:
            json.dump(self.events, f, indent=4)

    def __get_next_id(self) -> int:
        """Get the next available ID for an event."""
        if not self.events:
            return 1
        return max(int(event_id) for event_id in self.events.keys()) + 1

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
            event_id = self.__get_next_id()  # Assign next available ID
        event_id = str(event_id)  # Normalize to string
        if event_id in self.events:
            raise ValueError(f"Event with ID {event_id} already exists.")
        self.events[event_id] = {"title": title, "date": date, "duration": duration, "users": users or []}
        self.____save_state()
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
        event_id = str(event_id)  # Normalize to string
        if event_id not in self.events:
            raise ValueError(f"Event with ID {event_id} does not exist.")
        if title:
            self.events[event_id]["title"] = title
        if date:
            self.events[event_id]["date"] = date
        if duration:
            self.events[event_id]["duration"] = duration
        if users:
            self.events[event_id]["users"] = users
        self.____save_state()
        return f"Event {event_id} updated"

    def delete_event(self, event_id: int) -> str:
        """Delete an event."""
        event_id = str(event_id)  # Normalize to string
        if event_id in self.events:
            del self.events[event_id]
            self.____save_state()
        else:
            raise ValueError(f"Event with ID {event_id} does not exist.")
        return f"Event {event_id} deleted"

    def list_events(self) -> Dict[int, Dict]:
        """List all events with integer keys."""
        return {int(event_id): details for event_id, details in self.events.items()}

    def get_event(self, event_id: int) -> Dict:
        event_id = str(event_id)
        if event_id in self.events:
            return self.events[event_id]
        else:
            return f"Event {event_id} not found"
        
    def get_events_by_date(self, date: str) -> List[Dict]:
        """Find all events on a specific date."""
        return [
            {"event_id": event_id, **event}
            for event_id, event in self.events.items()
            if event["date"].startswith(date)  # Match date portion
        ]
        return events_on_date
    
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

class Tasks:
    """The tsk.* functions for managing lists of tasks and their due-dates, status, percentage complete"""
    
    def __init__(self, state_file: str):
        self.state_file = state_file
        self.tasks: Dict[str, Dict] = self.__load_state()

    def __load_state(self) -> Dict[str, Dict]:
        """Load tasks from the state file."""
        try:
            with open(self.state_file, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}  # No state file, start with empty calendar

    def ____save_state(self) -> None:
        """Save tasks to the state file."""
        with open(self.state_file, "w") as f:
            json.dump(self.tasks, f, indent=4)

    def __get_next_id(self) -> int:
        """Get the next available ID for a task."""
        if not self.tasks:
            return 1
        return max(int(task_id) for task_id in self.tasks.keys()) + 1

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
            task_id = self.__get_next_id()  # Assign next available ID
        task_id = str(task_id)  # Normalize to string
        if task_id in self.tasks:
            raise ValueError(f"Task with ID {task_id} already exists.")
        self.tasks[task_id] = {
            "title": title,
            "desc": description,
            "dueDate": due_date,
            "progress": progress,
            "state": state,
        }
        self.____save_state()
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
        task_id = str(task_id)  # Normalize to string
        if task_id not in self.tasks:
            raise ValueError(f"Task with ID {task_id} does not exist.")
        if title:
            self.tasks[task_id]["title"] = title
        if due_date:
            self.tasks[task_id]["dueDate"] = due_date
        if progress:
            self.tasks[task_id]["progress"] = progress
            if progress == 100.0:
                self.tasks[task_id]["state"] = "Completed"
        if description:
            self.tasks[task_id]["desc"] = description
        if state:
            self.tasks[task_id]["state"] = state
            if state.lower() == "completed":
                self.tasks[task_id]["progress"] = 100.0
        self.____save_state()
        return f"Task {task_id} updated"

    def delete_task(self, task_id: int) -> str:
        """Delete a task."""
        task_id = str(task_id)  # Normalize to string
        if task_id in self.tasks:
            del self.tasks[task_id]
            self.____save_state()
        else:
            raise ValueError(f"Event with ID {task_id} does not exist.")
        return f"Task {task_id} deleted"

    def list_tasks(self) -> Dict[int, Dict]:
        """List all tasks with integer keys."""
        return {int(task_id): details for task_id, details in self.tasks.items()}

    def get_task(self, task_id: int) -> Dict:
        task_id = str(task_id)
        if task_id in self.tasks:
            return self.tasks[task_id]
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
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%m/%d/%Y")
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

class Contacts:
    """The ctc.* functions for managing lists of contacts and information such as email, phone numbers, etc."""
    
    def __init__(self, state_file: str):
        self.state_file = state_file
        self.contacts: Dict[str, Dict] = self.__load_state()

    def __load_state(self) -> Dict[str, Dict]:
        """Load contacts from the state file."""
        try:
            with open(self.state_file, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}  # No state file, start with empty contacts

    def __save_state(self) -> None:
        """Save contacts to the state file."""
        with open(self.state_file, "w") as f:
            json.dump(self.contacts, f, indent=4)

    def __get_next_id(self) -> int:
        """Get the next available ID for a contact."""
        if not self.contacts:
            return 1
        return max(int(contact_id) for contact_id in self.contacts.keys()) + 1

    def add_contact(
        self,
        contact_id: Optional[int] = None,
        first_name: str = "",
        last_name: str = "",
        title: Optional[str] = None,
        company: Optional[str] = None,
        work_phone: Optional[str] = None,
        mobile_phone: Optional[str] = None,
        home_phone: Optional[str] = None,
        email: Optional[str] = None,
    ) -> str:
        """Add a new contact."""
        if not contact_id:
            contact_id = self.__get_next_id()  # Assign next available ID
        contact_id = str(contact_id)  # Normalize to string
        if contact_id in self.contacts:
            raise ValueError(f"Contact with ID {contact_id} already exists.")
        self.contacts[contact_id] = {
            "first_name": first_name,
            "last_name": last_name,
            "company": company,
            "title": title,
            "work_phone": work_phone,
            "mobile_phone": mobile_phone,
            "home_phone": home_phone,
            "email": email,
        }
        self.__save_state()
        return f"Contact {contact_id} added"

    def update_contact(
        self,
        contact_id: int,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        company: Optional[str] = None,
        title: Optional[str] = None,
        work_phone: Optional[str] = None,
        mobile_phone: Optional[str] = None,
        home_phone: Optional[str] = None,
        email: Optional[str] = None,
    ) -> str:
        """Update an existing contact."""
        contact_id = str(contact_id)  # Normalize to string
        if contact_id not in self.contacts:
            raise ValueError(f"Contact with ID {contact_id} does not exist.")
        if first_name:
            self.contacts[contact_id]["first_name"] = first_name
        if last_name:
            self.contacts[contact_id]["last_name"] = last_name
        if company:
            self.contacts[contact_id]["company"] = company
        if title:
            self.contacts[contact_id]["title"] = title
        if work_phone:
            self.contacts[contact_id]["work_phone"] = work_phone
        if mobile_phone:
            self.contacts[contact_id]["mobile_phone"] = mobile_phone
        if home_phone:
            self.contacts[contact_id]["home_phone"] = home_phone
        if email:
            self.contacts[contact_id]["email"] = email
        self.__save_state()
        return f"Contact {contact_id} updated"

    def delete_contact(self, contact_id: int) -> str:
        """Delete a contact."""
        contact_id = str(contact_id)  # Normalize to string
        if contact_id in self.contacts:
            del self.contacts[contact_id]
            self.__save_state()
        else:
            raise ValueError(f"Contact with ID {contact_id} does not exist.")
        return f"Contact {contact_id} deleted"

    def list_contacts(self) -> Dict[int, Dict]:
        """List all contacts with integer keys."""
        return {int(contact_id): details for contact_id, details in self.contacts.items()}

    def get_contact(self, contact_id: int) -> Dict:
        """Retrieve a contact by ID."""
        contact_id = str(contact_id)
        if contact_id in self.contacts:
            return self.contacts[contact_id]
        else:
            return f"Contact {contact_id} does not exist"

    def search_contacts(self, query: str) -> List[Dict]:
        """Search contacts by name, email, or phone number using a regex pattern."""
        try:
            query_regex = re.compile(query, re.IGNORECASE)
        except re.error as e:
            raise ValueError(f"Invalid regex pattern: {e}")
        return [
            {"contact_id": contact_id, **contact}
            for contact_id, contact in self.contacts.items()
            if query_regex.search(contact.get("first_name", "") or "")
            or query_regex.search(contact.get("last_name", "") or "")
            or query_regex.search(contact.get("email", "") or "")
            or query_regex.search(contact.get("work_phone", "") or "")
            or query_regex.search(contact.get("mobile_phone", "") or "")
            or query_regex.search(contact.get("home_phone", "") or "")
        ]

def get_todays_date() -> str:
    return "11/11/2024"

def sendEmail(
    to: str, 
    subj: str, 
    cc: Optional[str] = None, 
    body: Optional[List[str]] = None
) -> str:
    """Fake-send an email with the provided parameters"""
    return {
        "status": "Message Sent",
        "to": to,
        "subject": subj
    }

import readline
import os

HISTORY_FILE = ".calMsgEmail_history"

def setup_readline():
    """Set up GNU Readline capabilities."""
    # Load command history if it exists
    if os.path.exists(HISTORY_FILE):
        readline.read_history_file(HISTORY_FILE)

    # Save command history on exit
    import atexit
    atexit.register(readline.write_history_file, HISTORY_FILE)

    # Enable auto-completion (optional)
    def completer(text, state):
        commands = [
            "cal.add_event(",
            "cal.find_next_available(start_datetime=",
            "cal.delete_event(event_id=",
            "cal.get_event(event_id=",
            "cal.list_events()",
            "cal.get_events_by_date(date=",
            "cal.get_events_between(start_datetime=",
            "tsk.add_task(title=",
            "tsk.update_task(task_id=",
            "tsk.delete_task(task_id=",
            "tsk.list_tasks()",
            "ctc.list_contacts()",
            "ctc.add_contact(",
            "ctc.update_contact(contact_id=",
            "ctc.delete_contact(contact_id=",
            "ctc.get_contact(contact_id=",
            "ctc.search_contacts(query=",
            "sendEmail(to=",
            "get_todays_date()",
        ]
        matches = [cmd for cmd in commands if cmd.startswith(text)]
        if state < len(matches):
            return matches[state]
        return None

    readline.set_completer(completer)
    readline.parse_and_bind("tab: complete")  # Use tab for auto-completion

def main():
    cal = Calendar("_calendar.json")
    tsk = Tasks("_tasks.json")
    ctc = Contacts("_contacts.json")

    setup_readline()
    print("Interactive Mode: Enter commands to interact with Calendar and Tasks.")
    print("Available objects: `cal` (Calendar), `tsk` (Tasks), and 'ctc' (Contacts).")
    print("Example commands:")
    print("  cal.add_event(title='Meeting', date='12/19/2024 09:00', duration=60, users=['Alice', 'Bob'])")
    print("  tsk.list_tasks()")
    print("  cal.find_events_by_date('12/19/2024')")
    print("  tsk.get_tasks_due_on('12/19/2024')")
    print("  ctc.add_contact(first_name='John', last_name='Smith', title='Chief Cook and Bottle Washer', work_phone='555.1212', email='jsmith@example.com')")

    while True:
        try:
            # Read user input
            command = input("\nEnter command (or 'exit' to quit): ")
            if command.lower() == "exit":
                print("Exiting interactive mode. Goodbye!")
                break

            # Execute the command dynamically
            response = eval(command)

            # Format the result as JSON
            output = {"response": response}
            print(json.dumps(output, indent=4))
        except Exception as e:
            # Catch and display errors
            print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
