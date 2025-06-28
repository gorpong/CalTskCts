import json
import pytest
from typer.testing import CliRunner

from caltskcts.cli       import app as cli_app
from caltskcts.calendars import Calendar
from caltskcts.tasks     import Tasks
from caltskcts.contacts  import Contacts

runner = CliRunner()

@pytest.fixture
def cli_context(tmp_path):
    cal_file = tmp_path / "calendar.json"
    tsk_file = tmp_path / "tasks.json"
    ctc_file = tmp_path / "contacts.json"
    for f in (cal_file, tsk_file, ctc_file):
        f.write_text("{}")

    calendar = Calendar(str(cal_file))
    tasks    = Tasks   (str(tsk_file))
    contacts = Contacts(str(ctc_file))

    # Prepoulate some calendar events for all tests
    calendar.add_event(title="First Event", date="11/12/2024 10:00", duration=60, users=["Joe", "Alice"])
    calendar.add_event(title="Second Event", date="11/12/2024 11:00", duration=30, users=["Bob", "John"])
    calendar.add_event(title="Third Event", date="11/13/2024 13:00", duration=60, users=["Fred", "Bob"])
    # Prepoulate some tasks for all tests
    tasks.add_task(title="First Task", description="This is the first task", due_date="11/13/2024")
    tasks.add_task(title="Second Task", description="This is the second task", due_date="11/14/2024", progress=50, state="In Progress")
    tasks.add_task(title="Third Task", description="This is the third task", due_date="11/15/2024", progress=100)
    # Prepopulate some contacts for all tests
    contacts.add_contact(first_name="Joe", last_name="Bob", email="joe.bob@example.com")
    contacts.add_contact(first_name="Alice", last_name="Smith", email="alice.smith@example.com")
    contacts.add_contact(first_name="Fred", last_name="Smythe", email="fred.smythe@example.com")

    return {
        "cal":    calendar,
        "tsk":    tasks,
        "ctc":    contacts,
        "result": [None],
    }

# ------------------------- 
#       Calendar Events
# -------------------------
def test_get_event_by_id(cli_context):
    evt = runner.invoke(cli_app, [
        "cal", "get_event",
        "--event_id", 2
    ], obj=cli_context)
    assert evt.exit_code == 0
    assert "Second Event" in evt.stdout

def test_add_and_list_event(cli_context):
    add = runner.invoke(cli_app, [
        "cal", "add_event",
        "--title",    "Team Sync",
        "--date",     "06/30/2025 14:00",
        "--duration", "45",
        "--users",     "alice",
        "--users",     "bob",
    ], obj=cli_context)
    assert add.exit_code == 0
    assert "added" in add.stdout.lower()

    lst = runner.invoke(cli_app, ["cal", "list_events"], obj=cli_context)
    assert lst.exit_code == 0
    assert "Team Sync" in lst.stdout
    assert "Second Event" in lst.stdout

    with open(cli_context["cal"].state_file, "r") as f:
        state = json.load(f)
    assert any(ev["title"] == "Team Sync" for ev in state.values())

def test_update_event(cli_context):
    evs = cli_context["cal"].list_events()
    id = next(k for k, v in evs.items() if v["title"] == "Second Event")
    upd = runner.invoke(cli_app, [
        "cal", "update_event",
        "--event_id", id,
        "--title",    "Rescheduled"
    ], obj=cli_context)
    assert upd.exit_code == 0
    assert "updated" in upd.stdout
    ev2 = cli_context["cal"].list_events()
    assert ev2[id]["title"] == "Rescheduled"

def test_delete_event(cli_context):
    evt = runner.invoke(cli_app, [
        "cal", "delete_event",
        "--event_id", "1"
    ], obj=cli_context)
    assert evt.exit_code == 0
    assert "deleted" in evt.stdout
    
    evs = cli_context["cal"].list_events()
    assert len(evs) == 2

def test_delete_without_eventid(cli_context):
    runner.invoke(cli_app, [
        "cal", "add_event",
        "--title", "Original",
        "--date",  "06/30/2025 10:00"
    ], obj=cli_context)

    evt = runner.invoke(cli_app, [
        "cal", "delete_event"
    ], obj=cli_context)
    assert evt.exit_code != 0

def test_get_events_by_date(cli_context):
    evt = runner.invoke(cli_app, [
        "cal", "get_events_by_date",
        "--date", "11/12/2024"
    ], obj=cli_context)
    assert evt.exit_code == 0
    assert "Third Event" not in evt.stdout

def test_get_events_between(cli_context):
    evt = runner.invoke(cli_app, [
        "cal", "get_events_between",
        "--start", "11/12/2024 10:30",
        "--end", "11/13/2024 15:00"
    ], obj=cli_context)
    assert evt.exit_code == 0
    assert "First Event" not in evt.stdout
    assert "Second Event" in evt.stdout
    assert "Third Event" in evt.stdout

def test_find_next_available(cli_context):
    evt = runner.invoke(cli_app, [
        "cal", "find_next_available",
        "--start_datetime", "11/12/2024 10:30",
        "--duration_minutes", "60"
    ], obj=cli_context)
    assert evt.exit_code == 0
    assert "11/12/2024 11:30" in evt.stdout

# -------------------------
#           Tasks
# -------------------------
def test_get_task_by_id(cli_context):
    tsk = runner.invoke(cli_app, [
        "tsk", "get_task",
        "--task_id", 2
    ], obj=cli_context)
    assert tsk.exit_code == 0
    assert "Second Task" in tsk.stdout
    
