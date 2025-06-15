import pytest
from typer.testing import CliRunner
from unittest.mock import patch, MagicMock
from caltskcts.cli import app as cli_app

runner = CliRunner()

@pytest.fixture
def mock_storage():
    mock_cal = MagicMock()
    mock_cal.add_event.return_value = {"id": 1, "title": "Test Event"}
    mock_cal.list_events.return_value = [{"id": 1, "title": "Test Event"}]

    mock_tsk = MagicMock()
    mock_tsk.add_task.return_value = {"id": 1, "title": "Test Task"}
    mock_tsk.list_tasks.return_value = [{"id": 1, "title": "Test Task"}]

    mock_ctc = MagicMock()
    mock_ctc.add_contact.return_value = {"id": 1, "first_name": "John", "last_name": "Doe"}
    mock_ctc.list_contacts.return_value = [{"id": 1, "first_name": "John", "last_name": "Doe"}]

    context = {"cal": mock_cal, "tsk": mock_tsk, "ctc": mock_ctc, "result": [None]}
    return context

@pytest.fixture
def dummy_context():
    class Dummy:
        def list_events(self): return [{"id": 1}]
        def list_tasks(self): return [{"id": 2}]
        def list_contacts(self): return [{"id": 3}]

    dummy = Dummy()
    return {"cal": dummy, "tsk": dummy, "ctc": dummy, "result": [None]}

def test_raw_cal_command(dummy_context):
    result = runner.invoke(cli_app, ["raw", "cal.list_events()"], obj=dummy_context)
    assert result.exit_code == 0
    assert '"id": 1' in result.output

def test_raw_task_command(dummy_context):
    result = runner.invoke(cli_app, ["raw", "tsk.list_tasks()"], obj=dummy_context)
    assert result.exit_code == 0
    assert '"id": 2' in result.output

def test_raw_contact_command(dummy_context):
    result = runner.invoke(cli_app, ["raw", "ctc.list_contacts()"], obj=dummy_context)
    assert result.exit_code == 0
    assert '"id": 3' in result.output

def test_add_event(mock_storage):
    result = runner.invoke(cli_app, ["cal", "add_event", "--title", "Test Event", "--date", "01/01/2025 10:00"], obj=mock_storage)
    assert result.exit_code == 0
    assert "Test Event" in result.stdout

def test_list_events(mock_storage):
    result = runner.invoke(cli_app, ["cal", "list_events"], obj=mock_storage)
    assert result.exit_code == 0
    assert "Test Event" in result.stdout

def test_add_task(mock_storage):
    result = runner.invoke(cli_app, ["tsk", "add_task", "--title", "Test Task"], obj=mock_storage)
    assert result.exit_code == 0
    assert "Test Task" in result.stdout

def test_list_tasks(mock_storage):
    result = runner.invoke(cli_app, ["tsk", "list_tasks"], obj=mock_storage)
    assert result.exit_code == 0
    assert "Test Task" in result.stdout

def test_add_contact(mock_storage):
    result = runner.invoke(cli_app, ["ctc", "add_contact", "--first", "John", "--last", "Doe"], obj=mock_storage)
    assert result.exit_code == 0
    assert "John" in result.stdout

def test_list_contacts(mock_storage):
    result = runner.invoke(cli_app, ["ctc", "list_contacts"], obj=mock_storage)
    assert result.exit_code == 0
    assert "John" in result.stdout
