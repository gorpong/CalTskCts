import pytest
import json
from typer.testing import CliRunner
from caltskcts.cli import app as cli_app

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


def test_raw_cal_command(temp_json_files):
    result = runner.invoke(cli_app, ["--file", "raw", "cal.list_events()"])
    assert result.exit_code == 0
    assert "Existing Meeting" in result.output

def test_raw_task_command(temp_json_files):
    result = runner.invoke(cli_app, ["--file", "raw", "tsk.list_tasks()"])
    assert result.exit_code == 0
    assert "Important thing" in result.output

def test_raw_contact_command(temp_json_files):
    result = runner.invoke(cli_app, ["--file", "raw", "ctc.list_contacts()"])
    assert result.exit_code == 0
    assert "Smythe" in result.output

def test_add_event(temp_json_files):
    result = runner.invoke(cli_app, ["--file", "cal", "add_event", "--title", "Test Event", "--date", "01/01/2025 10:00"])
    assert result.exit_code == 0
    assert "Added" in result.stdout
    result = runner.invoke(cli_app, ["--file", "cal", "list_events"])
    assert result.exit_code == 0
    assert "Test Event" in result.stdout

def test_add_contact(temp_json_files):
    result = runner.invoke(cli_app, ["--file", "ctc", "add_contact", "-f", "Joe", "-l", "Bob Briggs"])
    assert result.exit_code == 0
    assert "added" in result.stdout
    result = runner.invoke(cli_app, ["--file", "ctc", "list_contacts"])
    assert result.exit_code == 0
    assert "3:" in result.stdout 
    assert "Briggs" in result.stdout

def test_delete_event(temp_json_files):
    result = runner.invoke(cli_app, ["--file", "cal", "list_events"])
    assert result.exit_code == 0
    assert "Daily Standup" in result.stdout
    result = runner.invoke(cli_app, ["--file", "cal", "delete_event", "--event_id", "2"])
    assert result.exit_code == 0
    result = runner.invoke(cli_app, ["--file", "cal", "list_events"])
    assert result.exit_code == 0
    assert "Daily Standup" not in result.stdout    
