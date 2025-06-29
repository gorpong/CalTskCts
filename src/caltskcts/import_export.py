import re
import csv
from pathlib import Path
from typing import Any, Dict, List, Union
from datetime import datetime, date, timedelta

from caltskcts.contacts import Contacts
from caltskcts.calendars import Calendar
from caltskcts.tasks import Tasks
from caltskcts.schemas import ContactModel, EventModel, TaskModel

from icalendar import Calendar as ICalendar, Event as ICSEvent
import vobject

# --------------------
#   Helper functions
# --------------------
def _extract_id(msg: str) -> int:
    """
    Pulls the first integer out of a string like "Contact 42 added".
    Raises ValueError if none found.
    """
    m = re.search(r"\b(\d+)\b", msg)
    if not m:
        raise ValueError(f"Could not parse ID from message: {msg!r}")
    return int(m.group(1))


def _format_value(v: Any) -> str:
    """Serialize the datetime/date elements into strings"""
    if v is None:
        return ""
    if isinstance(v, datetime):
        return v.strftime("%m/%d/%Y %H:%M")
    if isinstance(v, date):
        return v.strftime("%m/%d/%Y")
    return str(v)

# --------------------
# CONTACTS ⇄ CSV
# --------------------

def export_contacts_csv(state_uri: str, out_path: Path) -> None:
    """
    Export all contacts from storage into a CSV file.

    Args:
        state_uri: URI of the contacts storage backend.
        out_path: Filesystem path where the CSV will be written.

    Returns:
        None

    Raises:
        ValueError: If the storage cannot be read or CSV write fails.
    """
    mgr = Contacts(state_uri)
    fields = list(ContactModel.model_fields.keys())
    header = ["id"] + fields

    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        for cid, raw in mgr.list_items().items():
            m = ContactModel.model_validate(raw)
            data = m.model_dump()
            row = [cid] + [_format_value(data.get(f)) for f in fields]
            writer.writerow(row)


def import_contacts_csv(state_uri: str, in_path: Path) -> List[int]:
    """
    Import contacts from a CSV file into storage.

    Args:
        state_uri: URI of the contacts storage backend.
        in_path: Filesystem path of the CSV file to read.

    Returns:
        A list of newly assigned contact IDs.

    Raises:
        ValueError: If CSV parsing fails or a contact record is invalid.
    """
    mgr = Contacts(state_uri)
    new_ids: List[int] = []

    with in_path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fld = reader.fieldnames or []
        if not fld or fld[0] != "id":
            raise ValueError("Contacts CSV must start with an 'id' column")
        schema_fields = fld[1:]

        for row in reader:
            cid = int(row["id"]) if row["id"].strip() else None

            payload: Dict[str,str] = {}
            for k in schema_fields:
                v = row[k].strip()
                if v == "":
                    continue
                payload[k] = v

            valid = ContactModel(**payload).model_dump()
            msg = mgr.add_contact(contact_id=cid, **valid)
            assigned = _extract_id(msg)
            new_ids.append(assigned)

    return new_ids

# --------------------
# CONTACTS ⇄ VCARD
# --------------------

def export_contacts_vcard(state_uri: str, out_path: Path) -> None:
    """
    Export all contacts from storage into a VCard (.vcf) file.

    Args:
        state_uri: URI of the contacts storage backend.
        out_path: Filesystem path where the VCard file will be written.

    Returns:
        None

    Raises:
        ValueError: If the storage cannot be read or VCard write fails.
    """
    mgr = Contacts(state_uri)
    contacts = mgr.list_items()

    with out_path.open("w", encoding="utf-8") as f:
        for cid, data in contacts.items():
            card = vobject.vCard()
            n = card.add("n")
            n.value = vobject.vcard.Name(
                family=data.get("last_name", "") or "",
                given=data.get("first_name", "") or ""
            )
            fn = card.add("fn")
            fn.value = f"{data.get('first_name','').strip()} {data.get('last_name','').strip()}".strip()

            # Email
            email_addr = data.get("email")
            if email_addr:
                em = card.add("email")
                em.value = email_addr
                em.type_param = "INTERNET"

            # Phone numbers
            for field, tp in (
                ("work_phone", "WORK"),
                ("mobile_phone", "CELL"),
                ("home_phone", "HOME"),
            ):
                number = data.get(field)
                if number:
                    tel = card.add("tel")
                    tel.value = number
                    tel.type_param = tp

            company = data.get("company")
            if company:
                org = card.add("org")
                org.value = [company]

            title = data.get("title")
            if title:
                jt = card.add("title")
                jt.value = title

            f.write(card.serialize())
            f.write("\n")

