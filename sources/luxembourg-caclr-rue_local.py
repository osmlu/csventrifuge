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
    with open(os.path.expanduser('~/caclr/RUE'), 'r', encoding='ISO-8859-15') as extracted_file:
        for data in extracted_file:
            caclr.append({
                'numero': trimget(data, 0,  5),
                'nom': trimget(data, 5, 40),
                'mot_tri': trimget(data, 85, 10),
                'code_nomenclature': trimget(data, 95, 5),
                'indic_lieu_dit': trimget(data, 101, 1),
                'date_fin_valid': trimget(data, 102, 10),
                'ds_timestamp_modif': trimget(data, 113,10), 
                'fk_cptch_typerue': trimget(data, 123,2),
                'fk_cptch_numerorue': trimget(data, 126,4),
                'fk_local_numero': trimget(data, 131,5),
                'indic_provisoire': trimget(data, 137, 1)
            })
        return caclr, list(caclr[0].keys())

if __name__ == "__main__":
    print(get())
