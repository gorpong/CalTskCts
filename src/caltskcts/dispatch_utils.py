from typing import Dict, Any, List
from caltskcts.logger import get_logger

logger = get_logger(__name__)

def get_command_map() -> Dict[str, List[str]]:
    """Build command map for auto-completion"""
    return {
        "cal": [
            "cal.add_event(title='', date='', duration=-1, users=[])",
            "cal.find_next_available(start_datetime='', duration_minutes=-1)",
            "cal.delete_event(event_id=-1)",
            "cal.get_event(event_id=-1)",
            "cal.list_events()",
            "cal.get_events_by_date(date='')",
            "cal.get_events_between(start_datetime='', end_datetime='')",
            "cal.update_event(event_id=-1, title='', date='', duration=-1, users=[])",
        ],
        "tsk": [
            "tsk.add_task(title='', description='', due_date='', progress=-1.0, state='Not Started')",
            "tsk.update_task(task_id=-1, title='', description='', due_date='', progress=-1.0, state='')",
            "tsk.delete_task(task_id=-1)",
            "tsk.list_tasks()",
            "tsk.get_task(task_id=-1)",
            "tsk.get_tasks_due_today()",
            "tsk.get_tasks_due_on(date='')",
            "tsk.get_tasks_due_on_or_before(date='')",
            "tsk.get_tasks_with_progress(min_progress=0.0, max_progress=100.0)",
            "tsk.get_tasks_by_state(state='Not Started')",
        ],
        "ctc": [
            "ctc.list_contacts()",
            "ctc.add_contact(first_name='', last_name='', title='', company='', work_phone='', mobile_phone='', home_phone='', email='')",
            "ctc.update_contact(contact_id=-1, first_name='', last_name='', company='', title='', work_phone='', mobile_phone='', home_phone='', email='')",
            "ctc.delete_contact(contact_id=-1)",
            "ctc.get_contact(contact_id=-1)",
            "ctc.search_contacts(query='')",
        ],
    }


def dispatch_command(command: str, context: Dict[str, Any]) -> Any:
    """Safely execute a command in the given context"""
    logger.debug(f"Dispatching command: {command}")
    allowed_prefixes = [f"{key}." for key in context.keys()]
    if not any(command.startswith(prefix) for prefix in allowed_prefixes):
        error_msg = f"Invalid command. Must use one of: {', '.join(context.keys())}"
        logger.warning(f"Command validation failed: {error_msg}")
        raise ValueError(error_msg)
    parts = command.split(".", 1)
    if len(parts) != 2:
        error_msg = "Invalid command format"
        logger.warning(f"Command parsing failed: {error_msg}")
        raise ValueError(error_msg)
    obj_name, method_call = parts
    obj = context.get(obj_name)
    if not obj:
        error_msg = f"Unknown object: {obj_name}"
        logger.warning(f"Command validation failed: {error_msg}")
        raise ValueError(error_msg)
    method_name = method_call.split("(", 1)[0].strip()
    if not hasattr(obj, method_name):
        error_msg = f"Unknown method: {method_name}"
        logger.warning(f"Command validation failed: {error_msg}")
        raise ValueError(error_msg)
    method = getattr(obj, method_name)
    if not callable(method):
        error_msg = f"{method_name} is not callable"
        logger.warning(f"Command validation failed: {error_msg}")
        raise ValueError(error_msg)
    local_context = {**context}
    exec_str = f"result[0] = {command}"
    try:
        logger.info(f"Executing command: {command}")
        exec(exec_str, {"__builtins__": {}}, local_context)
        logger.debug("Command executed successfully")
        return local_context["result"][0]
    except Exception as e:
        logger.error(f"Command execution failed: {str(e)}")
        raise

