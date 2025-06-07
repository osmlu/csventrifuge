#!/usr/bin/env python

# TODO use a generator instead of loading everything in ram
# DONE deal with rules that apply only in one city, e.g. Rue Churchill
#  which becomes Bd Churchill in Esch only - use an enhancement

# Import necessary libraries
import argparse
import csv
import importlib
import logging
import os
import re
from contextlib import suppress
from types import ModuleType
from typing import Dict, Iterable, Tuple, IO
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.WARNING)
log = logging.getLogger(__name__)

# Typed rulebooks used throughout processing
Rulebook = Dict[str, Dict[str, Tuple[str, int]]]
EnhanceBook = Dict[str, Dict[str, Dict[str, Tuple[str, int]]]]
FilterBook = Dict[str, Dict[str, Tuple[str, int]]]

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
def is_valid_output(parser: argparse.ArgumentParser, arg: str) -> IO[str]:
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


def load_rules(keys: Iterable[str], source_name: str) -> Rulebook:
    """Load the rules for ``source_name``."""
    rulebook: Rulebook = {}
    for key in keys:
        path = Path("rules") / source_name / f"{key}.csv"
        with suppress(IOError):
            with path.open(encoding="utf-8") as rulecsv:
                rulebook[key] = {}
                for row in csv.reader(rulecsv, delimiter="\t"):
                    try:
                        if not row[0].startswith("#"):
                            rulebook[key][row[0]] = (row[1], 0)
                    except IndexError:
                        log.error(f"Could not import rule: {row}")
    return rulebook


def load_enhancements(keys: list[str], source_name: str) -> Tuple[EnhanceBook, set[str]]:
    """Load enhancements for ``source_name`` and update ``keys`` in place."""
    enhancebook: EnhanceBook = {}
    enhanced: set[str] = set()
    for key in list(keys):
        path = Path("enhance") / source_name / key
        with suppress(OSError):
            enhancements = os.listdir(path)
            if enhancements:
                enhancebook[key] = {}
                for filename in enhancements:
                    with (path / filename).open(encoding="utf-8") as enhancecsv:
                        target = filename[:-4]
                        if target not in keys:
                            keys.append(target)
                        enhanced.add(target)
                        enhancebook[key].setdefault(target, {})
                        for erow in csv.reader(enhancecsv, delimiter="\t"):
                            try:
                                if not erow[0].startswith("#"):
                                    enhancebook[key][target][erow[0]] = (
                                        erow[1],
                                        0,
                                    )
                            except IndexError:
                                log.error(
                                    f"Could not import enhancement, erow is: {erow}"
                                )
                log.debug("Enhance book for %s: %s", key, ", ".join(enhancebook[key].keys()))
    return enhancebook, enhanced


def load_filters(keys: Iterable[str], source_name: str) -> FilterBook:
    """Load filters for ``source_name``."""
    filterbook: FilterBook = {}
    for key in keys:
        path = Path("filters") / source_name / f"{key}.csv"
        with suppress(IOError):
            with path.open(encoding="utf-8") as filtercsv:
                filterbook[key] = {}
                for row in csv.reader(filtercsv, delimiter="\t"):
                    if not row[0].startswith("#"):
                        comment = row[1] if len(row) > 1 else ""
                        filterbook[key][row[0]] = (comment, 0)
            log.debug("Filter book for %s is %i entries big.", key, len(filterbook[key]))
    return filterbook

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


def main() -> None:
    """Run the command line interface."""
    args = parser.parse_args()

    source = load_module(args.source, "sources")
    get_data = getattr(source, "get", None)
    if get_data is None:
        raise ImportError('function not found "{}" ({})'.format("get", args.source))

    data, keys = get_data()
    log.debug("Keys are %s", ", ".join(keys))

    rulebook = load_rules(keys, args.source)
    enhancebook, enhanced = load_enhancements(keys, args.source)
    filterbook = load_filters(keys, args.source)

    substitutions = 0
    filtered = 0
    len_data = len(data)

    for key in filterbook:
        filtered_data = [row for row in data if row[key] not in filterbook[key]]
        for deleted in [row for row in data if row[key] in filterbook[key]]:
            comment, count = filterbook[key][deleted[key]]
            filterbook[key][deleted[key]] = (comment, count + 1)
        filtered += len(data) - len(filtered_data)
        data = filtered_data

    for row in data:
        for key in keys:
            orig = row.get(key)
            if orig is not None and rulebook.get(key) and orig in rulebook[key]:
                replacement, count = rulebook[key][orig]
                row[key] = replacement
                rulebook[key][orig] = (replacement, count + 1)
                substitutions += 1
            else:
                if orig is not None:
                    log.debug("No rule for [%s] %s", key, orig)

            if key in enhancebook:
                for enhancement, mapping in enhancebook[key].items():
                    try:
                        replacement, count = mapping[row[key]]
                        row[enhancement] = replacement
                        mapping[row[key]] = (replacement, count + 1)
                    except KeyError:
                        pass
        for enhanced_column in enhanced:
            if enhanced_column not in row:
                log.error("No enhancement found for %s in row %s", enhanced_column, row)

    csv_out = args.output
    writer = csv.DictWriter(csv_out, fieldnames=keys, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(data)
    csv_out.close()
    log.info(
        "{} values out of {} dropped, {:.2%}".format(filtered, len_data, filtered / len_data)
    )
    log.info(
        "{} values out of {} replaced, {:.2%}".format(substitutions, len(data), substitutions / len_data)
    )

    for key in rulebook:
        for rule, (replacement, count) in rulebook[key].items():
            if count == 0:
                log.info('Did not use [{}] rule "{}" -> "{}"'.format(key, rule, replacement))
            else:
                log.debug("Used [{}] rule {} {} times".format(key, rule, count))

    for key in enhancebook:
        for enhancement in enhancebook[key].keys():
            for tkey, (val, count) in enhancebook[key][enhancement].items():
                if count == 0:
                    log.info(
                        'Did not use enhancement [{}] "{}" -> [{}] "{}"'.format(
                            key, tkey, enhancement, val
                        )
                    )

    for key in filterbook:
        for filter_val, (_, count) in filterbook[key].items():
            if count == 0:
                log.info("Did not use filter [{}] {}".format(key, filter_val))


if __name__ == "__main__":
    main()
