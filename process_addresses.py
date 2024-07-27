from datetime import datetime
from pathlib import Path
import polars as pl
import geojson
from geojson import Feature, FeatureCollection, Point
from typing import List

def process_addresses(input_file: str, output_dir: str) -> None:
    date_str = datetime.now().strftime("%Y-%m-%d")
    output_csv_file = Path(output_dir) / f"{date_str}-addresses-josm.csv"
    latest_csv_symlink = Path(output_dir) / "latest-addresses.csv"
    geojson_file = Path(output_dir) / "luxembourg-addresses.geojson"

    # Read the CSV file using polars
    df = pl.read_csv(input_file)

    # Process the data
    df = df.with_columns([
        pl.when(pl.col("rue") == "Maison")
          .then("")
          .otherwise(pl.col("rue"))
          .alias("addr:street"),
        pl.when(pl.col("rue") == "Maison")
          .then(pl.col("localite"))
          .otherwise("")
          .alias("addr:place"),
        pl.col("numero").alias("addr:housenumber"),
        pl.col("localite").alias("addr:city"),
        pl.col("code_postal").alias("addr:postcode"),
        pl.col("lat_wgs84"),
        pl.col("lon_wgs84"),
        pl.col("id_caclr_bat").alias("ref:caclr")
    ])

    # Select and reorder the columns
    df = df.select([
        "addr:housenumber", "addr:street", "addr:place", "addr:postcode", "addr:city",
        "lat_wgs84", "lon_wgs84", "ref:caclr"
    ])

    # Write the processed data to CSV
    df.write_csv(output_csv_file)

    # Generate GeoJSON
    features: List[Feature] = [
        Feature(
            geometry=Point((row["lon_wgs84"], row["lat_wgs84"])),
            properties={
                "addr:housenumber": row["addr:housenumber"],
                "addr:street": row["addr:street"],
                "addr:place": row["addr:place"],
                "addr:postcode": row["addr:postcode"],
                "addr:city": row["addr:city"],
                "ref:caclr": row["ref:caclr"]
            }
        ) for row in df.to_dicts()
    ]

    feature_collection = FeatureCollection(features)
    with open(geojson_file, 'w') as f:
        geojson.dump(feature_collection, f)

    # Manage symlink
    if latest_csv_symlink.exists() or latest_csv_symlink.is_symlink():
        latest_csv_symlink.unlink()
    latest_csv_symlink.symlink_to(output_csv_file)

    print("Conversion complete.")

if __name__ == "__main__":
    input_file = 'luxembourg-addresses.csv'
    output_dir = '../public_html/csventrifuge'
    process_addresses(input_file, output_dir)