def test_add_and_list_task(cli_context):
    at = runner.invoke(cli_app, [
        "tsk", "add_task",
        "--title", "Write Tests",
        "--desc",  "Cover CLI",
    ], obj=cli_context)
    assert at.exit_code == 0
    assert "added" in at.stdout

    lt = runner.invoke(cli_app, ["tsk", "list_tasks"], obj=cli_context)
    assert lt.exit_code == 0
    assert "Write Tests" in lt.stdout

    with open(cli_context["tsk"].state_file) as f:
        tasks_state = json.load(f)
    assert any(t["title"] == "Write Tests" for t in tasks_state.values())

def test_update_task(cli_context):
    tsk = runner.invoke(cli_app, [
        "tsk", "update_task",
        "--task_id", "2",
        "--progress", "100"
    ], obj=cli_context)
    assert tsk.exit_code == 0
    assert "updated" in tsk.stdout.lower()
    upd = cli_context["tsk"].get_task(2)
    assert upd["state"] == "Completed"

def test_delete_task(cli_context):
    tsk = runner.invoke(cli_app, [
        "tsk", "delete_task",
        "--task_id", "2"
    ], obj=cli_context)
    assert tsk.exit_code == 0
    chk = runner.invoke(cli_app, [
        "tsk", "list_tasks"
    ], obj=cli_context)
    assert "Second Task" not in chk.stdout

def test_get_tasks_due_today(cli_context):
    tsk = runner.invoke(cli_app, [
        "tsk", "get_tasks_due_today",
        "--today", "11/15/2024"
    ], obj=cli_context)
    assert tsk.exit_code == 0
    assert "Third Task" not in tsk.stdout

def test_get_tasks_due_on(cli_context):
    tsk = runner.invoke(cli_app, [
        "tsk", "get_tasks_due_on",
        "--date", "11/15/2024"
    ], obj=cli_context)
    assert tsk.exit_code == 0
    assert "" in tsk.stdout

def test_get_tasks_due_on_or_before(cli_context):
    tsk = runner.invoke(cli_app, [
        "tsk", "get_tasks_due_on_or_before",
        "--date", "11/15/2024"
    ], obj=cli_context)
    assert tsk.exit_code == 0
    assert "First Task" in tsk.stdout
    assert "Second Task" in tsk.stdout
    assert "Third Task" not in tsk.stdout

def test_get_tasks_with_progress(cli_context):
    # Add another one with 30% progress
    tsk = runner.invoke(cli_app, [
        "tsk", "add_task",
        "--title", "Test Task just started",
        "--description", "Just testing...",
        "--due_date", "11/14/2024", 
        "--progress", "30",
    ], obj=cli_context)
    assert tsk.exit_code == 0
    
    tsk = runner.invoke(cli_app, [
        "tsk", "get_tasks_with_progress",
        "--min_progress", "25",
        "--max_progress", "50"
    ], obj=cli_context)
    assert tsk.exit_code == 0
    assert "First Task" not in tsk.stdout
    assert "Test Task" in tsk.stdout
    assert "Second Task" in tsk.stdout
    assert "Third Task" not in tsk.stdout

def test_get_tasks_by_state(cli_context):
    tsk = runner.invoke(cli_app, [
        "tsk", "get_tasks_by_state",
        "--state", "Prog.*"
    ], obj=cli_context)
    assert tsk.exit_code == 0
    assert "Second Task" in tsk.stdout

def test_get_tasks_by_state_default_state(cli_context):
    tsk = runner.invoke(cli_app, [
        "tsk", "get_tasks_by_state"
    ], obj=cli_context)
    assert tsk.exit_code == 0
    assert "First Task" in tsk.stdout
    assert "Second Task" not in tsk.stdout
    assert "Third Task" not in tsk.stdout

# -------------------------
#           Contacts
# -------------------------
def test_add_and_list_contact(cli_context):
    ac = runner.invoke(cli_app, [
        "ctc", "add_contact",
        "--first", "Jane",
        "--last",  "Doe",
        "--email", "jane@example.com"
    ], obj=cli_context)
    assert ac.exit_code == 0
    assert "added" in ac.stdout

    lc = runner.invoke(cli_app, ["ctc", "list_contacts"], obj=cli_context)
    assert lc.exit_code == 0
    assert "Jane" in lc.stdout
    assert "Alice" in lc.stdout

    with open(cli_context["ctc"].state_file) as f:
        cts = json.load(f)
    assert any(c["first_name"] == "Jane" for c in cts.values())

def test_update_contact(cli_context):
    uc = runner.invoke(cli_app, [
        "ctc", "update_contact",
        "--contact_id", "2",
        "--company", "Acme Anvils"
    ], obj=cli_context)
    assert uc.exit_code == 0
    lc = cli_context["ctc"].get_contact(2)
    assert "Alice" == lc["first_name"]
    assert "Acme Anvils" == lc["company"]

def test_delete_contact(cli_context):
    uc = runner.invoke(cli_app, [
        "ctc", "delete_contact",
        "--contact_id", "3"
    ], obj=cli_context)
    assert uc.exit_code == 0
    assert "Smythe" not in uc.stdout

def test_search_contacts(cli_context):
    uc = runner.invoke(cli_app, [
        "ctc", "search_contacts",
        "--query", "Sm.th"
    ], obj=cli_context)
    assert uc.exit_code == 0
    assert "Smith" in uc.stdout
    assert "Smythe" in uc.stdout
    assert "Bob" not in uc.stdout

# -------------------------
#           Contacts
# -------------------------
def test_raw_bridge(cli_context):
    runner.invoke(cli_app, [
        "cal", "add_event",
        "--title", "X", "--date", "06/30/2025 12:00"
    ], obj=cli_context)

    raw = runner.invoke(cli_app, ["raw", "cal.list_events()"], obj=cli_context)
    assert raw.exit_code == 0
    # should be valid JSON array containing our event
    parsed = json.loads(raw.stdout)
    assert isinstance(parsed, dict)
    assert parsed.keys().__len__() == 4