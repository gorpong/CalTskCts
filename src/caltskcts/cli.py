# cli.py - Typer-based CLI for CalTskCts
import json
from typing import Any, Optional, List
import typer
from pathlib import Path
from caltskcts.dispatch_utils import dispatch_command
from caltskcts.import_export import (
    export_contacts_csv, import_contacts_csv, 
    import_contacts_vcard, export_contacts_vcard,
    export_events_ics,  import_events_ics,
    export_tasks_csv,  import_tasks_csv
)
from caltskcts.calendars import Calendar
from caltskcts.contacts  import Contacts
from caltskcts.tasks     import Tasks
from caltskcts.config    import (
    get_database_uri, 
    get_calendar_uri, 
    get_contacts_uri, 
    get_tasks_uri
)

app = typer.Typer(
    help="Calendar, Tasks, and Contacts Manager", 
    context_settings={"obj": {}},
    invoke_without_command=True
)

@app.callback()
def main(
    ctx: typer.Context,
    file: bool = typer.Option(
        False, "--file", "-f",
        help="Use default JSON backend."
    ),
    db: bool = typer.Option(
        False, "--db", "-d",
        help="Use SQLite backend (not JSON files)."
    ),
    db_path: str = typer.Option(
        get_database_uri(), "--db-path", "--path",
        help="(*) Path to the SQLite DB file (or default if not provided)."
    )
):
    """
    CLI entry point. Initialize storage. Exactly one of --file or --db allowed,
    otherwise fallback to JSON files (default).
    Needed so Flask/Click/Typer knows this is a group and can accept commands.
    """
    if file and db:
        typer.echo("⛔️  Please specify only one of --file or --db", err=True)
        raise typer.Exit(1)
    
    if not file and not db:
        file = True
    
    if db:
        state_uri = db_path.strip()
        if "://" not in state_uri:
            state_uri = f"sqlite:///{state_uri}"
        cal_uri = ctc_uri = tsk_uri = state_uri
        typer.echo(f"🗄 Using DB backend: {state_uri}")
    else:
        # Default to JSON files (whether --files specified or not)
        cal_uri = get_calendar_uri()
        ctc_uri = get_contacts_uri()
        tsk_uri = get_tasks_uri()
        typer.echo(f"🔣 Using JSON backend.")

    ctx.obj["cal"] = Calendar(cal_uri)
    ctx.obj["tsk"] = Tasks(tsk_uri)
    ctx.obj["ctc"] = Contacts(ctc_uri)
    ctx.obj["result"] = {}

# Sub-applications for grouping commands
cal_app = typer.Typer(help="Commands for calendar events")
tsk_app = typer.Typer(help="Commands for tasks")
ctc_app = typer.Typer(help="Commands for contacts")

# ------- Calendar Commands -------
@cal_app.command("add_event", help="Add a new event to the calendar")
def add_event(
    ctx: typer.Context,
    title: str = typer.Option(..., "--title", "-t", help="Event title"),
    date: str = typer.Option(..., "--date", "-d", help="MM/DD/YYYY HH:MM"),
    duration: Optional[int] = typer.Option(None, "--duration", "-D", help="Duration in minutes"),
    users: Optional[List[str]] = typer.Option(None, "--users", "--user", "-u", help="Users to invite"),
    id: Optional[int] = typer.Option(None, "--event_id", "--id", "-i", help="Specific ID to use (error if exists)")
):
    """Add a calendar event."""
    cal = ctx.obj["cal"]
    params: dict[str, Any] = {
        k: v for k, v in {
        "title": title,
        "date": date,
        "duration": duration,
        "users": users,
        "event_id": id
        }.items() if v is not None
    }
    result = cal.add_event(**params)
    typer.echo(result)


@cal_app.command("list_events", help="Get a list of all events in the calendar")
def list_events(ctx: typer.Context):
    cal = ctx.obj["cal"]
    events = cal.list_events()
    typer.echo(events)

@cal_app.command("get_event", help="Get a specific calendar event based on its ID")
def get_event(
    ctx: typer.Context,
    id: int = typer.Option(..., "--event_id", "--id", "-i", help="The ID for the calendar event")
):
    cal = ctx.obj["cal"]
    events = cal.list_events()
    typer.echo(events)

@cal_app.command("update_event", help="Update an existing event")
def update_event(
    ctx: typer.Context,
    event_id: int = typer.Option(..., "--event_id", "--id", "-i", help="Event ID"),
    title: Optional[str] = typer.Option(None, "--title", "-t", help="Event title"),
    date: Optional[str] = typer.Option(None, "--date", "-d", help="MM/DD/YYYY HH:MM"),
    duration: Optional[int] = typer.Option(None, "--duration", "-D", help="Duration in minutes"),
    users: Optional[List[str]] = typer.Option(None, "--users", "-u", help="Users to invite")
    
):
    cal = ctx.obj["cal"]
    params: dict[str, Any] = {
        k: v for k, v in {
        "event_id": event_id,
        "title": title,
        "date": date,
        "duration": duration,
        "users": users
        }.items() if v is not None
    }
    events = cal.update_event(**params)
    typer.echo(events)
    
