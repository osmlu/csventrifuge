from dataclasses import dataclass
import logging
from io import BytesIO

import httpx
import polars as pl

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


@dataclass
class LuxembourgAddresses:
    url: str = "https://data.public.lu/fr/datasets/r/5cadc5b8-6a7d-4283-87bc-f9e58dd771f7"
    delimiter: str = ";"

    def get(self) -> pl.DataFrame:
        r = httpx.get(self.url)
        r.encoding = "utf-8-sig"
        text = r.text
        df = pl.read_csv(
            BytesIO(text.encode("utf-8")),
            separator=self.delimiter,
            encoding="utf8",
            infer_schema_length=0,
        ).with_columns(pl.all().cast(pl.String))
        df = df.with_columns(
            pl.col("rue").alias("rue_orig"),
            pl.col("id_geoportail").str.slice(0, 3).alias("code_commune"),
        )
        df = df.select(["rue_orig", "code_commune", *[c for c in df.columns if c not in {"rue_orig", "code_commune"}]])
        return df


def get():
    return LuxembourgAddresses().get()
