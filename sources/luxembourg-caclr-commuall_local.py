#!/usr/bin/env python
# Call with get(), you get a collection containing dicts, and the field names list. That's the deal.

import os
import polars as pl

def trimget(data, startpos, length):
    return data[int(startpos):int(startpos)+int(length)].rstrip(' ')

def get() -> pl.DataFrame:
    """Return commune information as a ``polars.DataFrame``."""
    caclr = []
    with open(
        os.path.expanduser('~/caclr/COMMUALL'),
        'r',
        encoding='ISO-8859-15'
    ) as extracted_file:
        for data in extracted_file:
            caclr.append({
                'code': trimget(data, 0,  2),
                'nom': trimget(data, 2, 40),
                'ds_timestamp_modif': trimget(data, 82,10),
                'fk_canto_code': trimget(data, 92,2),
                'indic_fusionnee': trimget(data, 94, 1),
            })
    df = pl.DataFrame(caclr).with_columns(pl.all().cast(pl.String))
    return df

if __name__ == "__main__":
    print(get())
