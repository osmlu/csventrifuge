#!/usr/bin/env python
# Call with get(), you get a collection containing dicts, and the field names list. That's the deal.

from io import TextIOWrapper
import os

def trimget(data, startpos, length):
    return data[int(startpos) : int(startpos) + int(length)].rstrip(" ")


def get():
    caclr = []
    with open(os.path.expanduser("~/caclr/TR.DICACOLO.RUCP", "r")) as extracted_file:
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
        return caclr, [
            "district",
            "canton",
            "commune",
            "localite",
            "rue",
            "code_postal",
        ]


if __name__ == "__main__":
    print(get())
