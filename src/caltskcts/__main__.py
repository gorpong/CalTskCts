import sys
from typing import List, Optional

from caltskcts.cli import app as cli_app

def main(argv: Optional[List[str]] = None) -> None:
    """Entry point: delegate to CLI subcommands via Typer/Click"""
    cli_app()

if __name__ == "__main__":
    main(sys.argv[1:])
