import os
import csv
import runpy
import sys
import tempfile

import httpx
import pytest

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


@pytest.fixture()
def run_source(monkeypatch):
    def _run(module: str, response):
        if isinstance(response, bytes):
            class Resp:
                def __init__(self, content):
                    self.content = content
            monkeypatch.setattr(httpx, "get", lambda url: Resp(response))
        else:
            class Resp:
                def __init__(self, text):
                    self.text = text
                    self.encoding = "utf-8-sig"
            monkeypatch.setattr(httpx, "get", lambda url: Resp(response))
        tmp = tempfile.NamedTemporaryFile(delete=False)
        tmp.close()
        argv = ["csventrifuge.py", module, tmp.name]
        with monkeypatch.context() as m:
            m.setattr(sys, "argv", argv)
            runpy.run_module("csventrifuge", run_name="__main__")
        with open(tmp.name, "r", encoding="utf-8") as outf:
            produced = list(csv.DictReader(outf))
        os.unlink(tmp.name)
        return produced
    return _run