def import_contacts_vcard(state_uri: str, in_path: Path) -> List[int]:
    """
    Import contacts from a VCard (.vcf) file into storage.

    Args:
        state_uri: URI of the contacts storage backend.
        in_path: Filesystem path of the VCard file to read.

    Returns:
        A list of newly assigned contact IDs.

    Raises:
        ValueError: If VCard parsing fails or a contact record is invalid.
    """
    mgr = Contacts(state_uri)
    imported_ids: List[int] = []

    with in_path.open("r", encoding="utf-8") as f:
        for card in vobject.readComponents(f):
            data: dict[str, str] = {}

            # If it's got the new "N" then use, otherwise fallback to "FN"
            if hasattr(card, "n"):
                name = card.n.value
                data["first_name"] = name.given or ""
                data["last_name"]  = name.family or ""
            else:
                fn = getattr(card, "fn", None)
                if fn:
                    parts = fn.value.split(None, 1)
                    data["first_name"] = parts[0]
                    data["last_name"]  = parts[1] if len(parts) > 1 else ""

            if hasattr(card, "email"):
                data["email"] = card.email.value

            for tel in card.contents.get("tel", []):
                typ = tel.params.get("TYPE", tel.params.get("type", []) )
                typ = typ[0].upper() if isinstance(typ, list) else str(typ).upper()
                if "CELL" in typ:
                    data["mobile_phone"] = tel.value
                elif "WORK" in typ:
                    data["work_phone"] = tel.value
                elif "HOME" in typ:
                    data["home_phone"] = tel.value

            if hasattr(card, "org"):
                org = card.org.value
                if isinstance(org, list) and org:
                    data["company"] = org[0]

            if hasattr(card, "title"):
                data["title"] = card.title.value

            result_str = mgr.add_contact(**data)
            assigned = _extract_id(result_str)
            imported_ids.append(assigned)


    return imported_ids

# --------------------
# EVENTS ⇄ ICS
# --------------------

def export_events_ics(state_uri: str, out_path: Path) -> None:
    """
    Export all calendar events from storage into an iCalendar (.ics) file.

    Args:
        state_uri: URI of the calendar storage backend.
        out_path: Filesystem path where the .ics file will be written.

    Returns:
        None

    Raises:
        ValueError: If the storage cannot be read or ICS serialization fails.
    """
    mgr = Calendar(state_uri)
    cal = ICalendar()

    for eid, raw in mgr.list_items().items():
        m = EventModel.model_validate(raw)
        data = m.model_dump()

        ie = ICSEvent()
        ie.add("uid", f"event-{eid}@caltskc")
        ie.add("summary", data["title"])
        dt = data["date"]
        if dt is not None:
            if isinstance(dt, str):
                dt = datetime.strptime(dt, "%m/%d/%Y %H:%M")
            ie.add("dtstart", dt)
        dur = data["duration"]
        if dur is not None:
            try:
                minutes = int(dur)
            except (ValueError, TypeError):
                raise ValueError(f"Invalid duration: {dur|r}")
            ie.add("dtend", dt + timedelta(minutes=minutes))
        for u in data.get("users") or []:
            ie.add("attendee", u)
        cal.add_component(ie)

    with out_path.open("wb") as f:
        f.write(cal.to_ical())

