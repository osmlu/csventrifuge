#!/usr/bin/env python
# Call with get(), you get a collection containing dicts, and the field names list. That's the deal.

from io import BytesIO, TextIOWrapper
from zipfile import ZipFile

import requests


def trimget(data, startpos, length):
    return data[int(startpos) : int(startpos) + int(length)].rstrip(" ")


def get():
    # The endpoint that redirects to the most recent version of the
    # CACLR in zip.
    CACLR_ZIP = (
        "https://data.public.lu/fr/datasets/r/af76a119-2bd1-462c-a5bf-23e11ccfd3ee"
    )

    # Downloading the CACLR might take ~15 seconds.
    # In the meanwhile, shake your wrists and correct your posture.
    r = requests.get(CACLR_ZIP)
    zipfile = ZipFile(BytesIO(r.content))
    # zip_names = zipfile.namelist()
    extracted_file = zipfile.open("TR.DICACOLO.RUCP")
    caclr = []
    for data in TextIOWrapper(extracted_file, "latin-1"):
        caclr.append(
            {
                "district": trimget(data, 0, 40),
                "canton": trimget(data, 40, 40),
                "commune": trimget(data, 80, 40),
                "localite": trimget(data, 120, 40),
                "rue": trimget(data, 160, 40),
                "code_postal": trimget(data, 200, 4),
            }
        )
    return caclr, ["district", "canton", "commune", "localite", "rue", "code_postal"]


if __name__ == "__main__":
    print(get())
