import json
from typer.testing import CliRunner
from caltskcts.cli import app
import pytest
from pathlib import Path

runner = CliRunner()

@pytest.fixture
def temp_json_files(tmp_path, monkeypatch):
    cal_path = tmp_path / "_calendar.json"
    tsk_path = tmp_path / "_tasks.json"
    ctc_path = tmp_path / "_contacts.json"
    
    cal_data = {
        "1": { "title": "Existing Meeting", "date": "12/31/2025 14:00","duration": 60, "users": ["Alice"] },
        "2": { "title": "Daily Standup", "date": "12/30/2025 09:00", "duration": 30, "users": [] }
    }
    ctc_data = {
        "1": { "first_name": "Alice", "last_name": "Smith", "email": "alice@example.com" },
        "2": { "first_name": "Fred", "last_name": "Smythe", "email": "fsmythe@example.com" }
    }
    tsk_data = {
        "1": { "title": "Important thing", "desc": "Very Important description", "dueDate": "12/31/2025", "progress": 50.0, "state": "In Progress" }
    }
    cal_path.write_text(json.dumps(cal_data, indent=2))
    ctc_path.write_text(json.dumps(ctc_data, indent=2))
    tsk_path.write_text(json.dumps(tsk_data, indent=2))
    
    monkeypatch.setenv("CALTSKCTS_CALENDAR_FILE", str(cal_path))
    monkeypatch.setenv("CALTSKCTS_CONTACTS_FILE", str(ctc_path))
    monkeypatch.setenv("CALTSKCTS_TASKS_FILE", str(tsk_path))
    
    return {"calendar": cal_path, "tasks": tsk_path, "contacts": ctc_path}

def test_help_top_level(temp_json_files):
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Commands for calendar events" in result.output
    assert "Commands for tasks" in result.output
    assert "Commands for contacts" in result.output

def test_cal_add_help(temp_json_files):
    result = runner.invoke(app, ["cal", "add_event", "--help"])
    assert result.exit_code == 0
    assert "Add a new event to the calendar" in result.output

def test_task_add_help(temp_json_files):
    result = runner.invoke(app, ["tsk", "add_task", "--help"])
    assert result.exit_code == 0
    assert "Add a Task to the system" in result.output

def test_contact_add_help(temp_json_files):
    result = runner.invoke(app, ["ctc", "add_contact", "--help"])
    assert result.exit_code == 0
    assert "Add a contact" in result.output

def test_raw_command_executes(temp_json_files):
    result = runner.invoke(app, ["raw", "ctc.list_contacts()"])
    assert result.exit_code == 0
    assert "{" in result.output or result.output.strip() == "{}"

def test_export_invalid_combination(temp_json_files):
    result = runner.invoke(app, ["export", "contacts", "--format", "ics", "--output", "foo.ics"])
    assert result.exit_code != 0
    assert "Unsupported combination" in result.output

def test_import_invalid_type(temp_json_files):
    path = Path("dummy.csv")
    result = runner.invoke(app, ["import", "widgets", str(path)])
    assert result.exit_code != 0
    assert "Unsupported type" in result.output
