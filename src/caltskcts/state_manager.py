import json
import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type, TypeVar, Generic
from datetime import date, datetime
from filelock import FileLock, Timeout

from sqlalchemy import create_engine, Date, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker, DeclarativeMeta

from caltskcts.logger import get_logger, log_exception

# Base class for ORM models
Base = declarative_base()

# Type variable for ORM model classes
ModelType = TypeVar("ModelType", bound=DeclarativeMeta)

class StateManagerBase(ABC, Generic[ModelType]):
    """
    Base class for managing state via JSON files or SQLAlchemy ORM.
    Subclasses must define a `Model` attribute (an ORM class inheriting from Base)
    and implement `_validate_item` to enforce field constraints.
    """
    _state: Dict[int, Any] # unified in-memory cache of DB or JSON rows
    Model: Type[ModelType]

    def __init__(self, state_uri: str):
        """
        If state_uri contains '://', we treat it as a database URL.
        Otherwise we treat it as a path to a JSON file.
        """
        self.logger = get_logger(self.__class__.__name__)
        self.state_uri = state_uri

        if "://" in state_uri:
            # --- DB backend (ORM) ---
            self._use_db = True
            self.engine = create_engine(state_uri, future=True)
            self.SessionLocal = sessionmaker(bind=self.engine, future=True)
            # create tables
            Base.metadata.create_all(self.engine)
            # load existing data
            self._state = self._load_state_db()
        else:
            # --- JSON‐file backend ---
            self._use_db = False
            self.logger.info(f"Initializing {self.__class__.__name__} with state file: {state_uri}")
            self.state_file = state_uri
            self._state = self._load_state_file()

    def _load_state(self) -> Dict[int, Any]:
        """ Alias for the old file-based loader, or DB loader if using SQL. """
        return self._load_state_db() if self._use_db else self._load_state_file()

    def _save_state(self) -> None:
        """ Alias for the old file-base saver; no-op for DB (per-record save). """
        if self._use_db:
            return
        return self._save_state_file()

    # =========================
    # DB-related save/load
    # =========================
    
    def _load_state_db(self) -> Dict[int, Any]:
        """Load all rows from the database into the in‐memory dict."""
        state: Dict[int, Any] = {}
        try:
            with self.SessionLocal() as session:
                for obj in session.query(self.Model).all():
                    state[obj.id] = obj # type: ignore[attr-defined]
            self.logger.info(f"Loaded {len(state)} items from table '{self.Model.__tablename__}' table") # type: ignore
        except Exception as e:
            log_exception(e, "Failed to load state from DB")
            state = {}
        return state

    # =========================
    # File-related save/load
    # =========================
    
    def _json_default(self, obj: Any) -> Any:
        """
        JSON serializer fallback: converts date/datetime
        into the required MM/DD/YYYY[ HH:MM] strings.
        """
        if isinstance(obj, datetime):
            return obj.strftime("%m/%d/%Y %H:%M")
        if isinstance(obj, date):
            return obj.strftime("%m/%d/%Y")
        raise TypeError(f"Type {type(obj)} not serializable")

    def _load_state_file(self) -> Dict[int, Any]:
        """
        Concurrency-safe load: acquire a filesystem lock, read the JSON (or
        fall back to empty), convert keys to ints, and return the dict.
        """
        state: Dict[int, Any] = {}
        lock = FileLock(self.state_file + ".lock", timeout=2)
        try:
            with lock:
                try:
                    with open(self.state_file, "r") as f:
                        data = json.load(f)
                except FileNotFoundError:
                    self.logger.warning(f"State file not found: {self.state_file}. Using empty state.")
                    data = {}
                except json.JSONDecodeError as e:
                    log_exception(e, f"Error parsing JSON file: {self.state_file}")
                    data: Dict[str, Any] = {}
                # convert string keys back to ints
                state = {int(k): v for k, v in data.items()}
                self.logger.info(f"Loaded {len(state)} items from JSON file '{self.state_file}'")
        except Timeout:
            self.logger.error(f"Could not acquire lock for reading {self.state_file}")
        return state

    def _save_state_file(self) -> None:
        """
        Concurrency-safe save: acquire a filesystem lock, read any existing JSON,
        merge in self._state, and write the combined dict back out.
        """
        lock = FileLock(self.state_file + ".lock", timeout=2)
        try:
            with lock:
                # read existing file so we don't clobber others' writes
                try:
                    with open(self.state_file, "r") as f:
                        existing = json.load(f)
                except (FileNotFoundError, json.JSONDecodeError):
                    existing = {}
                    
                # Snapshot in-memory state right now
                snapshot = {str(k): v for k, v in self._state.items()}
                
                # merge snapshot into existing from disk
                existing.update(snapshot) # type: ignore

                # write out full merged state
                with open(self.state_file, "w") as f:
                    json.dump(existing, f, indent=4, default=self._json_default)
                
                # reflect that merged state back into current
                self._state = {int(k): v for k, v in existing.items()}  # type: ignore
                
        except Timeout:
            self.logger.error(f"Could not acquire lock for writing {self.state_file}")
            raise
        except Exception as e:
            log_exception(e, f"Failed to save state to {self.state_file}")
            raise
        
    def _save_one_file(self, item_id: int, item_data: Any) -> None:
        """Insert or update a single record in the JSON file, under lock."""
        lock = FileLock(self.state_file + ".lock", timeout=2)
        try:
            with lock:
                try:
                    with open(self.state_file, "r") as f:
                        data = json.load(f)
                except (FileNotFoundError, json.JSONDecodeError):
                    data = {}

                data[str(item_id)] = item_data
                with open(self.state_file, "w") as f:
                    json.dump(data, f, indent=4, default=self._json_default)

                # reflect back into memory
                self._state = {int(k): v for k, v in data.items()} # type: ignore

        except Timeout:
            self.logger.error(f"Could not acquire lock for writing {self.state_file}")
            raise
        except Exception as e:
            log_exception(e, f"Failed to save one record to {self.state_file}")
            raise
    
    def _delete_one_file(self, item_id: int) -> None:
        """Delete a single record from the JSON file, under lock."""
        lock = FileLock(self.state_file + ".lock", timeout=2)
        try:
            with lock:
                try:
                    with open(self.state_file, "r") as f:
                        data = json.load(f)
                except (FileNotFoundError, json.JSONDecodeError):
                    data = {}

                data.pop(str(item_id), None) # type: ignore
                with open(self.state_file, "w") as f:
                    json.dump(data, f, indent=4, default=self._json_default)

                # reflect back into memory
                self._state = {int(k): v for k, v in data.items()} # type: ignore

        except Timeout:
            self.logger.error(f"Could not acquire lock for writing {self.state_file}")
            raise
        except Exception as e:
            log_exception(e, f"Failed to delete one record from {self.state_file}")
            raise
        
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

    def get_item(self, item_id: int) -> Optional[Dict[str, Any]]:
        """
        Get an item by its ID.
        
        Args:
            item_id: The ID of the item to retrieve
            
        Returns:
            The item data or None if not found
        """
        obj = self._state.get(item_id)
        if obj is None:
            self.logger.debug(f"Item with ID {item_id} not found")
            return None
        self.logger.debug(f"Retrieved item with ID {item_id}")
        if self._use_db:
            flat: Dict[str, Any] = {}
            for col in obj.__table__.columns:   # type: ignore[attr-defined]
                v = getattr(obj, col.name)      # type: ignore[attr-defined]
                if isinstance(v, datetime):
                    flat[col.name] = v.strftime("%m/%d/%Y %H:%M")
                    print(f"Item {item_id} {col.name} is a datetime, {flat[col.name]}")
                elif isinstance(v, date):
                    flat[col.name] = v.strftime("%m/%d/%Y")
                    print(f"Item {item_id} {col.name} is a date, {flat[col.name]}")
                else:
                    flat[col.name] = v
            return flat
        # JSON-file mode: obj is already a dict
        return obj

    def list_items(self) -> Dict[int, Any]:
        """
        List all items with integer keys.
        
        Returns:
            Dictionary of items with integer keys
        """
        self.logger.debug(f"Listing {len(self._state)} items")
        if getattr(self, "_use_db", False):
            # DB mode: convert each ORM instance into a plain dict
            result: Dict[int, Any] = {}
            for item_id, obj in self._state.items():
                flat = {}
                for col in obj.__table__.columns:   # type: ignore[attr-defined]
                    v = getattr(obj, col.name)      # type: ignore[attr-defined]
                    if isinstance(v, datetime):
                        flat[col.name] = v.strftime("%m/%d/%Y %H:%M")
                    elif isinstance(v, date):
                        flat[col.name] = v.strftime("%m/%d/%Y")
                    else:
                        flat[col.name] = v
                result[item_id] = flat
            return result
        
        # File-based mode, just return the in-memory dict
        return dict(self._state)

    def add_item(self, item_id: int, item_data: Dict[str, Any]) -> bool:
        """
        Add an item to state with the specified ID.
        
        Args:
            item_id: The ID for the new item
            item_data: Dictionary containing the item data
            
        Returns:
            True if added successfully, False if ID already exists
        """
        if item_id in self._state:
            self.logger.warning(f"Failed to add item: ID {item_id} already exists")
            return False

        self._validate_item(item_data)
        if self._use_db:
            kwargs = dict(item_data)
            for col in self.Model.__table__.columns:     # type: ignore[attr-defined]
                name = col.name # type: ignore
                if name in kwargs and isinstance(kwargs[name], str):
                    val = kwargs[name]
                    if isinstance(col.type, Date): # type: ignore[attr-defined]
                        kwargs[name] = datetime.strptime(val, "%m/%d/%Y").date()
                    elif isinstance(col.type, DateTime): # type: ignore[attr-defined]
                        kwargs[name] = datetime.strptime(val, "%m/%d/%Y %H:%M")

            try:
                inst = self.Model(id=item_id, **kwargs) # type: ignore
                with self.SessionLocal() as session:
                    session.add(inst)
                    session.commit()
                    session.refresh(inst)
                self._state[item_id] = inst
            except Exception as e:
                log_exception(e, f"Failed to add item {item_id} to DB")
                return False
        else:
            self._state[item_id] = item_data
            self._save_one_file(item_id, item_data)
        self.logger.info(f"Added item with ID {item_id}")
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
        if item_id not in self._state:
            return False
        if self._use_db:
            try:
                with self.SessionLocal() as session:
                    inst = session.get(self.Model, item_id)
                    if inst is None:
                        return False
                    # apply updates
                    for k, v in updates.items():
                        if isinstance(v, str):
                            col = self.Model.__table__.columns[k] # type: ignore[attr-defined]
                            if isinstance(col.type, Date): # type: ignore[attr-defined]
                                v = datetime.strptime(v, "%m/%d/%Y").date()
                            elif isinstance(col.type, DateTime):  # type: ignore[attr-defined]
                                v = datetime.strptime(v, "%m/%d/%Y %H:%M")
                        setattr(inst, k, v)

                    # build a flat dict for validation, formatting dates/times
                    current_map: Dict[str, Any] = {}
                    for col in inst.__table__.columns:  # type: ignore[attr-defined]
                        val = getattr(inst, col.name)     # type: ignore[attr-defined]
                        if isinstance(val, datetime):
                            # keep HH:MM for Calendar ORM
                            current_map[col.name] = val.strftime("%m/%d/%Y %H:%M") # type: ignore[attr-defined]
                        elif isinstance(val, date):
                            # tasks only care about MM/DD/YYYY
                            current_map[col.name] = val.strftime("%m/%d/%Y") # type: ignore[attr-defined]
                        else:
                            current_map[col.name] = val # type: ignore[attr-defined]

                    # now validate with exactly the same format as JSON mode
                    self._validate_item(current_map)
                    session.commit()
                    session.refresh(inst)
                self._state[item_id] = inst
                return True
            except Exception as e:
                log_exception(e, f"Failed to update item {item_id} in DB")
                return False
        else:
            new_data = {**self._state[item_id], **updates} # type: ignore
            self._validate_item(new_data)
            self._state[item_id].update(updates)
            self._save_one_file(item_id, self._state[item_id])
            return True

    def delete_item(self, item_id: int) -> bool:
        """
        Delete an item by its ID.
        
        Args:
            item_id: The ID of the item to delete
            
        Returns:
            True if deleted successfully, False if item doesn't exist
        """
        if item_id not in self._state:
            return False
        if self._use_db:
            try:
                with self.SessionLocal() as session:
                    inst = session.get(self.Model, item_id)
                    if inst is None:
                        return False
                    session.delete(inst)
                    session.commit()
                del self._state[item_id]
                return True
            except Exception as e:
                log_exception(e, f"Failed to delete item {item_id} from DB")
                return False
        else:
            del self._state[item_id]
            self._delete_one_file(item_id)
            return True

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
        
        results: List[Dict[str, Any]] = []
        for item_id, item in self._state.items():
            if self._use_db:
                row = {col.name: getattr(item, col.name) for col in item.__table__.columns}
                row["item_id"] = item_id
            else:
                row: Dict[str, Any] = {"item_id": item_id, **item}
            for f in fields:
                if f in row and row[f] and query_regex.search(str(row[f])):
                    results.append(row)
                    break
                
        self.logger.debug(f"Search found {len(results)} results")
        return results

    @property
    def items(self) -> Dict[int, Any]:
        """
        Access state data directly with int keys.
        
        Returns:
            Dictionary of all items with int keys.
        """
        return self.list_items()

    # --- Force subclasses to continue providing per‐type validation ---
    @abstractmethod
    def _validate_item(self, item: Any) -> bool:
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
