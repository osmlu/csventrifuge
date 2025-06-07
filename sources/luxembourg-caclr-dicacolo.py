from dataclasses import dataclass
from io import BytesIO, TextIOWrapper
from zipfile import ZipFile

import httpx
import polars as pl


def trimget(data: str, startpos: int, length: int) -> str:
    return data[int(startpos) : int(startpos) + int(length)].rstrip(" ")


@dataclass
class CaclrDicacolo:
    url: str = "https://data.public.lu/fr/datasets/r/af76a119-2bd1-462c-a5bf-23e11ccfd3ee"
    delimiter: str = ","

    def get(self) -> pl.DataFrame:
        r = httpx.get(self.url)
        zipfile = ZipFile(BytesIO(r.content))
        extracted_file = zipfile.open("TR.DICACOLO.RUCP")
        rows = []
        fieldnames = [
            "district",
            "canton",
            "commune",
            "localite",
            "rue",
            "code_postal",
        ]
        for data in TextIOWrapper(extracted_file, "iso-8859-15"):
            rows.append([
                trimget(data, 0, 40),
                trimget(data, 40, 40),
                trimget(data, 80, 40),
                trimget(data, 120, 40),
                trimget(data, 160, 40),
                trimget(data, 200, 4),
            ])
        df = pl.DataFrame(rows, schema=fieldnames, orient="row")
        df = df.with_columns(pl.all().cast(pl.String))
        return df


def get():
    return CaclrDicacolo().get()


if __name__ == "__main__":
    print(get())
