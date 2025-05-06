#!/usr/bin/env python3
"""
Demo script to show how to use the logging system.
This script demonstrates various logging capabilities.
"""

import os
import sys
import time
import json
import logging
import random
from datetime import datetime

# Add the current directory to path so we can import our modules
sys.path.insert(0, f"{os.path.dirname(os.path.abspath(__file__))}/src")

# Import our logging modules
from logger import get_logger, log_exception, log_state_change, set_log_level, get_logs_stats

def simulate_operation(operation_name):
    """Simulate an operation that might fail"""
    logger = get_logger(__name__)
    logger.info(f"Starting operation: {operation_name}")
    
    try:
        # Simulate some processing time
        time.sleep(random.uniform(0.1, 0.5))
        
        # Randomly fail some operations
        if random.random() < 0.3:
            raise ValueError(f"Simulated failure in {operation_name}")
            
        logger.info(f"Operation {operation_name} completed successfully")
        return True
    except Exception as e:
        log_exception(e, f"Operation {operation_name} failed")
        return False

def main():
    # Get the main application logger
    logger = get_logger()
    
    # Show banner
    logger.info("=" * 60)
    logger.info("LOGGING DEMONSTRATION STARTED")
    logger.info("=" * 60)
    
    # Show current log configuration
    stats = get_logs_stats()
    logger.info(f"Current logging configuration: {json.dumps(stats, indent=2)}")
    
    # Demo different log levels
    logger.debug("This is a DEBUG message - detailed information for troubleshooting")
    logger.info("This is an INFO message - general information about program flow")
    logger.warning("This is a WARNING message - potential issues that aren't errors")
    logger.error("This is an ERROR message - issues that prevent functionality")
    logger.critical("This is a CRITICAL message - severe errors that may crash the app")
    
    # Change log level temporarily
    current_log_level = logging.getLogger().level
    logger.info(f"Changing log level to DEBUG")
    set_log_level(logging.DEBUG)
    logger.debug("You should now be able to see DEBUG messages in the console")
    
    # Demo state change logging
    modules = ["Calendar", "Tasks", "Contacts"]
    operations = ["add", "update", "delete"]
    
    for i in range(5):
        module = random.choice(modules)
        operation = random.choice(operations)
        item_id = random.randint(1, 100)
        details = f"by user 'demo_user' at {datetime.now().strftime('%H:%M:%S')}"
        
        log_state_change(module, operation, item_id, details)
    
    # Demo error handling
    operations = [
        "fetch_calendar_data", 
        "update_contact", 
        "delete_task", 
        "sync_with_server",
        "send_notification"
    ]
    
    for op in operations:
        simulate_operation(op)
    
    # Restore original log level
    logger.info(f"Restoring original log level")
    set_log_level(current_log_level)
    
    logger.info("=" * 60)
    logger.info("LOGGING DEMONSTRATION COMPLETED")
    logger.info("=" * 60)
    
    # Final message that tells where to find logs
    print("\nDemonstration completed!")
    print("Check the logs directory to see the generated log files.")
    print("You can view the log with: cat logs/calmsgcts.log")

if __name__ == "__main__":
    main()
