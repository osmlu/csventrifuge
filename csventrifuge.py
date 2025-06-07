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
from typing import Dict
import polars as pl
# Set up logging
logging.basicConfig(level=logging.WARNING)
log = logging.getLogger(__name__)

def load_module(wanted_module, origin):
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

def form_module(fp):
    """
    Form a module name from a filepath.

    Args:
        fp (str): The filepath from which to form a module name.
    Returns:
        The formed module name.
    """
    return "." + os.path.splitext(fp)[0]

def is_valid_source(parser, arg):
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
def is_valid_output(parser, arg):
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


def main() -> None:
    """Entry point executed by the CLI."""
    args = parser.parse_args()
    source = load_module(args.source, "sources")
    get_data = getattr(source, "get", None)
    if get_data is None:
        raise ImportError(f'function not found "get" ({args.source})')

    data, keys = get_data()
    log.debug("Keys are %s", ", ".join(keys))
    df = pl.DataFrame(data)

    rulebook: Dict[str, dict] = {}
    for key in keys:
        with suppress(IOError):
            with open(f"rules/{args.source}/{key}.csv", encoding="utf-8") as rulecsv:
                rulebook[key] = {}
                for row in csv.reader(rulecsv, delimiter="\t"):
                    if row and not row[0].startswith("#"):
                        rulebook[key][row[0]] = [row[1], 0]

    enhancebook: Dict[str, dict] = {}
    enhanced = set()
    for key in keys:
        with suppress(OSError):
            enhancepath = f"enhance/{args.source}/{key}"
            if os.path.isdir(enhancepath):
                enhancebook[key] = {}
                for filename in os.listdir(enhancepath):
                    with open(os.path.join(enhancepath, filename), encoding="utf-8") as enhancecsv:
                        target = filename[:-4]
                        if target not in keys:
                            keys.append(target)
                        enhanced.add(target)
                        enhancebook[key][target] = {}
                        for erow in csv.reader(enhancecsv, delimiter="\t"):
                            if erow and not erow[0].startswith("#"):
                                enhancebook[key][target][erow[0]] = [erow[1], 0]
                log.debug("Enhance book for %s: %s", key, ", ".join(enhancebook[key].keys()))

    filterbook: Dict[str, dict] = {}
    for key in keys:
        with suppress(IOError):
            with open(f"filters/{args.source}/{key}.csv", encoding="utf-8") as filtercsv:
                filterbook[key] = {}
                for row in csv.reader(filtercsv, delimiter="\t"):
                    if row and not row[0].startswith("#"):
                        filterbook[key][row[0]] = 0
            log.debug("Filter book for %s is %i entries big.", key, len(filterbook[key]))

    filtered = 0
    len_data = df.height
    for key, filters in filterbook.items():
        mask = ~pl.col(key).is_in(list(filters.keys()))
        counts = df.filter(~mask).group_by(key).len()
        for row in counts.rows():
            filters[row[0]] = row[1]
        filtered += df.height - df.filter(mask).height
        df = df.filter(mask)

    substitutions = 0
    for key, mapping in rulebook.items():
        if not mapping:
            continue
        replace_map = {k: v[0] for k, v in mapping.items()}
        counts = df.filter(pl.col(key).is_in(list(replace_map.keys()))).group_by(key).len()
        for row in counts.rows():
            mapping[row[0]][1] = row[1]
            substitutions += row[1]
        df = df.with_columns(pl.col(key).replace(replace_map).alias(key))

    for key, targets in enhancebook.items():
        for target, mapping in targets.items():
            replace_map = {k: v[0] for k, v in mapping.items()}
            counts = df.filter(pl.col(key).is_in(list(replace_map.keys()))).group_by(key).len()
            for row in counts.rows():
                mapping[row[0]][1] = row[1]
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
        for rule, (replacement, count) in rulebook[key].items():
            if count == 0:
                log.info('Did not use [{}] rule "{}" -> "{}"'.format(key, rule, replacement))
            else:
                log.debug("Used [{}] rule {} {} times".format(key, rule, count))

    for key, targets in enhancebook.items():
        for enhancement, mapping in targets.items():
            for tkey, (value, count) in mapping.items():
                if count == 0:
                    log.info('Did not use enhancement [{}] "{}" -> [{}] "{}"'.format(key, tkey, enhancement, value))

    for key, filters in filterbook.items():
        for value, count in filters.items():
            if count == 0:
                log.info("Did not use filter [{}] {}".format(key, value))


if __name__ == "__main__":
    main()