def import_events_ics(state_uri: str, in_path: Path) -> List[int]:
    """
    Import VEVENTs from an iCalendar (.ics) file into storage.

    Args:
        state_uri: URI of the calendar storage backend.
        in_path: Filesystem path of the .ics file to read.

    Returns:
        A list of newly assigned event IDs.

    Raises:
        ValueError: If the .ics is malformed or an event record is invalid.
    """
    mgr = Calendar(state_uri)
    imported: List[int] = []

    try:
        raw = in_path.read_bytes()
        ics = ICalendar.from_ical(raw)
    except ValueError:
        return []

    for comp in ics.walk():
        if comp.name != "VEVENT":
            continue

        uid = str(comp.get("uid", ""))
        m = re.match(r"^event-(\d+)@", uid)
        if not m:
            event_id = None # Fall back to get new if not our previous export
        else:
            event_id = int(m.group(1))

        title    = str(comp.get("summary", ""))
        dtstart  = comp.decoded("dtstart")
        date_str = dtstart.strftime("%m/%d/%Y %H:%M")

        # If no "duration" but "dtend" then try to compute
        try:
            dur_td = comp.decoded("duration")
        except KeyError:
            dtend = comp.decoded("dtend")
            dur_td = (dtend - dtstart) if dtend else None
        minutes = int(dur_td.total_seconds() // 60) if dur_td else None

        att = comp.get("attendee", [])
        if isinstance(att, list):
            users = [str(a) for a in att]
        else:
            users = [str(att)]

        msg = mgr.add_event(
            title=title,
            date=date_str,
            duration=minutes,
            users=users,
            event_id=event_id,
        )
        imported.append(_extract_id(msg))

    return imported

# --------------------
# TASKS ⇄ CSV
# --------------------

def export_tasks_csv(state_uri: str, out_path: Path) -> None:
    """
    Export all tasks from storage into a CSV file.

    Args:
        state_uri: URI of the tasks storage backend.
        out_path: Filesystem path where the CSV will be written.

    Returns:
        None

    Raises:
        ValueError: If the storage cannot be read or CSV write fails.
    """
    mgr = Tasks(state_uri)
    fields = list(TaskModel.model_fields.keys())
    header = ["id"] + fields

    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        for tid, raw in mgr.list_items().items():
            m = TaskModel.model_validate(raw)
            data = m.model_dump()
            row = [tid] + [_format_value(data.get(f)) for f in fields]
            writer.writerow(row)

def import_tasks_csv(state_uri: str, in_path: Path) -> List[int]:
    """
    Import tasks from a CSV file into storage.

    Args:
        state_uri: URI of the tasks storage backend.
        in_path: Filesystem path of the CSV file to read.

    Returns:
        A list of newly assigned task IDs.

    Raises:
        ValueError: If CSV parsing fails or a task record is invalid.
    """
    mgr = Tasks(state_uri)
    new_ids: List[int] = []

    with in_path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fld = reader.fieldnames or []
        if not fld or fld[0] != "id":
            raise ValueError("Tasks CSV must start with an 'id' column")
        schema = fld[1:]

        for row in reader:
            tid = int(row["id"]) if row["id"].strip() else None

            kwargs: Dict[str, Union[str, float]] = {}
            for k in schema:
                v = row[k].strip()
                if k == "desc":
                    kwargs["description"] = v
                elif k == "dueDate":
                    if v:
                        kwargs["due_date"] = v
                elif k == "progress":
                    if v:
                        kwargs["progress"] = float(v)
                elif k == "state":
                    if v:
                        kwargs["state"] = v
                elif k == "title":
                    if v:
                        kwargs["title"] = v

            msg = mgr.add_task(task_id=tid, **kwargs)
            assigned = _extract_id(msg)
            new_ids.append(assigned)

    return new_ids
