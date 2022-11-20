# Call with get(), you get a collection containing dicts, and the field names list. That's the deal.

import csv


def get():
    with open("stuff/addresses.csv", "r") as csvfile:
        csvreader = csv.DictReader(csvfile, delimiter=";")
        fieldnames = csvreader.fieldnames
        addresses = [{k: v for k, v in row.items()} for row in csvreader]
        for row in addresses:
            row["code_commune"] = row["id_geoportail"][:3]
        fieldnames.insert(0, "code_commune")
        return addresses, fieldnames