@cal_app.command("delete_event", help="Delete a calendar event")
def delete_event(
    ctx: typer.Context,
    id: int = typer.Option(..., "--event_id", "--id", "-i", help="Event ID to delete")
):
    """Delete an existing event."""
    cal = ctx.obj["cal"]
    events = cal.delete_event(event_id = id)
    typer.echo(events)

@cal_app.command("get_events_by_date", help="Get all events on a specific date")
def get_events_by_date(
    ctx: typer.Context,
    date: str = typer.Option(..., "--date", "-d", help="Date in MM/DD/YYYY format")
):
    """Get all of the events from a particular date."""
    cal = ctx.obj["cal"]
    events = cal.get_events_by_date(date = date)
    typer.echo(events)

@cal_app.command("get_events_between", help="Get all events between two dates (inclusive).")
def get_events_between(
    ctx: typer.Context,
    start: str = typer.Option(..., "--start_datetime", "--start", "-s", help="Start date/time in MM/DD/YYYY [HH:MM] format"),
    end: str = typer.Option(..., "--end_datetime", "--end", "-e", help="End date/time in MM/DD/YYYY [HH:MM] format")
):
    cal = ctx.obj["cal"]
    events = cal.get_events_between(start_datetime=start, end_datetime=end)
    typer.echo(events)

@cal_app.command("find_next_available", help="Find the next available time slot.")
def find_next_available(
    ctx: typer.Context,
    start: str = typer.Option(..., "--start_datetime", "--start", "-s", help="Starting point to search from (MM/DD/YYYY HH:MM)"),
    duration: Optional[int] = typer.Option(None, "--duration_minutes", "--duration", "--min", "-d", "-m", help="Required duration in minutes")
):
    cal = ctx.obj["cal"]
    events = cal.find_next_available(start_datetime=start, duration_minutes=duration) if duration is not None else cal.find_next_available(start_datetime=start)
    typer.echo(events)

# ------- Task Commands -------
@tsk_app.command("get_task", help="Get a specific task based on the task's ID")
def get_task(
    ctx: typer.Context,
    id: int = typer.Option(..., "--task_id", "--id", "-i", help="The ID for the task")
):
    tsk = ctx.obj["tsk"]
    result = tsk.get_task(task_id=id)
    typer.echo(result)

@tsk_app.command("add_task", help="Add a Task to the system")
def add_task(
    ctx: typer.Context,
    title: str = typer.Option(..., "--title", "-t", help="The title of the new task"),
    description: str = typer.Option("", "--description", "--desc", "-d", help="The description for the task"),
    due_date: Optional[str] = typer.Option(None, "--due_date", "--due", help="The due date for the task (MM/DD/YYYY)"),
    progress: Optional[float] = typer.Option(None, "--progress", help="Progress (0-100)"),
    state_str: Optional[str] = typer.Option(None, "--state", help="The state (In Progress, Completed, ...)"),
    task_id: Optional[int] = typer.Option(None, "--task_id", "--id", "-i", help="Optional Task ID to add (error if it exists)")
):
    tsk = ctx.obj["tsk"]
    params: dict[str, Any] = {
        k: v for k, v in {
        "title": title,
        "description": description,
        "due_date": due_date,
        "progress": progress,
        "state": state_str,
        "task_id": task_id
        }.items() if v is not None
    }
    result = tsk.add_task(**params)
    typer.echo(result)

@tsk_app.command("delete_task", help="Delete a task")
def delete_task(
    ctx: typer.Context,
    id: int = typer.Option(..., "--task_id", "--id", "-i", help="The ID of the task")
):
    tsk = ctx.obj["tsk"]
    result = tsk.delete_task(task_id=id)
    typer.echo(result)

@tsk_app.command("update_task", help="Update an existing task")
def update_task(
    ctx: typer.Context,
    id: int = typer.Option(..., "--task_id", "--id", "-i", help="The ID of the task to update"),
    title: Optional[str] = typer.Option(None, "--title", "-t", help="The new title"),
    desc: Optional[str] = typer.Option("", "--description", "--desc", "-d", help="The new description"),
    date: Optional[str] = typer.Option(None, "--due_date", "--due", help="New Due Date (MM/DD/YYYY)"),
    progress: Optional[float] = typer.Option(None, "--progress"),
    state: Optional[str] = typer.Option(None, "--state")
):
    tsk = ctx.obj["tsk"]
    params: dict[str, Any] = {
        k: v for k, v in {
        "task_id": id,
        "title": title,
        "description": desc,
        "due_date": date,
        "progress": progress,
        "state": state
        }.items() if v is not None
    }
    result = tsk.update_task(**params)
    typer.echo(result)

