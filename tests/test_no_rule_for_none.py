import os
import runpy
import sys
import tempfile
import logging
import unittest
from unittest import mock


class TestNoRuleForNone(unittest.TestCase):
    def test_no_log_when_value_none(self):
        tmp = tempfile.NamedTemporaryFile(delete=False)
        tmp.close()
        script_path = os.path.join(os.path.dirname(__file__), os.pardir)
        sys.path.insert(0, script_path)
        argv = ["csventrifuge.py", "test_source", tmp.name]
        with mock.patch.object(sys, "argv", argv):
            logging.basicConfig(level=logging.DEBUG)
            with self.assertLogs("__main__", level="DEBUG") as cm:
                runpy.run_module("csventrifuge", run_name="__main__")
        os.unlink(tmp.name)
        self.assertNotIn("No rule for [foo] None", "\n".join(cm.output))


if __name__ == "__main__":
    unittest.main()
