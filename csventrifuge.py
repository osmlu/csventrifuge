#!/usr/bin/env -S uv run --script
# /// script
# dependencies = [
#     "polars>=0.20",
#     "httpx==0.27.0",
#     "pytest"
# ]
# requires-python = ">=3.14"
# ///

# NOTE: Future enhancement - use generators instead of loading everything into RAM
# DONE: deal with rules that apply only in one city, e.g. Rue Churchill
#  which becomes Bd Churchill in Esch only - use an enhancement

# Import necessary libraries
import argparse
import importlib.util
import logging
from dataclasses import dataclass, field
from typing import Dict, Iterable, Tuple, TextIO
from pathlib import Path
from types import ModuleType
import polars as pl

# Directory constants
RULES_DIR = Path("rules")
ENHANCE_DIR = Path("enhance")
FILTERS_DIR = Path("filters")
SOURCES_DIR = Path("sources")


# Typed wrappers
@dataclass
class Entry:
    """Mapping or filter entry that tracks how often it is used."""

    value: str
    count: int = 0


@dataclass
class TransformStats:
    """Statistics for a transformation operation."""

    matched_count: int = 0
    affected_count: int = 0


@dataclass
class Transformation:
    """Represents a transformation that can be applied to a DataFrame.

    Supports filters, rules, and enhancements.
    """

    key: str  # Column name
    mappings: Dict[str, str]  # old value -> new value
    stats: TransformStats = field(default_factory=TransformStats)

    def apply_and_count(self, df: pl.DataFrame) -> Tuple[pl.DataFrame, TransformStats]:
        """Apply transformation and return updated DataFrame with statistics."""
        if not self.mappings:
            return df, self.stats

        keys = list(self.mappings.keys())

        # Count matches before transformation
        matches = df.filter(pl.col(self.key).is_in(keys))
        if matches.height > 0:
            vc = matches.get_column(self.key).value_counts()
            self.stats.affected_count = sum(count for _, count in vc.rows())

        # Apply transformation
        replace_map = dict(self.mappings)
        df_transformed = df.with_columns(
            pl.col(self.key).replace(replace_map).alias(self.key)
        )
        self.stats.matched_count = len(self.mappings)

        return df_transformed, self.stats


Rulebook = Dict[str, Dict[str, Entry]]
EnhanceBook = Dict[str, Dict[str, Dict[str, Entry]]]
FilterBook = Dict[str, Dict[str, Entry]]
# Set up logging
logging.basicConfig(level=logging.WARNING)
log = logging.getLogger(__name__)


def load_module(wanted_module: str, origin: str) -> ModuleType:
    """
    Load the specified module from the given origin directory.

    Args:
        wanted_module (str): The desired module to load.
        origin (str): The directory in which to search for the module.
    Returns:
        The loaded module.
    Raises:
        ImportError: If the desired module is not found in the origin directory.
    """
    # Build the full path to the module file
    module_dir = Path(__file__).parent / origin
    module_file = module_dir / f"{wanted_module}.py"

    if not module_file.exists():
        raise ImportError(f'module not found "{wanted_module}" ({origin})')

    log.debug("Loading module %s from %s", wanted_module, module_file)

    # Use importlib.util to load the module from file
    spec = importlib.util.spec_from_file_location(
        f"{origin}.{wanted_module}", module_file
    )
    if spec is None or spec.loader is None:
        raise ImportError(f'could not load "{wanted_module}" ({origin})')

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def is_valid_source(  # pylint: disable=inconsistent-return-statements
    arg_parser: argparse.ArgumentParser, arg: str
) -> str:
    """
    Check if the input source definition file exists.

    Args:
        arg_parser: The argparse parser object.
        arg (str): The input source definition file.
    Returns:
        The argument if the input source definition file exists.

    Note:
        Raises SystemExit via arg_parser.error() if file doesn't exist.
    """
    # Check if the input source definition file exists
    source_file = SOURCES_DIR / f"{arg}.py"
    if not source_file.exists():
        arg_parser.error(f"The input source definition {source_file} does not exist")
        return ""  # unreachable after error()
    # If the argument is a valid source definition file, return the argument
    return arg


# Define function to check if output file is valid
def is_valid_output(
    arg_parser: argparse.ArgumentParser, arg: str
) -> TextIO:  # pylint: disable=consider-using-with
    """
    Check if the output file can be written to.

    Args:
        arg_parser: The argparse parser object.
        arg (str): The output file.
    Returns:
        The output file if it can be written to.

    Note:
        Deliberately returns an unclosed file handle for caller to manage.
    """
    # Try opening the output file for writing, encoded in utf-8 and with
    # normalized newlines.
    try:
        output = open(  # pylint: disable=consider-using-with
            arg, "w", encoding="utf-8", newline=""
        )
    # If an OSError occurs, raise an error stating that the output file
    # cannot be written to
    except OSError:
        arg_parser.error(f"Unable to write to file {arg}")
    # If no error occurs, return the output file
    else:
        return output


