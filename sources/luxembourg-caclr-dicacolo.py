#!/usr/bin/env python
# Call with get(), you get a collection containing dicts, and the field names list. That's the deal.

from io import BytesIO, TextIOWrapper
from zipfile import ZipFile
import requests

def trimget(data, startpos, length):
    return data[int(startpos):int(startpos)+int(length)].rstrip(' ')

def get():
    # The API endpoint that contains the link to the most recent version of the
    # CACLR in all available formats (geojson, but also shp).
    UDATA_CACLR = 'https://data.public.lu/api/1/datasets/registre-national-des-localites-et-des-rues/'

    # Eugh, magic numbers.
    # This is just the uuid for the CACLR in csv format.
    UDATA_CACLR_ID = 'af76a119-2bd1-462c-a5bf-23e11ccfd3ee'

    # Udata has no permalink. Parse the API to get the latest geojson.
    udata_json = requests.get(UDATA_CACLR).json()

    # Find the resource with that ID in the udata json
    # i.e. our CACLR
    for resource in udata_json['resources']:
        if resource['id'] == UDATA_CACLR_ID:
            CACLR_ZIP = resource['url']
            break
    else:
        # Oops, the for loop didn't find anything!
        raise IOError("Could not find resource id {} in {}".format(
            UDATA_CACLR_ID, UDATA_CACLR
        ))

    # Downloading the CACLR might take ~15 seconds.
    # In the meanwile, shake your wrists and correct your posture.
    r = requests.get(CACLR_ZIP)
    zipfile = ZipFile(BytesIO(r.content))
    zip_names = zipfile.namelist()
    extracted_file = zipfile.open("TR.DICACOLO.RUCP")
    caclr = []
    for data in TextIOWrapper(extracted_file, "latin-1"):
        caclr.append({
            'district': trimget(data, 0,  40),
            'canton': trimget(data, 40, 40),
            'commune': trimget(data, 80, 40),
            'localite': trimget(data, 120,40),
            'rue': trimget(data, 160,40),
            'code_postal': trimget(data, 200, 4)
        })
    return caclr, ['district', 'canton', 'commune', 'localite', 'rue', 'code_postal']

if __name__ == "__main__":
    print(get())
