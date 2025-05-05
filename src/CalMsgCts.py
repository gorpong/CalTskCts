import json
import os
import readline
import atexit
from typing import Dict, Any, List

# Local imports
from calendars import Calendar
from tasks import Tasks
from contacts import Contacts

HISTORY_FILE = ".calMsgCts_history"

def setup_readline(command_map: Dict[str, List[str]]) -> None:
    """
    Set up GNU Readline capabilities for command history and auto-completion.
    
    Args:
        command_map: Dictionary mapping object names to their available commands
    """
    # Load command history if it exists
    if os.path.exists(HISTORY_FILE):
        readline.read_history_file(HISTORY_FILE)

    # Save command history on exit
    atexit.register(readline.write_history_file, HISTORY_FILE)

    # Enable auto-completion
    def completer(text: str, state: int) -> str:
        # Flatten command list
        commands = []
        for cmd_list in command_map.values():
            commands.extend(cmd_list)
            
        matches = [cmd for cmd in commands if cmd.startswith(text)]
        if state < len(matches):
            return matches[state]
        return None

    readline.set_completer(completer)
    readline.parse_and_bind("tab: complete")  # Use tab for auto-completion

def get_command_map() -> Dict[str, List[str]]:
    """Build command map for auto-completion"""
    return {
        "cal": [
            "cal.add_event(title='', date='', duration=-1, users=[])",
            "cal.find_next_available(start_datetime='', duration_minutes=-1)",
            "cal.delete_event(event_id=-1)",
            "cal.get_event(event_id=-1)",
            "cal.list_events()",
            "cal.get_events_by_date(date='')",
            "cal.get_events_between(start_datetime='', end_datetime='')",
            "cal.update_event(event_id=-1, title='', date='', duration=-1, users=[])",
        ],
        "tsk": [
            "tsk.add_task(title='', description='', due_date='', progress=-1.0, state='Not Started')",
            "tsk.update_task(task_id=-1, title='', description='', due_date='', progress=-1.0, state='')",
            "tsk.delete_task(task_id=-1)",
            "tsk.list_tasks()",
            "tsk.get_task(task_id=-1)",
            "tsk.get_tasks_due_today()",
            "tsk.get_tasks_due_on(date='')",
            "tsk.get_tasks_due_on_or_before(date='')",
            "tsk.get_tasks_with_progress(min_progress=0.0, max_progress=100.0)",
            "tsk.get_tasks_by_state(state='Not Started')",
        ],
        "ctc": [
            "ctc.list_contacts()",
            "ctc.add_contact(first_name='', last_name='', title='', company='', work_phone='', mobile_phone='', home_phone='', email='')",
            "ctc.update_contact(contact_id=-1, first_name='', last_name='', company='', title='', work_phone='', mobile_phone='', home_phone='', email='')",
            "ctc.delete_contact(contact_id=-1)",
            "ctc.get_contact(contact_id=-1)",
            "ctc.search_contacts(query='')",
        ]
    }

def dispatch_command(command: str, context: Dict[str, Any]) -> Any:
    """
    Safely execute a command in the given context.
    
    Args:
        command: The command string to execute
        context: Dictionary of available objects
        
    Returns:
        The result of the command execution
        
    Raises:
        ValueError: If the command is not recognized or contains unauthorized operations
    """
    # Security check - only allow specific function calls
    allowed_prefixes = [f"{key}." for key in context.keys()]
    
    if not any(command.startswith(prefix) for prefix in allowed_prefixes):
        raise ValueError(f"Invalid command. Must use one of: {', '.join(context.keys())}")
    
    # Parse object and method
    parts = command.split(".", 1)
    if len(parts) != 2:
        raise ValueError("Invalid command format")
        
    obj_name, method_call = parts
    
    # Get the object
    obj = context.get(obj_name)
    if not obj:
        raise ValueError(f"Unknown object: {obj_name}")
    
    # Extract method name and arguments
    method_name = method_call.split("(", 1)[0].strip()
    
    # Check if method exists
    if not hasattr(obj, method_name):
        raise ValueError(f"Unknown method: {method_name}")
    
    # Get the method
    method = getattr(obj, method_name)
    if not callable(method):
        raise ValueError(f"{method_name} is not callable")
    
    # Use exec with local context to run the command
    # This is safer than eval but still requires trusted input
    local_context = {**context}
    result = [None]  # Use list to store result from exec
    
    exec_str = f"result[0] = {command}"
    exec(exec_str, {"__builtins__": {}}, local_context)
    
    return local_context["result"][0]

def main() -> None:
    # Initialize objects with data files
    cal = Calendar("_calendar.json")
    tsk = Tasks("_tasks.json")
    ctc = Contacts("_contacts.json")
    
    # Create context with available objects
    context = {
        "cal": cal,
        "tsk": tsk,
        "ctc": ctc,
        "result": [None],  # Used for exec
    }

    # Set up command history and auto-completion
    command_map = get_command_map()
    setup_readline(command_map)
    
    # Print welcome message and instructions
    print("Interactive Mode: Enter commands to interact with Calendar, Tasks, and Contacts.")
    print("Available objects: `cal` (Calendar), `tsk` (Tasks), and `ctc` (Contacts).")
    print("Example commands:")
    print("  cal.add_event(title='Meeting', date='12/19/2024 09:00', duration=60, users=['Alice', 'Bob'])")
    print("  tsk.list_tasks()")
    print("  cal.get_events_by_date('12/19/2024')")
    print("  tsk.get_tasks_due_on('12/19/2024')")
    print("  ctc.add_contact(first_name='John', last_name='Smith', title='Manager', work_phone='555.1212')")

    while True:
        try:
            # Read user input
            command = input("\nEnter command (or 'exit' to quit): ").strip()
            if command.lower() in ("exit", "quit"):
                print("Exiting interactive mode. Goodbye!")
                break

            # Execute the command through dispatcher
            response = dispatch_command(command, context)

            # Format the result as JSON
            output = {"response": response}
            print(json.dumps(output, indent=4, default=str))
        except Exception as e:
            print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