@tsk_app.command("get_tasks_due_today", help="Get all tasks due today or before")
def get_tasks_due_today(
    ctx: typer.Context,
    today: Optional[str] = typer.Option(None, "--today", help="Date in MM/DD/YYYY format, defaults to current date")
):
    tsk = ctx.obj["tsk"]
    result = tsk.get_tasks_due_today(today=today) if today is not None else tsk.get_tasks_due_today()
    typer.echo(result)

@tsk_app.command("get_tasks_due_on", help="Get all tasks due on a specific date")
def get_tasks_due_on(
    ctx: typer.Context,
    date: str = typer.Option(..., "--date", help="Date in MM/DD/YYYY format")
):
    tsk = ctx.obj["tsk"]
    result = tsk.get_tasks_due_on(date=date)
    typer.echo(result)

@tsk_app.command("get_tasks_due_on_or_before", help="Get all tasks due on or before a date")
def get_tasks_due_on_or_before(
    ctx: typer.Context,
    date: str = typer.Option(..., "--date", help="Date in MM/DD/YYYY format")
):
    tsk = ctx.obj["tsk"]
    result = tsk.get_tasks_due_on_or_before(date=date)
    typer.echo(result)

@tsk_app.command("get_tasks_with_progress", help="Get tasks filtered by progress range.")
def get_tasks_with_progress(
    ctx: typer.Context,
    min: float = typer.Option(..., "--min_progress", "--min", help="Minimum progress value"),
    max: float = typer.Option(..., "--max_progress", "--max", help="Maximum progress value")
):
    tsk = ctx.obj["tsk"]
    result = tsk.get_tasks_with_progress(min_progress=min, max_progress=max)
    typer.echo(result)

@tsk_app.command("get_tasks_by_state", help="Get tasks matching a state pattern")
def get_tasks_by_state(
    ctx: typer.Context,
    state: Optional[str] = typer.Option(None, "--state", "--st", help="State or state pattern to match")
):
    tsk = ctx.obj["tsk"]
    result = tsk.get_tasks_by_state(state=state) if state is not None else tsk.get_tasks_by_state()
    typer.echo(result)

@tsk_app.command("list_tasks", help="List all tasks")
def list_tasks(ctx: typer.Context):
    tsk = ctx.obj["tsk"]
    tasks = tsk.list_tasks()
    typer.echo(tasks)

# ------- Contact Commands -------
@ctc_app.command("add_contact", help="Add a contact")
def add_contact(
    ctx: typer.Context,
    first_name: str = typer.Option(..., "--first", "-f", help="Contact's first name"),
    last_name: str = typer.Option(..., "--last", "-l", help="Contact's last name"),
    email: Optional[str] = typer.Option(None, "--email", "-e", help="Email address"),
    company: Optional[str] = typer.Option(None, "--company", "--comp", help="Company name"),
    title: Optional[str] = typer.Option(None, "--title", "-t", help="Job title"),
    work_phone: Optional[str] = typer.Option(None, "--work_phone", "--work", "-w", help="Work phone number"),
    mobile_phone: Optional[str] = typer.Option(None, "--moble_phone", "--mobile", "-m", help="Mobile phone number"),
    home_phone: Optional[str] = typer.Option(None, "--home_phone", "--home", "-h", help="Home phone number"),
    id: Optional[int] = typer.Option(None, "--contact_id", "--id", help="Optional specific ID to use")
):
    ctc = ctx.obj["ctc"]
    params: dict[str, Any] = {
        k: v for k, v in {
            "contact_id": id,
            "first_name": first_name,
            "last_name": last_name,
            "title": title,
            "company": company,
            "work_phone": work_phone,
            "mobile_phone": mobile_phone,
            "home_phone": home_phone,
            "email": email
        }.items() if v is not None
    }
    result = ctc.add_contact(**params)
    typer.echo(result)

