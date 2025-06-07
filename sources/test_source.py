from dataclasses import dataclass

import polars as pl

@dataclass
class TestSource:
    delimiter: str = ","
    __test__ = False

    def get(self) -> pl.DataFrame:
        df = pl.DataFrame({"foo": [None]}).with_columns(pl.all().cast(pl.String))
        return df


def get():
    return TestSource().get()
