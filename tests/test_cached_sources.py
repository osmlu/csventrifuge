import os
import json
import importlib.util
import requests
from io import BytesIO
from zipfile import ZipFile

"""Offline tests for network-based sources.

The expected output is stored under ``tests/data`` so the modules can be
tested without network access. If rules, filters or enhancements change and
these tests fail, run the source modules once (without monkeypatching) and
replace the ``*_output.json`` files with the new results.
"""

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


def load_source(path):
    spec = importlib.util.spec_from_file_location("src", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_addresses_cached(monkeypatch):
    module = load_source(os.path.join(os.path.dirname(__file__), os.pardir, "sources", "luxembourg_addresses.py"))
    with open(os.path.join(DATA_DIR, "addresses_sample.csv"), "r", encoding="utf-8-sig") as f:
        text = f.read()

    class Resp:
        def __init__(self, text):
            self.text = text
            self.encoding = "utf-8-sig"

    monkeypatch.setattr(requests, "get", lambda url: Resp(text))
    rows, fields = module.get()
    with open(os.path.join(DATA_DIR, "addresses_sample_output.json"), "r", encoding="utf-8") as f:
        expected = json.load(f)
    assert rows == expected["rows"]
    assert fields == expected["fieldnames"]


def test_dicacolo_cached(monkeypatch):
    module = load_source(os.path.join(os.path.dirname(__file__), os.pardir, "sources", "luxembourg-caclr-dicacolo.py"))
    with open(os.path.join(DATA_DIR, "caclr_sample.txt"), "rb") as f:
        data = f.read()
    buf = BytesIO()
    with ZipFile(buf, "w") as zf:
        zf.writestr("TR.DICACOLO.RUCP", data)
    zipped = buf.getvalue()

    class Resp:
        def __init__(self, content):
            self.content = content

    monkeypatch.setattr(requests, "get", lambda url: Resp(zipped))
    rows, fields = module.get()
    with open(os.path.join(DATA_DIR, "caclr_sample_output.json"), "r", encoding="utf-8") as f:
        expected = json.load(f)
    assert rows == expected["rows"]
    assert fields == expected["fieldnames"]