@ctc_app.command("update_contact", help="Update an existing contact.")
def update_contact(
    ctx: typer.Context,
    id: int = typer.Option(..., "--contact_id", "--id", help="The ID of the contact to update"),
    first_name: Optional[str] = typer.Option(None, "--first_name", "--fname", "--first", help="New first name"),
    last_name: Optional[str] = typer.Option(None, "--last_name", "--lname", "--last", help="New last name"),
    title: Optional[str] = typer.Option(None, "--title", help="New job title"),
    company: Optional[str] = typer.Option(None, "--company", "--comp", help="New company name"),
    work: Optional[str] = typer.Option(None, "--work_phone", "--work", help="New work phone"),
    mobile: Optional[str] = typer.Option(None, "--mobile_phone", "--mobile", help="New mobile phone"),
    home: Optional[str] = typer.Option(None, "--home_phone", "--home", help="New home phone"),
    email: Optional[str] = typer.Option(None, "--email", "--mail", help="New email address")
):
    ctc = ctx.obj["ctc"]
    params: dict[str, Any] = {
        k: v for k, v in {
            "contact_id": id,
            "first_name": first_name,
            "last_name": last_name,
            "title": title,
            "company": company,
            "work_phone": work,
            "mobile_phone": mobile,
            "home_phone": home,
            "email": email
        }.items() if v is not None
    }
    result = ctc.update_contact(**params)
    typer.echo(result)

@ctc_app.command("delete_contact", help="Delete a contact.")
def delete_contact(
    ctx: typer.Context,
    id: int = typer.Option(..., "--contact_id", "--id", help="ID of contact to delete")
):
    ctc = ctx.obj["ctc"]
    result = ctc.delete_contact(contact_id=id)
    typer.echo(result)

@ctc_app.command("search_contacts", help="Search contacts by name, email, or phone number")
def search_contacts(
    ctx: typer.Context,
    qry: str = typer.Option(..., "--query", "--qry", "-q", help="Search query (regex pattern)")
):
    ctc = ctx.obj["ctc"]
    result = ctc.search_contacts(query=qry)
    typer.echo(result)

@ctc_app.command("list_contacts", help="List all contacts")
def list_contacts(ctx: typer.Context):
    ctc = ctx.obj["ctc"]
    contacts = ctc.list_contacts()
    typer.echo(contacts)

@ctc_app.command("get_contact", help="Get a specific contact based on the contact ID.")
def get_contact(
    ctx: typer.Context,
    id: int = typer.Option(..., "--contact_id", "--id", help="The integer ID for the contact")
):
    ctc = ctx.obj["ctc"]
    contacts = ctc.get_contact(contact_id=id)
    typer.echo(contacts)

# ------- Link the sub-commands -------
app.add_typer(cal_app, name="cal")
app.add_typer(tsk_app, name="tsk")
app.add_typer(ctc_app, name="ctc")

# ------- Root level commands -------
@app.command("raw", help="Raw commands to bridge when CLI doesn't yet support, e.g, (raw 'cal.find_next_available(start_datetime='01/01/1990 10:30')")
def raw(
    ctx: typer.Context,
    command: str = typer.Argument(..., help="Command to execute, e.g. 'cal.get_event(event_id=1)'")
):
    """Execute raw REPL-style command (e.g. cal.list_events())"""
    try:
        result = dispatch_command(command, ctx.obj)
        typer.echo(json.dumps(result, indent=2, default=str))
    except Exception as e:
        typer.echo(f"Error: {e}")

@app.command("export", help="Export contacts/events/tasks to CSV/ICS")
def export(
    ctx: typer.Context,
    what: str = typer.Argument(..., help="contacts | events | tasks"),
    fmt:  str = typer.Option(..., "--format", "-f", help="csv | ics | vcard"),
    out:  Path = typer.Option(..., "--output", "-o", help="Output file"),
):
    """
    Export contacts/events/tasks into the given format.
    """
    if what == "contacts" and fmt == "csv":
        export_contacts_csv(ctx.obj["ctc"].state_uri, out)
    elif what == "contacts" and fmt == "vcard":
        export_contacts_vcard(ctx.obj["ctc"].state_uri, out)
    elif what == "events" and fmt == "ics":
        export_events_ics(ctx.obj["cal"].state_uri, out)
    elif what == "tasks" and fmt == "csv":
        export_tasks_csv(ctx.obj["cal"].state_uri, out)
    else:
        typer.echo("Unsupported combination", err=True)
        raise typer.Exit(1)

@app.command("import", help="Import contacts/events/tasks from CSV/ICS")
def import_(
    ctx: typer.Context,
    what: str = typer.Argument(..., help="contacts | events | tasks"),
    in_:   Path = typer.Argument(..., help="Input file"),
):
    """
    Import from CSV/ICS into your state.
    """
    if what == "contacts":
        if in_.suffix.lower() == ".vcf":
            ids = import_contacts_vcard(ctx.obj["ctc"].state_uri, in_)
        else:
            ids = import_contacts_csv(ctx.obj["ctc"].state_uri, in_)
    elif what == "events":
        ids = import_events_ics(ctx.obj["cal"].state_uri, in_)
    elif what == "tasks":
        ids = import_tasks_csv(ctx.obj["tsk"].state_uri, in_)
    else:
        typer.echo("Unsupported type", err=True)
        raise typer.Exit(1)

    typer.echo(f"Imported IDs: {ids}")


if __name__ == "__main__":
    app()
