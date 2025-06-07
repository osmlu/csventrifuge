import os
import csv
import requests
import runpy
import sys
import tempfile

"""Offline tests for network-based sources.

The expected output is stored under ``tests/data`` so the modules can be
tested without network access. If rules, filters or enhancements change and
these tests fail, run the source modules once (without monkeypatching) and
replace the ``*_output.json`` files with the new results.
"""

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


def test_addresses_cached(monkeypatch):
    with open(os.path.join(DATA_DIR, "addresses.csv"), "r", encoding="utf-8-sig") as f:
        text = f.read()

    class Resp:
        def __init__(self, text):
            self.text = text
            self.encoding = "utf-8-sig"

    monkeypatch.setattr(requests, "get", lambda url: Resp(text))
    tmp = tempfile.NamedTemporaryFile(delete=False)
    tmp.close()
    argv = ["csventrifuge.py", "luxembourg_addresses", tmp.name]
    with monkeypatch.context() as m:
        m.setattr(sys, "argv", argv)
        runpy.run_module("csventrifuge", run_name="__main__")
    with open(tmp.name, "r", encoding="utf-8") as outf:
        produced = list(csv.DictReader(outf))
        produced = sorted(produced, key=lambda r: r["id_geoportail"])
    os.unlink(tmp.name)
    with open(os.path.join(DATA_DIR, "luxembourg-addresses.csv"), "r", encoding="utf-8") as f:
        expected_rows = list(csv.DictReader(f))
        expected_rows = sorted(expected_rows, key=lambda r: r["id_geoportail"])
    assert produced[:100] == expected_rows[:100]


def test_dicacolo_cached(monkeypatch):
    with open(os.path.join(DATA_DIR, "caclr.zip"), "rb") as f:
        zipped = f.read()

    class Resp:
        def __init__(self, content):
            self.content = content

    monkeypatch.setattr(requests, "get", lambda url: Resp(zipped))
    tmp = tempfile.NamedTemporaryFile(delete=False)
    tmp.close()
    argv = ["csventrifuge.py", "luxembourg-caclr-dicacolo", tmp.name]
    with monkeypatch.context() as m:
        m.setattr(sys, "argv", argv)
        runpy.run_module("csventrifuge", run_name="__main__")
    with open(tmp.name, "r", encoding="utf-8") as outf:
        produced = list(csv.DictReader(outf))
        produced = sorted(produced, key=lambda r: (
            r["district"], r["canton"], r["commune"], r["localite"], r["rue"], r["code_postal"]
        ))
    os.unlink(tmp.name)
    with open(os.path.join(DATA_DIR, "luxembourg-streets.csv"), "r", encoding="utf-8") as f:
        expected_rows = list(csv.DictReader(f))
        expected_rows = sorted(expected_rows, key=lambda r: (
            r["district"], r["canton"], r["commune"], r["localite"], r["rue"], r["code_postal"]
        ))
    assert produced[:100] == expected_rows[:100]
