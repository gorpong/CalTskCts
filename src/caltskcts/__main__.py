import sys
from typing import List, Optional

from caltskcts.config import get_database_uri
from caltskcts.cli import app as cli_app

def fixup_db_argument(argv: List[str]) -> List[str]:
    out: List[str] = []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a in ("--db","-db","--database"):
            out.append(a)
            if i+1 == len(argv) or argv[i+1].startswith(("-", "cal", "tsk", "ctc", "raw", "export", "import")):
                out.append(get_database_uri())
            else:
                i += 1
                out.append(argv[i])
        else:
            out.append(a)
        i += 1
    return out

def main(argv: Optional[List[str]] = None) -> None:
    """Entry point: delegate to CLI subcommands via Typer/Click"""
    args_list = argv if argv is not None else sys.argv[1:]
    args_list = fixup_db_argument(args_list)
    cli_app(args=args_list)

if __name__ == "__main__":
    main(sys.argv[1:])
