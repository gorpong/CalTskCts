import pytest
from typer.testing import CliRunner
from caltskcts.cli import app as cli_app
from caltskcts.calendars import Calendar
from caltskcts.tasks import Tasks
from caltskcts.contacts import Contacts

runner = CliRunner()

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
