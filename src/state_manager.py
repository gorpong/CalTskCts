from abc import ABC, abstractmethod
import json
from typing import Dict, Any, List, Optional, TypeVar, Generic
import re

# Import our logger
from logger import get_logger, log_exception

# Define a generic type for item data
T = TypeVar('T', bound=Dict[str, Any])

class StateManagerBase(ABC, Generic[T]):
    """
    Abstract base class for managing state data with common CRUD operations
    and data persistence functionality.
    """
    
    def __init__(self, state_file: str):
        """
        Initialize the state manager with a file path.
        
        Args:
            state_file: Path to the JSON file for storing state data
        """
        # Get a logger for this class
        self.logger = get_logger(self.__class__.__name__)
        self.logger.info(f"Initializing {self.__class__.__name__} with state file: {state_file}")
        
        self.state_file = state_file
        self._state: Dict[str, T] = self._load_state()
    
    def _load_state(self) -> Dict[str, T]:
        """
        Load state from the state file.
        
        Returns:
            Dict containing the loaded state or an empty dict if file doesn't exist
        """
        try:
            with open(self.state_file, "r") as f:
                state = json.load(f)
                self.logger.info(f"Loaded state from {self.state_file}: {len(state)} items")
                return state
        except FileNotFoundError:
            self.logger.warning(f"State file not found: {self.state_file}, using empty state")
            return {}
        except json.JSONDecodeError as e:
            self.logger.error(f"Error parsing state file {self.state_file}: {str(e)}")
            return {}
    
    def _save_state(self) -> None:
        """Save current state to the state file."""
        try:
            with open(self.state_file, "w") as f:
                json.dump(self._state, f, indent=4)
                self.logger.debug(f"State saved to {self.state_file}")
        except Exception as e:
            log_exception(e, f"Failed to save state to {self.state_file}")
            # Re-raise to maintain original behavior
            raise
    
    def _get_next_id(self) -> int:
        """
        Get the next available ID for an item in the state.
        
        Returns:
            Next available integer ID
        """
        if not self._state:
            self.logger.debug("No items in state, returning ID 1")
            return 1
        next_id = max(int(item_id) for item_id in self._state.keys()) + 1
        self.logger.debug(f"Generated next ID: {next_id}")
        return next_id
    
    def get_item(self, item_id: int) -> Optional[T]:
        """
        Get an item by its ID.
        
        Args:
            item_id: The ID of the item to retrieve
            
        Returns:
            The item data or None if not found
        """
        result = self._state.get(str(item_id))
        if result is None:
            self.logger.debug(f"Item with ID {item_id} not found")
        else:
            self.logger.debug(f"Retrieved item with ID {item_id}")
        return result
    
    def add_item(self, item_id: int, item_data: T) -> bool:
        """
        Add an item to state with the specified ID.
        
        Args:
            item_id: The ID for the new item
            item_data: Dictionary containing the item data
            
        Returns:
            True if added successfully, False if ID already exists
        """
        item_id_str = str(item_id)
        if item_id_str in self._state:
            self.logger.warning(f"Failed to add item: ID {item_id} already exists")
            return False
        
        try:
            # Validate the item before adding
            self._validate_item(item_data)
            
            self._state[item_id_str] = item_data
            self._save_state()
            self.logger.info(f"Added item with ID {item_id}")
            return True
        except ValueError as e:
            self.logger.error(f"Validation error adding item ID {item_id}: {str(e)}")
            raise
        except Exception as e:
            log_exception(e, f"Error adding item with ID {item_id}")
            raise
    
    def update_item(self, item_id: int, updates: Dict[str, Any]) -> bool:
        """
        Update an existing item with partial updates.
        
        Args:
            item_id: The ID of the item to update
            updates: Dictionary containing fields to update
            
        Returns:
            True if updated successfully, False if item doesn't exist
        """
        item_id_str = str(item_id)
        if item_id_str not in self._state:
            self.logger.warning(f"Failed to update item: ID {item_id} not found")
            return False
        
        try:
            # Check that updates would result in a valid item
            updated_item = self._state[item_id_str].copy()
            for key, value in updates.items():
                updated_item[key] = value
            
            self._validate_item(updated_item)
            
            # Apply the updates
            for key, value in updates.items():
                self._state[item_id_str][key] = value
            
            self._save_state()
            self.logger.info(f"Updated item with ID {item_id} - fields: {', '.join(updates.keys())}")
            return True
        except ValueError as e:
            self.logger.error(f"Validation error updating item ID {item_id}: {str(e)}")
            raise
        except Exception as e:
            log_exception(e, f"Error updating item with ID {item_id}")
            raise
    
    def delete_item(self, item_id: int) -> bool:
        """
        Delete an item by its ID.
        
        Args:
            item_id: The ID of the item to delete
            
        Returns:
            True if deleted successfully, False if item doesn't exist
        """
        item_id_str = str(item_id)
        if item_id_str not in self._state:
            self.logger.warning(f"Failed to delete item: ID {item_id} not found")
            return False
        
        try:
            del self._state[item_id_str]
            self._save_state()
            self.logger.info(f"Deleted item with ID {item_id}")
            return True
        except Exception as e:
            log_exception(e, f"Error deleting item with ID {item_id}")
            raise
    
    def list_items(self) -> Dict[int, T]:
        """
        List all items with integer keys.
        
        Returns:
            Dictionary of items with integer keys
        """
        self.logger.debug(f"Listing {len(self._state)} items")
        return {int(k): v for k, v in self._state.items()}
    
    @property
    def items(self) -> Dict[str, T]:
        """
        Access state data directly with string keys.
        
        Returns:
            Dictionary of all items with string keys
        """
        return self._state

    def search_items(self, query: str, fields: List[str]) -> List[Dict[str, Any]]:
        """
        Generic search function that searches across specified fields using regex.
        
        Args:
            query: Search query (regex pattern)
            fields: List of field names to search in
            
        Returns:
            List of matching items with their IDs included
        """
        self.logger.debug(f"Searching for '{query}' in fields: {fields}")
        try:
            query_regex = re.compile(query, re.IGNORECASE)
        except re.error as e:
            error_msg = f"Invalid regex pattern: {e}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
            
        results = []
        for item_id, item in self._state.items():
            for field in fields:
                field_value = item.get(field, "")
                if field_value and query_regex.search(str(field_value)):
                    results.append({"item_id": int(item_id), **item})
                    break  # Found in one field, no need to check others
        
        self.logger.debug(f"Search found {len(results)} results")
        return results

    @abstractmethod
    def _validate_item(self, item: Dict[str, Any]) -> bool:
        """
        Validate item data before adding/updating.
        To be implemented by subclasses for specific validation rules.
        
        Args:
            item: The item data to validate
            
        Returns:
            True if valid
        
        Raises:
            ValueError: If validation fails with specific reason
        """
        pass