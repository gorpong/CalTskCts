from abc import ABC, abstractmethod
import json
from datetime import datetime
from typing import Dict, Any, List, Optional, TypeVar, Generic
import re

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
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def save_state(self) -> None:
        """Save current state to the state file."""
        with open(self.state_file, "w") as f:
            json.dump(self._state, f, indent=4)
    
    def get_next_id(self) -> int:
        """
        Get the next available ID for an item in the state.
        
        Returns:
            Next available integer ID
        """
        if not self._state:
            return 1
        return max(int(item_id) for item_id in self._state.keys()) + 1
    
    def get_item(self, item_id: int) -> Optional[T]:
        """
        Get an item by its ID.
        
        Args:
            item_id: The ID of the item to retrieve
            
        Returns:
            The item data or None if not found
        """
        return self._state.get(str(item_id))
    
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
            return False
        
        self._state[item_id_str] = item_data
        self.save_state()
        return True
    
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
            return False
        
        for key, value in updates.items():
            if value is not None:  # Only update non-None values
                self._state[item_id_str][key] = value
        
        self.save_state()
        return True
    
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
            return False
        
        del self._state[item_id_str]
        self.save_state()
        return True
    
    def list_items(self) -> Dict[int, T]:
        """
        List all items with integer keys.
        
        Returns:
            Dictionary of items with integer keys
        """
        return {int(k): v for k, v in self._state.items()}
    
    @property
    def items(self) -> Dict[str, T]:
        """Access state data directly."""
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
        try:
            query_regex = re.compile(query, re.IGNORECASE)
        except re.error as e:
            raise ValueError(f"Invalid regex pattern: {e}")
            
        results = []
        for item_id, item in self._state.items():
            for field in fields:
                field_value = item.get(field, "")
                if field_value and query_regex.search(str(field_value)):
                    results.append({"item_id": int(item_id), **item})
                    break  # Found in one field, no need to check others
        return results

    @abstractmethod
    def validate_item(self, item: Dict[str, Any]) -> bool:
        """
        Validate item data before adding/updating.
        To be implemented by subclasses for specific validation rules.
        
        Args:
            item: The item data to validate
            
        Returns:
            True if valid, False otherwise
        
        Raises:
            ValueError: If validation fails with specific reason
        """
        pass
