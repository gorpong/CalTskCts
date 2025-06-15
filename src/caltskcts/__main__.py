import json
import os
import readline
import atexit
import argparse
from typing import Dict, Any, List, Union, Tuple, Optional
import re
import sys

# Local imports
from caltskcts.calendars import Calendar
from caltskcts.tasks import Tasks
from caltskcts.contacts import Contacts
from caltskcts.logger import get_logger, log_exception
from caltskcts.config import DATABASE_URI
from caltskcts.dispatch_utils import dispatch_command, get_command_map

HISTORY_FILE = ".calTskCts_history"
logger = get_logger(__name__)

def extract_sqlite_path(uri: str) -> str:
    match = re.match(r"sqlite:///(.+)", uri)
    return match.group(1) if match else uri

def parse_arguments(argv: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse command line arguments for storage selection."""
    parser = argparse.ArgumentParser(description="Calendar, Tasks, and Contacts Manager")
    
    # Mutually exclusive group for storage (JSON vs SQLite)
    storage_group = parser.add_mutually_exclusive_group()
    storage_group.add_argument(
        "-f", "--files", action="store_true",
        help="Use JSON files for storage (default)"
    )
    storage_group.add_argument(
        "-db", "--database", nargs="?", const=DATABASE_URI, metavar="DB_PATH",
        help="Use SQLite database for storage (optionally specify path)"
    )

    args = parser.parse_args(argv)

    # Default to files if neither given
    if not args.files and not args.database:
        args.files = True

    # If database is specified, ensure it has the correct SQLAlchemy prefix
    if args.database:
        if not args.database.startswith("sqlite:///"):
            args.database = f"sqlite:///{args.database}"
        db_path = extract_sqlite_path(args.database)
        # Convert relative or absolute path to SQLAlchemy URI format
        if not os.path.isabs(db_path):
            # For relative paths, make sure the directory exists
            db_dir = os.path.dirname(db_path)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir)
    
    return args

def setup_storage(args: argparse.Namespace) -> Tuple[Calendar, Tasks, Contacts, str]:
    """
    Given parsed args, initialize and return
    (cal, tsk, ctc, storage_type_name).
    """
    if args.files:
        logger.info("Using JSON files for storage")
        cal = Calendar("_calendar.json")
        tsk = Tasks("_tasks.json")
        ctc = Contacts("_contacts.json")
        storage_type = "file-based"
    else:
        logger.info(f"Using database for storage: {args.database}")
        cal = Calendar(args.database)
        tsk = Tasks(args.database)
        ctc = Contacts(args.database)
        storage_type = "database"

    return cal, tsk, ctc, storage_type

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

    readline.set_history_length(500)
    # Save command history on exit
    atexit.register(readline.write_history_file, HISTORY_FILE)

    # Enable auto-completion
    def completer(text: str, state: int) -> Union[str, None]:
        # Flatten command list
        commands: List[str] = []
        for cmd_list in command_map.values():
            commands.extend(cmd_list)
            
        matches = [cmd for cmd in commands if cmd.startswith(text)]
        if state < len(matches):
            return matches[state]
        return None

    readline.set_completer(completer)
    readline.parse_and_bind("tab: complete")  # Use tab for auto-completion
    logger.debug("Command auto-completion enabled")

def main(argv: Optional[List[str]] = None) -> None:
    logger.info("Application starting")
    try:
        # ==== argument parsing & storage setup ====
        args = parse_arguments(argv)
        logger.info("Initializing application components")
        cal, tsk, ctc, storage_type = setup_storage(args)
        command_map = get_command_map()
        # Create context with available objects
        context: Dict[str, Any] = {
            "cal": cal,
            "tsk": tsk,
            "ctc": ctc,
            "result": [None],  # Used for exec
        }
        logger.info("Application context initialized")

        setup_readline(command_map)
        # Print welcome message and instructions
        logger.info("Starting interactive mode")
        print("Interactive Mode: Enter commands to interact with Calendar, Tasks, and Contacts.")
        print(f"Storage: Using {storage_type} storage")
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
                print(f"Error: {e}")
                log_exception(e, "Command execution error")

    except Exception as e:
        logger.critical(f"Fatal error: {e}")
        print(f"Fatal error occurred: {e}")
        log_exception(e, "Fatal application error")
    finally:
        logger.info("Application exiting")

if __name__ == "__main__":
    main(sys.argv[1:])
