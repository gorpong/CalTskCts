import json
import os
import readline
import atexit
import traceback
from typing import Dict, Any, List
from datetime import datetime

# Local imports
from calendars import Calendar
from tasks import Tasks
from contacts import Contacts
from logger import get_logger, log_exception

HISTORY_FILE = ".calMsgCts_history"

# Initialize logger
logger = get_logger()

def setup_readline(command_map: Dict[str, List[str]]) -> None:
    """
    Set up GNU Readline capabilities for command history and auto-completion.
    
    Args:
        command_map: Dictionary mapping object names to their available commands
    """
    logger.debug("Setting up readline for command history and auto-completion")
    
    # Load command history if it exists
    if os.path.exists(HISTORY_FILE):
        try:
            readline.read_history_file(HISTORY_FILE)
            logger.debug(f"Loaded command history from {HISTORY_FILE}")
        except Exception as e:
            logger.warning(f"Failed to read history file: {e}")

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
    logger.debug("Command auto-completion enabled")

def get_command_map() -> Dict[str, List[str]]:
    """Build command map for auto-completion"""
    logger.debug("Building command map for auto-completion")
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
    logger.debug(f"Dispatching command: {command}")
    
    # Security check - only allow specific function calls
    allowed_prefixes = [f"{key}." for key in context.keys()]
    
    if not any(command.startswith(prefix) for prefix in allowed_prefixes):
        error_msg = f"Invalid command. Must use one of: {', '.join(context.keys())}"
        logger.warning(f"Command validation failed: {error_msg}")
        raise ValueError(error_msg)
    
    # Parse object and method
    parts = command.split(".", 1)
    if len(parts) != 2:
        error_msg = "Invalid command format"
        logger.warning(f"Command parsing failed: {error_msg}")
        raise ValueError(error_msg)
        
    obj_name, method_call = parts
    
    # Get the object
    obj = context.get(obj_name)
    if not obj:
        error_msg = f"Unknown object: {obj_name}"
        logger.warning(f"Command validation failed: {error_msg}")
        raise ValueError(error_msg)
    
    # Extract method name and arguments
    method_name = method_call.split("(", 1)[0].strip()
    
    # Check if method exists
    if not hasattr(obj, method_name):
        error_msg = f"Unknown method: {method_name}"
        logger.warning(f"Command validation failed: {error_msg}")
        raise ValueError(error_msg)
    
    # Get the method
    method = getattr(obj, method_name)
    if not callable(method):
        error_msg = f"{method_name} is not callable"
        logger.warning(f"Command validation failed: {error_msg}")
        raise ValueError(error_msg)
    
    # Use exec with local context to run the command
    # This is safer than eval but still requires trusted input
    local_context = {**context}
    
    exec_str = f"result[0] = {command}"
    try:
        logger.info(f"Executing command: {command}")
        exec(exec_str, {"__builtins__": {}}, local_context)
        logger.debug("Command executed successfully")
        return local_context["result"][0]
    except Exception as e:
        logger.error(f"Command execution failed: {str(e)}")
        # Re-raise with original traceback
        raise

def main() -> None:
    logger.info("Application starting")
    
    try:
        # Initialize objects with data files
        logger.info("Initializing application components")
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
        logger.info("Application context initialized")

        # Set up command history and auto-completion
        command_map = get_command_map()
        setup_readline(command_map)
        
        # Print welcome message and instructions
        logger.info("Starting interactive mode")
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
                    logger.info("User requested exit")
                    print("Exiting interactive mode. Goodbye!")
                    break
                
                # Skip empty commands
                if not command:
                    continue
                    
                # Log the command (but not in DEBUG mode to avoid duplication)
                logger.info(f"User command: {command}")

                # Execute the command through dispatcher
                response = dispatch_command(command, context)

                # Format the result as JSON
                output = {"response": response}
                formatted_output = json.dumps(output, indent=4, default=str)
                print(formatted_output)
                
            except Exception as e:
                error_message = f"Error: {str(e)}"
                print(error_message)
                # Log the full traceback for debugging
                log_exception(e, "Command execution error")
    
    except Exception as e:
        logger.critical(f"Fatal error: {str(e)}")
        print(f"Fatal error occurred: {str(e)}")
        # Log the full traceback
        log_exception(e, "Fatal application error")
    finally:
        logger.info("Application exiting")

if __name__ == "__main__":
    main()
