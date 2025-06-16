#!/usr/bin/env python
# Call with get(), you get a collection containing dicts, and the field names list. That's the deal.

from io import BytesIO, TextIOWrapper
from zipfile import ZipFile
import requests
import os

def trimget(data, startpos, length):
    return data[int(startpos):int(startpos)+int(length)].rstrip(' ')

def get():
    caclr = []
    with open(os.path.expanduser('~/caclr/COMMUALL'), 'r', encoding='ISO-8859-15') as extracted_file:
        for data in extracted_file:
            caclr.append({
                'code': trimget(data, 0,  2),
                'nom': trimget(data, 2, 40),
                'ds_timestamp_modif': trimget(data, 82,10), 
                'fk_canto_code': trimget(data, 92,2),
                'indic_fusionnee': trimget(data, 94, 1)
            })
        return caclr, ['code', 'nom', 'nom_majuscule', 'ds_timestamp_modif', 'fk_canto_code', 'indic_fusionnee']

if __name__ == "__main__":
    print(get())
