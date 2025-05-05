import json
from typing import List, Optional, Tuple
import readline
import os
import atexit
from calendars import Calendar
from tasks import Tasks
from contacts import Contacts

HISTORY_FILE = ".calMsgCts_history"

def setup_readline():
    """Set up GNU Readline capabilities."""
    # Load command history if it exists
    if os.path.exists(HISTORY_FILE):
        readline.read_history_file(HISTORY_FILE)

    # Save command history on exit
    atexit.register(readline.write_history_file, HISTORY_FILE)

    # Enable auto-completion (optional)
    def completer(text, state):
        commands = [
            # Calendar methods
            "cal.add_event(title='', date='', duration=-1, users=[], event_id=-1)",
            "cal.find_next_available(start_datetime='', duration_minutes=-1)",
            "cal.delete_event(event_id=-1)",
            "cal.get_event(event_id=-1)",
            "cal.list_events()",
            "cal.get_events_by_date(date='')",
            "cal.get_events_between(start_datetime='', end_datetime='')",
            "cal.update_event(event_id=-1, title='', date='', duration=-1, users=[])",
            
            # Task methods
            "tsk.add_task(title='', description='', due_date='', progress=-1.0, state='', task_id=-1)",
            "tsk.update_task(task_id=-1, title='', description='', due_date='', progress=-1.0, state='')",
            "tsk.delete_task(task_id=-1)",
            "tsk.list_tasks()",
            "tsk.get_task(task_id=-1)",
            "tsk.get_tasks_due_today(today='')",
            "tsk.get_tasks_due_on(date='')",
            "tsk.get_tasks_due_on_or_before(date='')",
            "tsk.get_tasks_with_progress(min_progress=-1.0, max_progress=-1.0)",
            "tsk.get_tasks_by_state(state='')",
            
            # Contacts methods
            "ctc.list_contacts()",
            "ctc.add_contact(first_name='', last_name='', title='', company='', work_phone='', mobile_phone='', home_phone='', email='', contact_id=-1)",
            "ctc.update_contact(contact_id=-1, first_name='', last_name='', company='', title='', work_phone='', mobile_phone='', home_phone='', email='')",
            "ctc.delete_contact(contact_id=-1)",
            "ctc.get_contact(contact_id=-1)",
            "ctc.search_contacts(query='')",
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
    print("  cal.get_events_by_date('12/19/2024')")
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
