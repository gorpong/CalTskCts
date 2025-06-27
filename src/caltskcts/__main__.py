import sys
import os
import readline
import atexit
import argparse
import re
from typing import Dict, Any, List, Optional, Tuple

from caltskcts.dispatch_utils import get_command_map, dispatch_command
from caltskcts.cli import app as cli_app
from caltskcts.calendars import Calendar
from caltskcts.tasks import Tasks
from caltskcts.contacts import Contacts
from caltskcts.logger import get_logger, log_exception
from caltskcts.config import DATABASE_URI

HISTORY_FILE = ".calTskCts_history"
logger = get_logger(__name__)


def extract_sqlite_path(uri: str) -> str:
    match = re.match(r"sqlite:///([^?]+)", uri)
    return match.group(1) if match else uri

def fixup_db_argument(argv: List[str]) -> List[str]:
    """
    If `-db` is present without a path, and the next argument looks like a subcommand,
    inject DATABASE_URI so argparse doesn't misinterpret.
    """
    if "-db" in argv:
        idx = argv.index("-db")
        if idx + 1 >= len(argv) or argv[idx + 1].startswith("-") or argv[idx + 1] in ("cal", "tsk", "ctc", "raw"):
            argv.insert(idx + 1, DATABASE_URI)
    elif "--database" in argv:
        idx = argv.index("--database")
        if idx + 1 >= len(argv) or argv[idx + 1].startswith("-") or argv[idx + 1] in ("cal", "tsk", "ctc", "raw"):
            argv.insert(idx + 1, DATABASE_URI)
    return argv

def parse_arguments(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Calendar, Tasks, and Contacts Manager")
    storage_group = parser.add_mutually_exclusive_group()
    storage_group.add_argument(
        "-f", "--files", action="store_true",
        help="Use JSON files for storage (default)"
    )
    storage_group.add_argument(
        "-db", "--database", nargs="?", const=DATABASE_URI, metavar="DB_PATH",
        help="Use SQLite database for storage (optionally specify path)"
    )

    args, remaining = parser.parse_known_args(argv)
    args.remaining = remaining
    if not args.files and not args.database:
        args.files = True
    if args.database and not args.database.startswith("sqlite://"):
        args.database = f"sqlite:///{args.database}"
        db_path = extract_sqlite_path(args.database)
        if not os.path.isabs(db_path):
            db_dir = os.path.dirname(db_path)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir)
    return args

def setup_storage(args: argparse.Namespace) -> Tuple[Calendar, Tasks, Contacts, str]:
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
    logger.debug("Setting up readline for history and completion")
    if os.path.exists(HISTORY_FILE):
        try:
            readline.read_history_file(HISTORY_FILE)
        except Exception:
            pass
    readline.set_history_length(500)
    atexit.register(readline.write_history_file, HISTORY_FILE)
    def completer(text: str, state: int) -> Optional[str]:
        commands: List[str] = []
        for lst in command_map.values():
            commands.extend(lst)
        matches = [c for c in commands if c.startswith(text)]
        return matches[state] if state < len(matches) else None
    readline.set_completer(completer)
    readline.parse_and_bind("tab: complete")


def main(argv: Optional[List[str]] = None) -> None:
    """Entry point: delegate to CLI subcommands or fallback to interactive REPL."""
    args_list = argv if argv is not None else sys.argv[1:]
    args_list = fixup_db_argument(args_list)
    args = parse_arguments(args_list)

    if len(args.remaining) > 0 and args.remaining[0] == "--":
        args.remaining = args.remaining[1:]
        
    cal, tsk, ctc, storage_type = setup_storage(args)
    if args.remaining and (
        args.remaining[0] in ("cal", "tsk", "ctc", "raw")
        or "--help" in args.remaining
        or "-h" in args.remaining
    ):
        context = {"cal": cal, "tsk": tsk, "ctc": ctc, "result": [None]}
        try:
            cli_app(prog_name="caltskcts", args=args.remaining, standalone_mode=False, obj=context)
        except Exception as e:
            logger.critical(f"CLI command failed: {e}")
            print(f"Error running CLI command: {e}")
    else:
        logger.info("Application starting")
        try:
            command_map = get_command_map()
            context: Dict[str, Any] = {"cal": cal, "tsk": tsk, "ctc": ctc, "result": [None]}
            setup_readline(command_map)
            print(f"Storage: Using {storage_type} storage")
            while True:
                cmd = input("Enter command (or 'exit' to quit): ").strip()
                if cmd.lower() in ("exit", "quit"):
                    break
                if not cmd:
                    continue
                try:
                    resp = dispatch_command(cmd, context)
                    print(resp)
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
