# Call with get(), you get a collection containing dicts, and the field names list. That's the deal.

import csv
import logging

import requests

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


def get():
    # The endpoint that redirects to the most recent version of the
    # addresses in csv.
    ADDRESSES_CSV = (
        "https://data.public.lu/fr/datasets/r/5cadc5b8-6a7d-4283-87bc-f9e58dd771f7"
    )
    # Downloading the addresses might take ~15 seconds.
    # In the meanwhile, shake your wrists and correct your posture.
    r = requests.get(ADDRESSES_CSV)
    r.encoding = "utf-8-sig"
    req_addresses = r.text.splitlines()
    csvreader = csv.DictReader(req_addresses, delimiter=";")
    fieldnames = csvreader.fieldnames
    addresses = [{k: v for k, v in row.items()} for row in csvreader]
    for row in addresses:
        row["code_commune"] = row["id_geoportail"][:3]
        row["rue_orig"] = row["rue"]
    fieldnames.insert(0, "code_commune")
    fieldnames.insert(0, "rue_orig")
    localites = list(set(x["localite"] for x in addresses))
    log.debug("Localites found: %s. Expecting 542.", str(len(localites)))
    # if len(localites) != 542:
    #     raise IOError(f"Localites found: {len(localites)}. Expected 542!")
    return addresses, fieldnames
