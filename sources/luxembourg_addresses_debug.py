# Call with get(), you get a collection containing dicts, and the field names list. That's the deal.

import csv
import polars as pl


def get() -> pl.DataFrame:
    """Return a DataFrame with a ``code_commune`` column."""
    with open("stuff/addresses.csv", "r") as csvfile:
        csvreader = csv.DictReader(csvfile, delimiter=";")
        addresses = [{k: v for k, v in row.items()} for row in csvreader]
    for row in addresses:
        row["code_commune"] = row["id_geoportail"][:3]
    df = pl.DataFrame(addresses).with_columns(pl.all().cast(pl.String))
    # put ``code_commune`` first for consistency with other sources
    df = df.select(["code_commune", *[c for c in df.columns if c != "code_commune"]])
    return df
