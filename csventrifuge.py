#!/usr/bin/env -S uv pip install --system --strict --require-virtualenv --quiet
# [project]
# dependencies = [
#     "polars>=0.20",
#     "httpx==0.27.0",
# ]
# requires-python = ">=3.12"
# [tool.uv]
# cutoff = "2025-06-07"

# TODO use a generator instead of loading everything in ram
# DONE deal with rules that apply only in one city, e.g. Rue Churchill
#  which becomes Bd Churchill in Esch only - use an enhancement

# Import necessary libraries
import argparse
import importlib
import logging
import os
import re
from contextlib import suppress
from dataclasses import dataclass
from typing import Dict, Iterable, Tuple, TextIO
from pathlib import Path
from types import ModuleType
import polars as pl

# Typed wrappers
@dataclass
class RuleEntry:
    replacement: str
    count: int = 0


@dataclass
class FilterEntry:
    value: str
    count: int = 0


Rulebook = Dict[str, Dict[str, RuleEntry]]
EnhanceBook = Dict[str, Dict[str, Dict[str, RuleEntry]]]
FilterBook = Dict[str, Dict[str, FilterEntry]]
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
    # Compile regular expression to search for .py files
    pysearchre = re.compile(".py$", re.IGNORECASE)
    # Filter module files using compiled regular expression
    modulefiles = filter(
        pysearchre.search, os.listdir(os.path.join(os.path.dirname(__file__), origin))
    )
    # Create a list of modules by mapping form_module to modulefiles
    modules = map(form_module, modulefiles)
    # Import parent module/namespace
    importlib.import_module(origin)
    # Iterate through modules and find the desired module
    for module in modules:
        if module == "." + wanted_module:
            log.debug(f"Loading module {module}")
            return importlib.import_module(module, package="sources")
    # If the desired module is not found, raise an ImportError
    raise ImportError(f'module not found "{wanted_module}" ({origin})')

def form_module(fp: str) -> str:
    """
    Form a module name from a filepath.

    Args:
        fp (str): The filepath from which to form a module name.
    Returns:
        The formed module name.
    """
    return "." + os.path.splitext(fp)[0]

def is_valid_source(parser: argparse.ArgumentParser, arg: str) -> str:
    """
    Check if the input source definition file exists.

    Args:
        parser: The argparse parser object.
        arg (str): The input source definition file.
    Returns:
        The argument if the input source definition file exists.
    """
    # Check if the input source definition file exists
    if not os.path.exists(f"sources/{arg}.py"):
        parser.error(
            f"The input source definition sources/{arg}.py does not exist"
        )
        return False
    # If the argument is a valid source definition file, return the argument
    return arg

# Define function to check if output file is valid
def is_valid_output(parser: argparse.ArgumentParser, arg: str) -> TextIO:
    """
    Check if the output file can be written to.

    Args:
        parser: The argparse parser object.
        arg (str): The output file.
    Returns:
        The output file if it can be written to.
    """
    # Try opening the output file for writing, encoding it in utf-8 and using a newline
    try:
        output = open(arg, "w", encoding="utf-8", newline="")
    # If an OSError occurs, raise an error stating that the output file cannot be written to
    except OSError:
        parser.error(f"Unable to write to file {arg}")
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
        path = Path("rules") / source / f"{key}.csv"
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
            book[key][old] = RuleEntry(new)
    return book


def load_enhancements(source: str, keys: list[str]) -> Tuple[EnhanceBook, set[str]]:
    """Load enhancement CSV files for the given source."""
    book: Dict[str, Dict[str, Dict[str, RuleEntry]]] = {}
    enhanced: set[str] = set()
    for key in list(keys):
        enhancepath = Path("enhance") / source / key
        if not enhancepath.is_dir():
            continue
        book[key] = {}
        for filename in os.listdir(enhancepath):
            filepath = enhancepath / filename
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
                book[key][target][old] = RuleEntry(new)
        log.debug("Enhance book for %s: %s", key, ", ".join(book[key].keys()))
    return book, enhanced


def load_filters(source: str, keys: Iterable[str]) -> FilterBook:
    """Load filter CSV files for the given source."""
    book: FilterBook = {}
    for key in keys:
        path = Path("filters") / source / f"{key}.csv"
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
            book[key][value] = FilterEntry(value)
        log.debug("Filter book for %s is %i entries big.", key, len(book[key]))
    return book


def main() -> None:
    """Entry point executed by the CLI."""
    args = parser.parse_args()
    source = load_module(args.source, "sources")
    get_data = getattr(source, "get", None)
    if get_data is None:
        raise ImportError(f'function not found "get" ({args.source})')

    # All current sources expose a ``get`` function that returns a Polars
    # DataFrame directly.  Previous versions returned the CSV path and the
    # column list instead; the extra logic below handled both styles.  If new
    # sources revive that convention we can reintroduce it, but for now the
    # returned value is always a DataFrame.
    df = get_data()
    keys = list(df.columns)
    log.debug("Keys are %s", ", ".join(keys))

    rulebook = load_rules(args.source, keys)
    enhancebook, enhanced = load_enhancements(args.source, keys)
    filterbook = load_filters(args.source, keys)

    filtered = 0
    len_data = df.height
    for key, filters in filterbook.items():
        values = list(filters.keys())
        vc = df.filter(pl.col(key).is_in(values)).get_column(key).value_counts()
        for row in vc.rows():
            filters[row[0]].count = row[1]
            filtered += row[1]
        df = df.filter(~pl.col(key).is_in(values))

    substitutions = 0
    for key, mapping in rulebook.items():
        if not mapping:
            continue
        replace_map = {k: v.replacement for k, v in mapping.items()}
        vc = df.filter(pl.col(key).is_in(list(replace_map.keys()))).get_column(key).value_counts()
        for row in vc.rows():
            mapping[row[0]].count = row[1]
            substitutions += row[1]
        df = df.with_columns(pl.col(key).replace(replace_map).alias(key))

    for key, targets in enhancebook.items():
        for target, mapping in targets.items():
            replace_map = {k: v.replacement for k, v in mapping.items()}
            vc = df.filter(pl.col(key).is_in(list(replace_map.keys()))).get_column(key).value_counts()
            for row in vc.rows():
                mapping[row[0]].count = row[1]
            df = df.with_columns(
                pl.when(pl.col(key).is_in(list(replace_map.keys())))
                .then(pl.col(key).replace(replace_map))
                .otherwise(pl.col(target))
                .alias(target)
            )

    for col in enhanced:
        for row in df.filter(pl.col(col).is_null()).rows(named=True):
            log.error("No enhancement found for %s in row %s", col, row)

    df.write_csv(args.output)
    args.output.close()

    log.info("%d values out of %d dropped, %.2f%%", filtered, len_data, filtered / len_data)
    log.info("%d values out of %d replaced, %.2f%%", substitutions, df.height, substitutions / df.height)

    for key in rulebook:
        for rule, entry in rulebook[key].items():
            if entry.count == 0:
                log.info('Did not use [{}] rule "{}" -> "{}"'.format(key, rule, entry.replacement))
            else:
                log.debug("Used [{}] rule {} {} times".format(key, rule, entry.count))

    for key, targets in enhancebook.items():
        for enhancement, mapping in targets.items():
            for tkey, entry in mapping.items():
                if entry.count == 0:
                    log.info('Did not use enhancement [{}] "{}" -> [{}] "{}"'.format(key, tkey, enhancement, entry.replacement))

    for key, filters in filterbook.items():
        for value, entry in filters.items():
            if entry.count == 0:
                log.info("Did not use filter [{}] {}".format(key, value))


if __name__ == "__main__":
    main()
