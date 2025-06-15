import pytest
import sys
from types import SimpleNamespace
from unittest.mock import MagicMock

import caltskcts.__main__ as main_mod
from caltskcts.dispatch_utils import get_command_map, dispatch_command


class DummyCal:
    def __init__(self, uri):
        self.uri = uri
    def add_event(self, title, date, duration, users):
        return {"title": title, "date": date, "duration": duration, "users": users}
    def list_events(self):
        return [{"title": "dummy"}]

class DummyTsk:
    def __init__(self, uri): 
        self.uri = uri

class DummyCtc:
    def __init__(self, uri): self.uri = uri

def test_parse_defaults():
    args = main_mod.parse_arguments([])
    assert args.files is True
    assert args.database is None

def test_parse_database_flag():
    args = main_mod.parse_arguments(["--database", "mydb.sqlite"])
    assert args.database == "sqlite:///mydb.sqlite"
    assert args.files is False

def test_setup_storage_file(monkeypatch):
    monkeypatch.setattr(main_mod, "Calendar", DummyCal)
    monkeypatch.setattr(main_mod, "Tasks", DummyTsk)
    monkeypatch.setattr(main_mod, "Contacts", DummyCtc)

    args = SimpleNamespace(files=True, database=None)
    cal, tsk, ctc, mode = main_mod.setup_storage(args)

    assert isinstance(cal, DummyCal)
    assert isinstance(tsk, DummyTsk)
    assert isinstance(ctc, DummyCtc)
    assert mode == "file-based"
    assert cal.uri == "_calendar.json"
    assert tsk.uri == "_tasks.json"
    assert ctc.uri == "_contacts.json"

def test_command_map_has_all_keys():
    command_map = get_command_map()
    assert "cal" in command_map
    assert "tsk" in command_map
    assert "ctc" in command_map
    assert all(isinstance(v, list) for v in command_map.values())

def test_mutually_exclusive_args_fail(monkeypatch, capsys):
    # both flags should trigger argparse error
    monkeypatch.setattr(sys, "argv", ["prog", "--files", "--database"])
    with pytest.raises(SystemExit):
        main_mod.main()
    captured = capsys.readouterr()
    assert "not allowed with argument" in captured.err

def test_default_backend_files(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["prog", "--files"])
    cal = MagicMock()
    tsk = MagicMock()
    ctc = MagicMock()
    monkeypatch.setattr(main_mod, "Calendar", cal)
    monkeypatch.setattr(main_mod, "Tasks", tsk)
    monkeypatch.setattr(main_mod, "Contacts", ctc)
    monkeypatch.setattr("builtins.input", lambda prompt="": "exit")
    monkeypatch.setattr("builtins.print", lambda *args, **kwargs: None)
    monkeypatch.setattr(main_mod, "logger", MagicMock())

    main_mod.main()

    cal.assert_called_once_with("_calendar.json")
    tsk.assert_called_once_with("_tasks.json")
    ctc.assert_called_once_with("_contacts.json")


def test_backend_database_uri(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["prog", "--database", "custom.db"])
    cal = MagicMock()
    tsk = MagicMock()
    ctc = MagicMock()
    monkeypatch.setattr(main_mod, "Calendar", cal)
    monkeypatch.setattr(main_mod, "Tasks", tsk)
    monkeypatch.setattr(main_mod, "Contacts", ctc)
    monkeypatch.setattr("builtins.input", lambda prompt="": "exit")
    monkeypatch.setattr("builtins.print", lambda *args, **kwargs: None)
    monkeypatch.setattr(main_mod, "logger", MagicMock())

    main_mod.main()

    cal.assert_called_once_with("sqlite:///custom.db")

def test_dispatch_command_add_event(monkeypatch):
    # patch real storage classes
    monkeypatch.setattr(main_mod, "Calendar", DummyCal)
    monkeypatch.setattr(main_mod, "Tasks", DummyTsk)
    monkeypatch.setattr(main_mod, "Contacts", DummyCtc)

    # create our context
    cal = DummyCal("dummy")
    tsk = DummyTsk("dummy")
    ctc = DummyCtc("dummy")
    ctx = {"cal": cal, "tsk": tsk, "ctc": ctc, "result": [None]}

    cmd = "cal.add_event(title='Hello', date='06/15/2025 09:00', duration=30, users=['A','B'])"
    result = dispatch_command(cmd, ctx)

    assert isinstance(result, dict)
    assert result["title"] == "Hello"
    assert result["duration"] == 30

@pytest.mark.parametrize("argv, expected_mode", [
    ([], "file-based"),
    (["--files"], "file-based"),
    (["--database", "x.db"], "database"),
])
def test_full_main_no_loop(monkeypatch, capsys, argv, expected_mode):
    # stub storage & dispatch so we can quit immediately
    monkeypatch.setattr(main_mod, "Calendar", DummyCal)
    monkeypatch.setattr(main_mod, "Tasks", DummyTsk)
    monkeypatch.setattr(main_mod, "Contacts", DummyCtc)

    # make dispatch_command just echo back the command
    monkeypatch.setattr(main_mod, "dispatch_command", lambda c, ctx: f"ECHO: {c}")

    # stub input() to immediately return 'exit'
    monkeypatch.setattr("builtins.input", lambda prompt="": "exit")

    # run main
    main_mod.main(argv)

    captured = capsys.readouterr()
    assert f"Using {expected_mode} storage" in captured.out
