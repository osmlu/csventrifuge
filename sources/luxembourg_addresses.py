from dataclasses import dataclass
import logging
from io import BytesIO
from pathlib import Path
from typing import Optional

import httpx
import polars as pl

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


@dataclass
class LuxembourgAddresses:
    url: str = (
        "https://data.public.lu/fr/datasets/r/5cadc5b8-6a7d-4283-87bc-f9e58dd771f7"
    )
    delimiter: str = ";"
    cache_file: Path = Path("stuff/addresses.csv")
    cache_url_file: Path = Path("stuff/addresses-url.txt")

    def _read_df(self, payload: bytes) -> pl.DataFrame:
        # Handle UTF-8 BOM without converting through str.
        if payload.startswith(b"\xef\xbb\xbf"):
            payload = payload[3:]
        return pl.read_csv(
            BytesIO(payload),
            separator=self.delimiter,
            encoding="utf8",
            infer_schema_length=0,
        ).with_columns(pl.all().cast(pl.String))

    def _resolve_redirect(self) -> str:
        """Get the final S3 URL from the redirect chain."""
        with httpx.Client(follow_redirects=False, timeout=30.0) as client:
            r = client.get(self.url)
            if r.status_code in (301, 302, 303, 307, 308):
                location = r.headers.get("location")
                if location:
                    return location
            r.raise_for_status()
        return self.url

    def _get_cached_url(self) -> Optional[str]:
        """Get the stored resolved URL."""
        if not self.cache_url_file.exists():
            return None
        try:
            return self.cache_url_file.read_text(encoding="utf-8").strip()
        except OSError:
            return None

    def _store_resolved_url(self, url: str) -> None:
        """Store the resolved URL."""
        self.cache_url_file.parent.mkdir(parents=True, exist_ok=True)
        self.cache_url_file.write_text(url, encoding="utf-8")

    def clear_cache(self) -> int:
        """Delete cached payload and URL marker files.

        Returns:
            Number of files removed.
        """
        removed = 0
        for path in (self.cache_file, self.cache_url_file):
            if path.exists():
                path.unlink()
                removed += 1
        return removed

    def get(self) -> pl.DataFrame:
        # Check if redirect target changed
        current_url = self._resolve_redirect()
        cached_url = self._get_cached_url()

        if current_url == cached_url and self.cache_file.exists():
            log.debug("Using cached addresses file (%s)", self.cache_file)
            payload = self.cache_file.read_bytes()
        else:
            # Cache is stale or missing, download fresh
            log.debug("Downloading fresh addresses from %s", current_url)
            with httpx.Client(follow_redirects=True, timeout=30.0) as client:
                r = client.get(self.url)
                r.raise_for_status()
                payload = r.content
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            self.cache_file.write_bytes(payload)
            self._store_resolved_url(current_url)

        df = self._read_df(payload)
        df = df.with_columns(
            pl.col("rue").alias("rue_orig"),
        )
        return df


def get():
    return LuxembourgAddresses().get()


def clear_cache() -> int:
    """Clear local cache files used by Luxembourg addresses source."""
    return LuxembourgAddresses().clear_cache()
