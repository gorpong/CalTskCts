# cli.py - Typer-based CLI for CalTskCts
import json
from typing import Optional, List
import typer
from caltskcts.dispatch_utils import dispatch_command

app = typer.Typer(help="Calendar, Tasks, and Contacts Manager", context_settings={"obj": {}})

# Sub-applications for grouping commands
cal_app = typer.Typer(help="Commands for calendar events")
tsk_app = typer.Typer(help="Commands for tasks")
ctc_app = typer.Typer(help="Commands for contacts")

app.add_typer(cal_app, name="cal")
app.add_typer(tsk_app, name="tsk")
app.add_typer(ctc_app, name="ctc")

@app.callback()
def main(ctx: typer.Context):
    """
    CLI entry point. All storage and stuff passed by __main__, and ctx.obj as well
    """
    pass

# ------- Calendar Commands -------
@cal_app.command("add_event", help="Add a new event to the calendar")
def add_event(
    ctx: typer.Context,
    title: str = typer.Option(..., "--title", "-t", help="Event title"),
    date: str = typer.Option(..., "--date", "-d", help="MM/DD/YYYY HH:MM"),
    duration: int = typer.Option(30, "--duration", "-D", help="Duration in minutes"),
    users: List[str] = typer.Option([], "--user", "-u", help="Users to invite")
):
    """Add a calendar event."""
    cal = ctx.obj["cal"]
    result = cal.add_event(title=title, date=date, duration=duration, users=users)
    typer.echo(result)

@cal_app.command("list_events")
def list_events(ctx: typer.Context):
    """List all calendar events."""
    cal = ctx.obj["cal"]
    events = cal.list_events()
    typer.echo(events)

# ------- Task Commands -------
@tsk_app.command("add_task")
def add_task(
    ctx: typer.Context,
    title: str = typer.Option(..., "--title", "-t"),
    description: str = typer.Option("", "--desc", "-d"),
    due_date: Optional[str] = typer.Option(None, "--due", help="MM/DD/YYYY"),
    progress: float = typer.Option(0.0, "--progress"),
    state_str: str = typer.Option("Not Started", "--state")
):
    """Add a new task."""
    tsk = ctx.obj["tsk"]
    result = tsk.add_task(title=title, description=description, due_date=due_date, progress=progress, state=state_str)
    typer.echo(result)

@tsk_app.command("list_tasks")
def list_tasks(ctx: typer.Context):
    """List all tasks."""
    tsk = ctx.obj["tsk"]
    tasks = tsk.list_tasks()
    typer.echo(tasks)

# ------- Contact Commands -------
@ctc_app.command("add_contact")
def add_contact(
    ctx: typer.Context,
    first_name: str = typer.Option(..., "--first", "-f"),
    last_name: str = typer.Option(..., "--last", "-l"),
    email: Optional[str] = typer.Option(None, "--email", "-e"),
    company: Optional[str] = typer.Option(None),
    title: Optional[str] = typer.Option(None),
    work_phone: Optional[str] = typer.Option(None),
    mobile_phone: Optional[str] = typer.Option(None),
    home_phone: Optional[str] = typer.Option(None)
):
    """Add a new contact."""
    ctc = ctx.obj["ctc"]
    result = ctc.add_contact(
        first_name=first_name,
        last_name=last_name,
        title=title,
        company=company,
        work_phone=work_phone,
        mobile_phone=mobile_phone,
        home_phone=home_phone,
        email=email
    )
    typer.echo(result)

@ctc_app.command("list_contacts")
def list_contacts(ctx: typer.Context):
    """List all tasks."""
    ctc = ctx.obj["ctc"]
    contacts = ctc.list_contacts()
    typer.echo(contacts)

# ------- Raw Bridge Command -------
@app.command("raw")
def raw(
    ctx: typer.Context,
    command: str = typer.Argument(..., help="Command to execute, e.g. cal.get_event(event_id=1)")
):
    """Execute raw REPL-style command (e.g. cal.list_events())"""
    try:
        result = dispatch_command(command, ctx.obj)
        typer.echo(json.dumps(result, indent=2, default=str))
    except Exception as e:
        typer.echo(f"Error: {e}")

if __name__ == "__main__":
    app()
