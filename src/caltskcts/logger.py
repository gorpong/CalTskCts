"""
Logger module for CalTskCts application.
Provides centralized logging configuration for console and file output.
"""

import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from typing import Optional, Dict, Any, Union, MutableMapping

# Import the configuration setup
from caltskcts.logger_config import setup_logging

# Constants - Used as fallback if config file is not available
DEFAULT_ROOT_LOGGER = "CalTskCts"
DEFAULT_LOG_LEVEL = logging.INFO
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DEFAULT_LOG_DIR = "logs"
DEFAULT_LOG_FILENAME = "caltskcts.log"
MAX_LOG_SIZE = 5 * 1024 * 1024  # 5 MB
BACKUP_COUNT = 5  # Keep 5 backup logs

# Create the singleton logger instance
_logger: Optional[logging.Logger] = None
_is_configured: bool = False

def get_logger(name: str = DEFAULT_ROOT_LOGGER) -> logging.Logger:
    """
    Get or create a configured logger instance.
    
    Args:
        name: Logger name (usually the module name)
        
    Returns:
        Configured logger instance
    """
    global _logger, _is_configured
    
    # Configure logging only once
    if not _is_configured:
        try:
            # Try to configure from file
            setup_logging()
            _is_configured = True
        except Exception as e:
            # Fallback to basic configuration
            print(f"Warning: Could not configure logging from file: {e}")
            _configure_manual_logging()
            _is_configured = True
    
    # Get a logger with the specified name
    if name == DEFAULT_ROOT_LOGGER and _logger is not None:
        return _logger
    
    logger = logging.getLogger(name)
    
    # Store the root application logger
    if name == DEFAULT_ROOT_LOGGER:
        _logger = logger
    
    return logger

def _configure_manual_logging() -> None:
    """Configure logging manually when config file is not available"""
    root_logger = logging.getLogger()
    root_logger.setLevel(DEFAULT_LOG_LEVEL)
    
    # Remove any existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create formatter
    formatter = logging.Formatter(DEFAULT_LOG_FORMAT)
    
    # Add console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(DEFAULT_LOG_LEVEL)
    root_logger.addHandler(console_handler)
    
    # Add file handler
    try:
        # Create log directory if it doesn't exist
        if not os.path.exists(DEFAULT_LOG_DIR):
            os.makedirs(DEFAULT_LOG_DIR)
            
        log_path = os.path.join(DEFAULT_LOG_DIR, DEFAULT_LOG_FILENAME)
        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=MAX_LOG_SIZE,
            backupCount=BACKUP_COUNT
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)  # File gets more detailed logs
        root_logger.addHandler(file_handler)
    except Exception as e:
        # Just log to console if file handler setup fails
        print(f"Warning: Could not set up file logging: {e}")


def log_exception(e: Exception, message: str = "An exception occurred"):
    """
    Log an exception with traceback.
    
    Args:
        e: The exception to log
        message: Optional additional message
    """
    logger = get_logger()
    logger.exception(f"{message}: {str(e)}")

def log_state_change(module: str, operation: str, item_id: Optional[int] = None, details: str = ""):
    """
    Log a state change (e.g., item added, updated, deleted).
    
    Args:
        module: Module name (e.g., "Calendar", "Tasks", "Contacts")
        operation: Operation performed (e.g., "add", "update", "delete")
        item_id: ID of the affected item, if available
        details: Additional details about the change
    """
    id_str = f"ID {item_id}" if item_id is not None else "new item"
    logger = get_logger()
    logger.info(f"[{module}] {operation.upper()} {id_str} {details}")

def set_log_level(level: Union[int, str]):
    """
    Set the log level for the root logger.
    
    Args:
        level: Log level (e.g., logging.INFO or 'INFO')
    """
    # Convert string level to integer if needed
    if isinstance(level, str):
        level = getattr(logging, level.upper())
    
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Also update console handler to match (file handler remains detailed)
    for handler in root_logger.handlers:
        if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
            handler.setLevel(level)
    
    logging.info(f"Log level set to {logging.getLevelName(level)}") # type: ignore

def get_logs_stats() -> Dict[str, Any]:
    """
    Get statistics about the logs.
    
    Returns:
        Dictionary with log statistics
    """
    stats: MutableMapping[str, Any] = {
        "log_level": logging.getLevelName(logging.getLogger().level),
        "handlers": []
    }
    
    for handler in logging.getLogger().handlers:
        handler_info: MutableMapping[str, Any] = {
            "type": handler.__class__.__name__,
            "level": logging.getLevelName(handler.level)
        }
        
        if isinstance(handler, logging.FileHandler):
            handler_info["file"] = handler.baseFilename
            
            try:
                if os.path.exists(handler.baseFilename):
                    handler_info["size"] = os.path.getsize(handler.baseFilename)
                    handler_info["last_modified"] = datetime.fromtimestamp(
                        os.path.getmtime(handler.baseFilename)
                    ).strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                # Just ignore errors in getting file stats
                pass
                
        stats["handlers"].append(handler_info)
    
    return stats
