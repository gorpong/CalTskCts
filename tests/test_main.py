import pytest
import sys
from types import SimpleNamespace
from unittest.mock import MagicMock

import caltskcts.__main__ as main_mod
from caltskcts.dispatch_utils import dispatch_command
from caltskcts.config import get_database_uri

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

def test_file_flag_defaults(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["caltskcts", "--file", "raw", "cal.list_events()"])
    with pytest.raises(SystemExit):
        main_mod.main()
    captured = capsys.readouterr()
    assert "JSON" in captured.out

def test_db_flag_with_custom_path(monkeypatch, capsys):
    """Passing --db with a custom path uses that path."""
    monkeypatch.setattr(sys, "argv", ["caltskcts", "--db", "custom.db", "raw", "cal.list_events()"])
    with pytest.raises(SystemExit):
        main_mod.main()
    captured = capsys.readouterr()
    assert "custom.db" in captured.out

def test_db_flag_without_path(monkeypatch, capsys):
    """Passing only --db uses default DATABASE_URI."""
    cal = MagicMock(); tsk = MagicMock(); ctc = MagicMock();
    monkeypatch.setattr(sys, "argv", ["caltskcts", "--db", "raw", "cal.list_events()"])
    with pytest.raises(SystemExit) as e:
        main_mod.main()
    assert e.value.code == 0
    captured = capsys.readouterr()
    assert get_database_uri() in captured.out

def test_help_flag(monkeypatch, capsys):
    """Check that help message is displayed."""
    monkeypatch.setattr(sys, "argv", ["caltskcts", "--help"])
    with pytest.raises(SystemExit):
        main_mod.main()
    captured = capsys.readouterr()
    assert "Usage:" in captured.out or "usage:" in captured.out

def test_help_flag_cal(monkeypatch, capsys):
    """Check that sub-help dispatches correctly"""
    monkeypatch.setattr(sys, "argv", ["caltskcts", "cal", "--help"])
    with pytest.raises(SystemExit) as e:
        main_mod.main()
    assert e.value.code == 0
    captured = capsys.readouterr()
    assert "get_event" in captured.out

def test_help_flag_cal_getevent(monkeypatch, capsys):
    """Check that sub-help dispatches correctly"""
    monkeypatch.setattr(sys, "argv", ["caltskcts", "cal", "get_event", "--help"])
    with pytest.raises(SystemExit) as e:
        main_mod.main()
    assert e.value.code == 0
    captured = capsys.readouterr()
    assert "--event_id" in captured.out
