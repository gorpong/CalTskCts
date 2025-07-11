from typing import Dict, Any
from caltskcts.logger import get_logger

logger = get_logger(__name__)

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

