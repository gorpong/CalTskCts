# state_manager.py
import json
import re
from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Optional, TypeVar, MutableMapping, cast

from caltskcts.logger import get_logger, log_exception

T = TypeVar("T", bound=MutableMapping[str, Any])

# --- SQLAlchemy imports for DB backend ---
from sqlalchemy import (
    create_engine, Table, Column, Integer, MetaData, JSON as SA_JSON, select
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

class StateManagerBase(ABC, Generic[T]):
    """
    Abstract base class for managing state data either in JSON files
    or in a relational database (SQLite/Postgres) via SQLAlchemy.
    """

    def __init__(self, state_uri: str):
        """
        If state_uri contains '://', we treat it as a database URL.
        Otherwise we treat it as a path to a JSON file.
        """
        self.logger = get_logger(self.__class__.__name__)
        self.state_uri = state_uri

        if "://" in state_uri:
            # --- DB backend initialization ---
            self._use_db = True
            self.engine = create_engine(state_uri, future=True)
            self.Session = sessionmaker(bind=self.engine, future=True)
            self.metadata = MetaData()
            # we name the table after the subclass, e.g. "contacts", "calendars", ...
            self.table = Table(
                self.__class__.__name__.lower(),
                self.metadata,
                Column("id", Integer, primary_key=True),
                Column("data", SA_JSON, nullable=False),
            )
            self.metadata.create_all(self.engine)
            self._state: T = self._load_state_db()
            self.logger.info(f"Loaded {len(self._state)} items from DB table {self.table.name}")
        else:
            # --- JSON‐file backend (existing behavior) ---
            self._use_db = False
            self.logger.info(f"Initializing {self.__class__.__name__} with state file: {state_uri}")
            self.state_file = state_uri
            self._state: T = self._load_state_file()

    def _load_state(self) -> T:
        """ Alias for the old file-based loader, or DB loader if using SQL. """
        return self._load_state_db() if self._use_db else self._load_state_file()
    
    def _save_state(self) -> None:
        """ Alias for the old file-base saver; no-op for DB (per-record save). """
        if self._use_db:
            return
        return self._save_state_file()

    # ----------------------
    # JSON‐backend methods
    # ----------------------
    def _load_state_file(self) -> T:
        """
        Load state from the state file.
        
        Returns:
            Dict containing the loaded state or an empty dict if file doesn't exist
        """
        try:
            with open(self.state_file, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            self.logger.warning(f"State file not found: {self.state_file}, using empty state")
            return cast(T, {})
        except json.JSONDecodeError as e:
            self.logger.error(f"Error parsing state file {self.state_file}: {e}")
            return cast(T, {})

    def _save_state_file(self) -> None:
        """Save current state to the state file."""
        try:
            with open(self.state_file, "w") as f:
                json.dump(self._state, f, indent=4)
        except Exception as e:
            log_exception(e, f"Failed to save state to {self.state_file}")
            raise

    # ----------------------
    # DB‐backend methods
    # ----------------------
    def _load_state_db(self) -> T:
        """Load all rows from the database into the in‐memory dict."""
        state: T = cast(T, {})
        with self.Session() as session:
            for row in session.execute(select(self.table)).all():
                # row[0] is the id, row[1] is the JSON data
                state[str(row[0])] = row[1]  # type: ignore
        return state

    def _save_one_db(self, item_id: int, data: T) -> None:
        """Insert or update a single record in the DB."""
        with self.Session() as session:
            try:
                session.execute(
                    self.table.insert().values(id=item_id, data=data)
                )
            except IntegrityError:
                # already exists -> do update
                session.execute(
                    self.table.update()
                         .where(self.table.c.id == item_id)
                         .values(data=data)
                )
            session.commit()

    def _delete_one_db(self, item_id: int) -> None:
        with self.Session() as session:
            session.execute(
                self.table.delete().where(self.table.c.id == item_id)
            )
            session.commit()

    # ----------------------
    # Shared CRUD entry points
    # ----------------------
    def _get_next_id(self) -> int:
        """
        Get the next available ID for an item in the state.
        
        Returns:
            Next available integer ID
        """
        if not self._state:
            return 1
        return max(int(k) for k in self._state) + 1

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
        item_key = str(item_id)
        if item_key in self._state:
            self.logger.warning(f"Failed to add item: ID {item_id} already exists")
            return False

        try:
            # Validate the item before adding
            self._validate_item(item_data)
            
            self._state[item_key] = item_data
            if self._use_db:
                self._save_one_db(item_id, item_data)
            else:
                self._save_state_file()
            self.logger.info(f"Added item with ID {item_id}")
            return True
        except ValueError as e:
            self.logger.error(f"Validation error adding item ID {item_id}: {str(e)}")
            raise
        except Exception as e:
            log_exception(e, f"Error adding item with ID {item_id}")
            raise

    def update_item(self, item_id: int, updates: T) -> bool:
        """
        Update an existing item with partial updates.
        
        Args:
            item_id: The ID of the item to update
            updates: Dictionary containing fields to update
            
        Returns:
            True if updated successfully, False if item doesn't exist
        """
        key = str(item_id)
        if key not in self._state:
            self.logger.warning(f"Failed to update item: ID {item_id} not found")
            return False
        
        try:
            new_data: T = cast(T, {**self._state[key], **updates})
            self._validate_item(new_data)
            self._state[key].update(updates)
            if self._use_db:
                self._save_one_db(item_id, self._state[key])
            else:
                self._save_state_file()
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
        key = str(item_id)
        if key not in self._state:
            self.logger.warning(f"Failed to delete item: ID {item_id} not found")
            return False

        try:
            del self._state[key]
            if self._use_db:
                self._delete_one_db(item_id)
            else:
                self._save_state_file()
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

    def search_items(self, query: str, fields: List[str]) -> List[T]:
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
        
        results: List[T] = []
        for id_str, item in self._state.items():
            for f in fields:
                if f in item and item[f] and query_regex.search(str(item[f])):
                    results.append(cast(T, {"item_id": int(id_str), **item}))
                    break   # Found in one field, no need to check others
                
        self.logger.debug(f"Search found {len(results)} results")
        return results

    @property
    def items(self) -> T:
        """
        Access state data directly with string keys.
        
        Returns:
            Dictionary of all items with string keys
        """
        return self._state

    # --- Force subclasses to continue providing per‐type validation ---
    @abstractmethod
    def _validate_item(self, item: T) -> bool:
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
