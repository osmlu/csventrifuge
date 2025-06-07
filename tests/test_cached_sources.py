import os
import csv
from .conftest import DATA_DIR

"""Offline tests for network-based sources.

The expected output is stored under ``tests/data`` so the modules can be
tested without network access. If rules, filters or enhancements change and
these tests fail, run the source modules once (without monkeypatching) and
replace the ``*_output.json`` files with the new results.
"""


def test_addresses_cached(run_source):
    with open(os.path.join(DATA_DIR, "addresses.csv"), "r", encoding="utf-8-sig") as f:
        text = f.read()
    produced = run_source("luxembourg_addresses", text)
    produced = sorted(produced, key=lambda r: r["id_geoportail"])
    with open(os.path.join(DATA_DIR, "luxembourg-addresses.csv"), "r", encoding="utf-8") as f:
        expected_rows = list(csv.DictReader(f))
        expected_rows = sorted(expected_rows, key=lambda r: r["id_geoportail"])
    assert produced[:100] == expected_rows[:100]


def test_dicacolo_cached(run_source):
    with open(os.path.join(DATA_DIR, "caclr.zip"), "rb") as f:
        zipped = f.read()
    produced = run_source("luxembourg-caclr-dicacolo", zipped)
    produced = sorted(produced, key=lambda r: (
        r["district"], r["canton"], r["commune"], r["localite"], r["rue"], r["code_postal"]
    ))
    with open(os.path.join(DATA_DIR, "luxembourg-streets.csv"), "r", encoding="utf-8") as f:
        expected_rows = list(csv.DictReader(f))
        expected_rows = sorted(expected_rows, key=lambda r: (
            r["district"], r["canton"], r["commune"], r["localite"], r["rue"], r["code_postal"]
        ))
    assert produced[:100] == expected_rows[:100]
