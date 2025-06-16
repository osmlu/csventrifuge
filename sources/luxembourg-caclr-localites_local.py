#!/usr/bin/env python
# Call with get(), you get a collection containing dicts, and the field names list. That's the deal.

import os
import polars as pl

def trimget(data, startpos, length):
    return data[int(startpos):int(startpos)+int(length)].rstrip(' ')

def get() -> pl.DataFrame:
    """Return localities as a ``polars.DataFrame``."""
    caclr = []
    with open(
        os.path.expanduser('~/caclr/LOCALITE'),
        'r',
        encoding='ISO-8859-15'
    ) as extracted_file:
        for data in extracted_file:
            caclr.append({
                'numero': trimget(data, 0,  5),
                'nom': trimget(data, 5, 40),
                'code': trimget(data, 85, 2),
                'indic_ville': trimget(data, 87, 1),
                'date_fin_valid': trimget(data, 87, 10),
                'ds_timestamp_modif': trimget(data, 99,10),
                'fk_canto_code': trimget(data, 109,2),
                'fk_commu_code': trimget(data, 112, 2),
            })
    df = pl.DataFrame(caclr).with_columns(pl.all().cast(pl.String))
    return df

if __name__ == "__main__":
    print(get())
