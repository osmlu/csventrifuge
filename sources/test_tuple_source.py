from dataclasses import dataclass

import polars as pl

@dataclass
class TestTupleSource:
    delimiter: str = ","
    __test__ = False

    def get(self):
        return pl.DataFrame({"foo": ["bar"]}).with_columns(pl.all().cast(pl.String))

def get():
    return TestTupleSource().get()
