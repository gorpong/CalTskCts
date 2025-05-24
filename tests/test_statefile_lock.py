import threading
import time
import unittest
import os

from caltskcts.state_manager import StateManagerBase

class Dummy(StateManagerBase[dict]):
    def _validate_item(self, item): return True

class TestLocking(unittest.TestCase):
    def setUp(self):
        self.path = "tmp_state.json"
        try: os.remove(self.path)
        except: pass
        self.mgr = Dummy(self.path)

    def tearDown(self):
        for p in (self.path, self.path + ".lock"):
            try: os.remove(p)
            except: pass

    def test_concurrent_writes(self):
        def writer(i):
            mgr = Dummy(self.path)
            mgr._state = {i: i}
            time.sleep(1)   # Force interleaving
            mgr._save_state_file()

        t1 = threading.Thread(target=writer, args=(1,))
        t2 = threading.Thread(target=writer, args=(2,))

        t1.start()
        time.sleep(0.1)   # stagger slightly
        t2.start()
        t1.join()
        t2.join()

        # If no exception was raised, both writes serialized correctly
        mgr2 = Dummy(self.path)
        data = mgr2._load_state_file()
        self.assertIn(1, data)
        self.assertIn(2, data)