# Set up argument parser to parse input source and output file
parser = argparse.ArgumentParser(
    description="Rewrite [source] csv, and output to [output]"
)
parser.add_argument(
    "source",
    metavar="source",
    type=lambda x: is_valid_source(parser, x),
    help="Input source definition",
)
parser.add_argument(
    "output",
    metavar="output",
    default="csventrifuge-out.csv",
    type=lambda x: is_valid_output(parser, x),
    help="Output file",
    nargs="?",
)


def load_rules(source: str, keys: Iterable[str]) -> Rulebook:
    """Load rule CSV files for the given source."""
    book: Rulebook = {}
    for key in keys:
        path = RULES_DIR / source / f"{key}.csv"
        if not path.exists():
            continue
        book[key] = {}
        df = pl.read_csv(
            path,
            separator="\t",
            has_header=False,
            new_columns=["old", "new"],
            comment_prefix="#",
            schema={"old": pl.String, "new": pl.String},
            encoding="utf8",
        )
        for old, new in df.iter_rows():
            book[key][old] = Entry(new)
    return book


def load_enhancements(source: str, keys: list[str]) -> Tuple[EnhanceBook, set[str]]:
    """Load enhancement CSV files for the given source."""
    book: Dict[str, Dict[str, Dict[str, Entry]]] = {}
    enhanced: set[str] = set()
    for key in list(keys):
        enhancepath = ENHANCE_DIR / source / key
        if not enhancepath.is_dir():
            continue
        book[key] = {}
        for filepath in enhancepath.glob("*.csv"):
            target = filepath.stem
            if target not in keys:
                keys.append(target)
            enhanced.add(target)
            book[key][target] = {}
            df = pl.read_csv(
                filepath,
                separator="\t",
                has_header=False,
                new_columns=["old", "new"],
                comment_prefix="#",
                schema={"old": pl.String, "new": pl.String},
                encoding="utf8",
            )
            for old, new in df.iter_rows():
                book[key][target][old] = Entry(new)
        log.debug("Enhance book for %s: %s", key, ", ".join(book[key].keys()))
    return book, enhanced


def load_filters(source: str, keys: Iterable[str]) -> FilterBook:
    """Load filter CSV files for the given source."""
    book: FilterBook = {}
    for key in keys:
        path = FILTERS_DIR / source / f"{key}.csv"
        if not path.exists():
            continue
        book[key] = {}
        df = pl.read_csv(
            path,
            separator="\t",
            has_header=False,
            new_columns=["value", "why"],
            comment_prefix="#",
            schema={"value": pl.String, "why": pl.String},
            encoding="utf8",
        )
        for value, _ in df.iter_rows():
            book[key][value] = Entry(value)
        log.debug("Filter book for %s is %i entries big.", key, len(book[key]))
    return book


def _apply_filter_transformation(
    df: pl.DataFrame,
    key: str,
    mapping: Dict[str, Entry],
) -> Tuple[pl.DataFrame, int]:
    """Apply filter transformation: count and remove matching rows."""
    values = list(mapping.keys())
    matches = df.filter(pl.col(key).is_in(values))
    affected = 0
    if matches.height > 0:
        vc = matches.get_column(key).value_counts()
        for value_str, count in vc.rows():
            mapping[value_str].count = count
            affected += count
    return df.filter(~pl.col(key).is_in(values)), affected


def _apply_replace_transformation(
    df: pl.DataFrame,
    key: str,
    mapping: Dict[str, Entry],
) -> Tuple[pl.DataFrame, int]:
    """Apply replacement transformation: count and replace values."""
    replace_map = {k: v.value for k, v in mapping.items()}
    matches = df.filter(pl.col(key).is_in(list(replace_map.keys())))
    affected = 0
    if matches.height > 0:
        vc = matches.get_column(key).value_counts()
        for value_str, count in vc.rows():
            mapping[value_str].count = count
            affected += count
    return (
        df.with_columns(pl.col(key).replace(replace_map).alias(key)),
        affected,
    )


def apply_transformations(
    df: pl.DataFrame,
    book: Dict[str, Dict[str, Entry]],
    is_filter: bool = False,
) -> Tuple[pl.DataFrame, int]:
    """
    Apply a set of transformations (filters, rules, or enhancements) to a DataFrame.

    Args:
        df: The input DataFrame
        book: Dictionary mapping column names to transformation mappings
        is_filter: If True, remove matching rows instead of replacing values

    Returns:
        Tuple of (transformed_df, total_affected_count)
    """
    total_affected = 0
    transformer = (
        _apply_filter_transformation if is_filter else _apply_replace_transformation
    )

    for key, mapping in book.items():
        if not mapping:
            continue
        df, affected = transformer(df, key, mapping)
        total_affected += affected

    return df, total_affected


