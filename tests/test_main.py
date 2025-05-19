import unittest
from unittest.mock import patch
from caltskcts.__main__ import dispatch_command, get_command_map
import io

class TestDispatchCommand(unittest.TestCase):
    def setUp(self):
        class Dummy:
            def greet(self, name="World"):
                return f"Hello, {name}"
        self.context = {"test": Dummy(), "result": [None]}

    def test_valid_command_dispatch(self):
        result = dispatch_command("test.greet(name='Alice')", self.context)
        self.assertEqual(result, "Hello, Alice")

    def test_invalid_prefix(self):
        with self.assertRaises(ValueError):
            dispatch_command("badobj.greet()", self.context)

    def test_missing_method(self):
        with self.assertRaises(ValueError):
            dispatch_command("test.unknown_method()", self.context)

    def test_invalid_command_format(self):
        with self.assertRaises(ValueError):
            dispatch_command("not_even_a_command", self.context)

class TestCommandMap(unittest.TestCase):
    def test_command_map_has_all_keys(self):
        command_map = get_command_map()
        self.assertIn("cal", command_map)
        self.assertIn("tsk", command_map)
        self.assertIn("ctc", command_map)
        self.assertTrue(all(isinstance(v, list) for v in command_map.values()))

class TestArgParseBehavior(unittest.TestCase):
    @patch("sys.argv", ["program", "--files", "--database"])
    def test_mutually_exclusive_args_fail(self):
        from caltskcts.__main__ import main
        with self.assertRaises(SystemExit), patch("sys.stderr", new=io.StringIO()) as fake_err:
            main()
        self.assertIn("not allowed with argument", fake_err.getvalue())
    
    @patch("sys.argv", ["program", "--files"])
    def test_default_backend_files(self):
        from caltskcts.__main__ import main
        with patch("caltskcts.__main__.Calendar") as cal, \
             patch("caltskcts.__main__.Tasks") as tsk, \
             patch("caltskcts.__main__.Contacts") as ctc, \
             patch("builtins.input", side_effect=["exit"]), \
             patch("builtins.print"), \
             patch("caltskcts.__main__.logger"):
            main()
            cal.assert_called_once()
            tsk.assert_called_once()
            ctc.assert_called_once()
            cal.assert_called_with("_calendar.json")
            tsk.assert_called_with("_tasks.json")
            ctc.assert_called_with("_contacts.json")

    @patch("sys.argv", ["program", "--database", "custom.db"])
    def test_backend_database_uri(self):
        from caltskcts.__main__ import main
        with patch("caltskcts.__main__.Calendar") as cal, \
             patch("caltskcts.__main__.Tasks") as tsk, \
             patch("caltskcts.__main__.Contacts") as ctc, \
             patch("builtins.input", side_effect=["exit"]), \
             patch("builtins.print"), \
             patch("caltskcts.__main__.logger"):
            main()
            cal.assert_called_with("sqlite:///custom.db")
