"""
Logger configuration module for CalMsgsCts application.
Provides a way to configure logging from a JSON configuration file.
"""

import os
import json
import logging.config

def setup_logging(
    config_path: str = "logging_config.json",
    default_level: int = logging.INFO,
    env_key: str = "CALMSGCTS_LOG_CONFIG"
) -> None:
    """
    Setup logging configuration from a JSON file.
    
    Args:
        config_path: Path to the configuration file
        default_level: Default logging level if config file is not found
        env_key: Environment variable that can specify the config file path
    """
    path = os.getenv(env_key, config_path)
    
    if os.path.exists(path):
        with open(path, 'r') as f:
            config = json.load(f)
        
        # Make sure log directory exists
        log_dir = os.path.dirname(config.get('handlers', {}).get('file', {}).get('filename', 'logs/calmsgcts.log'))
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # Apply configuration
        logging.config.dictConfig(config)
        logging.info(f"Logging configured from file: {path}")
    else:
        # Basic configuration as a fallback
        logging.basicConfig(
            level=default_level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        logging.warning(f"Logging config file {path} not found. Using default configuration.")
