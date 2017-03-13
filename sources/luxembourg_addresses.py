# Call with get(), you get a collection containing dicts, and the field names list. That's the deal.

import requests
import csv

def get():
    # The API endpoint that contains the link to the most recent version of the
    # addresses in all available formats (geojson, but also shp).
    UDATA_ADDRESSES = 'https://data.public.lu/api/1/datasets/adresses-georeferencees-bd-adresses/'

    # Eugh, magic numbers.
    # This is just the uuid for the addresses in csv format.
    UDATA_ADDRESSES_ID = '5cadc5b8-6a7d-4283-87bc-f9e58dd771f7'

    # Udata has no permalink. Parse the API to get the latest geojson.
    udata_json = requests.get(UDATA_ADDRESSES).json()

    # Find the resource with that ID in the udata json
    # i.e. our addresses
    for resource in udata_json['resources']:
        if resource['id'] == UDATA_ADDRESSES_ID:
            ADDRESSES_CSV = resource['url']
            break
    else:
        # Oops, the for loop didn't find anything!
        raise IOError("Could not find resource id {} in {}".format(
            UDATA_ADDRESSES_ID, UDATA_ADDRESSES
        ))

    # Downloading the addresses might take ~15 seconds.
    # In the meanwile, shake your wrists and correct your posture.
    r = requests.get(ADDRESSES_CSV)
    r.encoding = 'utf-8'
    req_addresses = r.text.splitlines()
    csvreader = csv.DictReader(req_addresses, delimiter=';')
    addresses = [{k: v for k, v in row.items()}
        for row in csvreader]
    return addresses, csvreader.fieldnames
