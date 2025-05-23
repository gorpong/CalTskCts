import os
import json
import tempfile
import unittest
from io import StringIO
from typing import Any, Dict
from unittest.mock import mock_open, patch

from caltskcts.state_manager import StateManagerBase

# Minimal concrete subclass just so we can instantiate the abstract base
class DummyFileManager(StateManagerBase[Any]):
    Model = None  # not used in file‐mode

    def _validate_item(self, item: Any) -> bool:
        # we won't hit validation in these file‐backend tests
        return True

class TestStateFileBackend(unittest.TestCase):
    def setUp(self):
        # create a dummy file path (won't actually exist at first)
        tf = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        tf.close()
        self.path = tf.name
        # ensure it's gone so _load_state_file sees FileNotFoundError
        try:
            os.remove(self.path)
        except OSError:
            pass
        self.mgr = DummyFileManager(self.path)

    def tearDown(self):
        try:
            os.remove(self.path)
        except OSError:
            pass

    def test_load_state_file_not_found(self):
        """If the JSON file does not exist, _load_state_file should return {}."""
        data = self.mgr._load_state_file()
        self.assertEqual(data, {})

    def test_load_state_invalid_json(self):
        """If the JSON is malformed, _load_state_file should catch and return {}."""
        bad_json = "{ unbalanced: [ }"
        # write bad JSON to the file
        with open(self.path, "w") as f:
            f.write(bad_json)

        # it should not raise, but log and return empty dict
        data = self.mgr._load_state_file()
        self.assertEqual(data, {})

    def test_save_state_file_success(self):
        """Saving a non‐empty state should write valid JSON to disk."""
        payload: Dict[str, Dict[str, Any]] = {
            10: {"foo": "bar"},
            20: {"num": 123},
        }
        # prime the in-memory state
        self.mgr._state = payload

        # perform save
        self.mgr._save_state_file()

        # read it back and compare
        with open(self.path, "r") as f:
            loaded = json.load(f)
        # JSON keys must be strings
        self.assertEqual(set(loaded.keys()), {"10", "20"})
        self.assertEqual(loaded["10"], {"foo": "bar"})
        self.assertEqual(loaded["20"], {"num": 123})

    def test_save_state_file_failure(self):
        """If writing to disk fails, _save_state_file should propagate the exception."""
        # prime some state
        self.mgr._state = {1: {"a": 1}}

        # patch open to throw on write
        m = mock_open()
        m.return_value.write.side_effect = IOError("disk full")
        with patch("builtins.open", m):
            with self.assertRaises(IOError):
                self.mgr._save_state_file()

if __name__ == "__main__":
    unittest.main()