def apply_enhancements(
    df: pl.DataFrame,
    enhancebook: Dict[str, Dict[str, Dict[str, Entry]]],
) -> Tuple[pl.DataFrame, int]:
    """
    Apply enhancements to a DataFrame (add or replace columns based on another column).

    Args:
        df: The input DataFrame
        enhancebook: Dictionary mapping source columns to target columns to mappings

    Returns:
        Tuple of (transformed_df, total_affected_count)
    """
    total_affected = 0

    for key, targets in enhancebook.items():
        for target, mapping in targets.items():
            if not mapping:
                continue

            replace_map = {k: v.value for k, v in mapping.items()}
            matches = df.filter(pl.col(key).is_in(list(replace_map.keys())))
            if matches.height > 0:
                vc = matches.get_column(key).value_counts()
                for value_str, count in vc.rows():
                    mapping[value_str].count = count
                    total_affected += count

            # Apply enhancement: replace values in key column, and set target column
            df = df.with_columns(
                pl.when(pl.col(key).is_in(list(replace_map.keys())))
                .then(pl.col(key).replace(replace_map))
                .otherwise(pl.col(target))
                .alias(target)
            )

    return df, total_affected


def validate_enhancements(df: pl.DataFrame, enhanced: set[str]) -> None:
    """
    Validate that all enhanced columns have been properly populated.

    Args:
        df: The DataFrame to validate
        enhanced: Set of column names that should have been enhanced
    """
    for col in enhanced:
        null_rows = df.filter(pl.col(col).is_null())
        if null_rows.height > 0:
            for row in null_rows.rows(named=True):
                log.error("No enhancement found for %s in row %s", col, row)


def _report_filter_stats(filterbook: FilterBook) -> None:
    """Report statistics for unused filters."""
    for key, filters in filterbook.items():
        for value, entry in filters.items():
            if entry.count == 0:
                log.info("Did not use filter [%s] %s", key, value)


def _report_rule_stats(rulebook: Rulebook) -> None:
    """Report statistics for rules."""
    for key, mapping in rulebook.items():
        for rule, entry in mapping.items():
            if entry.count == 0:
                log.info(
                    'Did not use [%s] rule "%s" -> "%s"',
                    key,
                    rule,
                    entry.value,
                )
            else:
                log.debug("Used [%s] rule %s %d times", key, rule, entry.count)


def _report_enhancement_stats(enhancebook: EnhanceBook) -> None:
    """Report statistics for unused enhancements."""
    for key, targets in enhancebook.items():
        for enhancement, mapping in targets.items():
            for tkey, entry in mapping.items():
                if entry.count == 0:
                    log.info(
                        'Did not use enhancement [%s] "%s" -> [%s] "%s"',
                        key,
                        tkey,
                        enhancement,
                        entry.value,
                    )


def report_statistics(
    len_data: int,
    filtered: int,
    substitutions: int,
    rulebook: Rulebook,
    enhancebook: EnhanceBook,
    filterbook: FilterBook,
    df: pl.DataFrame,
) -> None:  # pylint: disable=too-many-arguments,too-many-positional-arguments
    """
    Report statistics about transformations applied.

    Args:
        len_data: Original number of rows
        filtered: Number of rows filtered out
        substitutions: Number of values substituted
        rulebook: Dictionary of rules applied
        enhancebook: Dictionary of enhancements applied
        filterbook: Dictionary of filters applied
        df: Final DataFrame
    """
    log.info(
        "%d values out of %d dropped, %.2f%%",
        filtered,
        len_data,
        filtered / len_data,
    )
    log.info(
        "%d values out of %d replaced, %.2f%%",
        substitutions,
        df.height,
        substitutions / df.height if df.height > 0 else 0,
    )
    _report_rule_stats(rulebook)
    _report_enhancement_stats(enhancebook)
    _report_filter_stats(filterbook)


def main() -> None:
    """Entry point executed by the CLI."""
    args = parser.parse_args()
    source = load_module(args.source, "sources")
    get_data = getattr(source, "get", None)
    if get_data is None:
        raise ImportError(f'function not found "get" ({args.source})')

    # All current sources expose a ``get`` function that returns a Polars
    # DataFrame directly.
    df = get_data()
    keys = list(df.columns)
    log.debug("Keys are %s", ", ".join(keys))

    rulebook = load_rules(args.source, keys)
    enhancebook, enhanced = load_enhancements(args.source, keys)
    filterbook = load_filters(args.source, keys)

    len_data = df.height

    # Apply filters (remove rows)
    df, filtered = apply_transformations(df, filterbook, is_filter=True)

    # Apply rules (replace values)
    df, substitutions = apply_transformations(df, rulebook, is_filter=False)

    # Apply enhancements (add columns)
    df, _ = apply_enhancements(df, enhancebook)

    # Validate enhancements
    validate_enhancements(df, enhanced)

    # Write output
    df.write_csv(args.output)
    args.output.close()

    # Report statistics
    report_statistics(
        len_data,
        filtered,
        substitutions,
        rulebook,
        enhancebook,
        filterbook,
        df,
    )


if __name__ == "__main__":
    main()
