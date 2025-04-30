import json
from typing import Dict, Any


class StateManager:
    """
    A class to manage the loading, saving, and ID generation for state data.
    This provides common functionality for data persistence.
    """
    
    def __init__(self, state_file: str):
        """
        Initialize the state manager with a file path.
        
        Args:
            state_file: Path to the JSON file for storing state data
        """
        self.state_file = state_file
        self.state: Dict[str, Dict[str, Any]] = self._load_state()
    
    def _load_state(self) -> Dict[str, Dict[str, Any]]:
        """
        Load state from the state file.
        
        Returns:
            Dict containing the loaded state or an empty dict if file doesn't exist
        """
        try:
            with open(self.state_file, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}  # No state file, start with empty state
    
    def save_state(self) -> None:
        """Save state to the state file."""
        with open(self.state_file, "w") as f:
            json.dump(self.state, f, indent=4)
    
    def get_next_id(self) -> int:
        """
        Get the next available ID for an item in the state.
        
        Returns:
            Next available integer ID
        """
        if not self.state:
            return 1
        return max(int(item_id) for item_id in self.state.keys()) + 1
    
    def get_item(self, item_id: int) -> Dict[str, Any]:
        """
        Get an item by its ID.
        
        Args:
            item_id: The ID of the item to retrieve
            
        Returns:
            The item data or an error message if not found
        """
        item_id = str(item_id)  # Normalize to string
        if item_id in self.state:
            return self.state[item_id]
        else:
            return None  # Return None if not found
    
    def add_item(self, item_id: int, item_data: Dict[str, Any]) -> bool:
        """
        Add an item to state with the specified ID.
        
        Args:
            item_id: The ID for the new item
            item_data: Dictionary containing the item data
            
        Returns:
            True if added successfully, False if ID already exists
        """
        item_id = str(item_id)  # Normalize to string
        
        if item_id in self.state:
            return False  # ID already exists
        
        self.state[item_id] = item_data
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
        item_id = str(item_id)  # Normalize to string
        
        if item_id not in self.state:
            return False  # Item doesn't exist
        
        # Apply updates to existing item
        for key, value in updates.items():
            if value is not None:  # Only update non-None values
                self.state[item_id][key] = value
        
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
        item_id = str(item_id)  # Normalize to string
        
        if item_id not in self.state:
            return False  # Item doesn't exist
        
        del self.state[item_id]
        self.save_state()
        return True
    
    def list_items(self) -> Dict[int, Dict[str, Any]]:
        """
        List all items with integer keys.
        
        Returns:
            Dictionary of items with integer keys
        """
        return {int(item_id): details for item_id, details in self.state.items()}
