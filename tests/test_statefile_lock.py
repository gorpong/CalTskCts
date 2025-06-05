import threading
import time
import unittest
import os
import tempfile
from filelock import FileLock, Timeout

from caltskcts.state_manager import StateManagerBase

class Dummy(StateManagerBase[dict]):
    def _validate_item(self, item): return True

class TestLocking(unittest.TestCase):
    def setUp(self):
        tf = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
        self.path = tf.name
        tf.close()
        try:
            os.remove(self.path)
        except OSError:
            pass
        self.mgr = Dummy(self.path)

    def tearDown(self):
        for p in (self.path, self.path + ".lock"):
            try:
                os.remove(p)
            except OSError:
                pass

    def test_concurrent_writes(self):
        """Two writers racing should both end up in the merged JSON."""
        start_evt = threading.Event()

        def writer(i):
            m = Dummy(self.path)
            m._state = {i: i}
            start_evt.wait()
            m._save_state_file()

        t1 = threading.Thread(target=writer, args=(1,))
        t2 = threading.Thread(target=writer, args=(2,))

        t1.start()
        t2.start()

        # let both threads proceed together
        start_evt.set()
        t1.join()
        t2.join()

        # load final state
        mgr_final = Dummy(self.path)
        data = mgr_final._load_state_file()
        self.assertEqual(set(data.keys()), {1, 2})

        # If a lock file was left behind, delete it (but don't fail)
        try:
            os.remove(self.path + ".lock")
        except OSError:
            pass

    def test_lock_timeout_raises(self):
        """If another process holds the lock indefinitely, a second writer times out."""
        # Manually acquire and hold the lock
        lock = FileLock(self.path + ".lock", timeout=0.1)
        lock.acquire()
        try:
            with self.assertRaises(Timeout):
                # This call tries to acquire the same lock and should time out
                Dummy(self.path)._save_state_file()
        finally:
            lock.release()

    def test_concurrent_add_and_delete(self):
        """Adding in one thread and deleting in another should merge properly."""
        # Pre-seed item 0
        mgr0 = Dummy(self.path)
        mgr0._state = {0: 0}
        mgr0._save_state_file()

        def adder():
            m = Dummy(self.path)
            m._state = {1: 1}
            # no sleep: race immediately
            m._save_state_file()

        def deleter():
            m = Dummy(self.path)
            # ensure adder probably ran first
            time.sleep(0.1)
            m.delete_item(0)

        t1 = threading.Thread(target=adder)
        t2 = threading.Thread(target=deleter)

        t1.start()
        t2.start()
        t1.join()
        t2.join()

        # Check final contents
        mgr_final = Dummy(self.path)
        data = mgr_final._load_state_file()
        self.assertNotIn(0, data)
        self.assertIn(1, data)

if __name__ == "__main__":
    unittest.main()
