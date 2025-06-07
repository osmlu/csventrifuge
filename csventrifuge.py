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

# Parse arguments
args = parser.parse_args()

# Load the specified module
source = load_module(args.source, "sources")

# Get the "get" function from the source module
get_data = getattr(source, "get", None)

# If the "get" function does not exist, raise an ImportError
if get_data is None:
    raise ImportError('function not found "{}" ({})'.format("get", args.source))

# Get the data and keys from the "get" function. Load it all up in memory.
data, keys = get_data()

# Print debug message with keys
log.debug("Keys are %s", ", ".join(keys))

# Build the rulebook
rulebook: Dict[str, dict] = {}
# Iterate through keys
for key in keys:
    # Throw the rules in a dict, e.g. rules['localite'] - according to
    # key->filename
    # Ignore IOError, means no rules for this column
    with suppress(IOError):
        with open(
            f"rules/{args.source}/{key}.csv", encoding="utf-8"
        ) as rulecsv:
            # Initialize empty dictionary for the current key in rulebook
            rulebook[key] = {}
            # Iterate through rows in the rules file
            for row in csv.reader(rulecsv, delimiter="\t"):
                try:
                    # If the row does not start with "#", add it to the rulebook
                    if not row[0].startswith("#"):
                        rulebook[key][row[0]] = [row[1], 0]
                # If an IndexError occurs, print an error message
                except IndexError:
                    log.error(f"Could not import rule: {row}")

# Build the enhancement book
# Initialize empty enhancement book dictionary
enhancebook: Dict[str, dict] = {}
# Initialize empty set of enhanced columns
enhanced = set()
for key in keys:
    # Ignore OSError, means no enhancements for this column
    with suppress(OSError):
        # Get the path to the enhancements for the current key
        enhancepath = "enhance/" + args.source + "/" + key
        # Get a list of enhancement names for the current key
        enhancements = os.listdir(enhancepath)
        # If there are enhancements for the current key
        if enhancements:
            # Initialize empty dictionary for the current key in enhancebook
            enhancebook[key] = {}
            for filename in os.listdir(enhancepath):
                with open(
                    enhancepath + "/" + filename,
                    encoding="utf-8",
                ) as enhancecsv:
                    # Target is file name without .csv at end
                    target = filename[:-4]
                    if target not in keys:
                        keys.append(target)
                    # Add the target key to the set of enhanced columns
                    enhanced.add(target)
                    enhancebook[key][target] = {}
                    log.debug("Adding enhance target " + target + " key " + key)
                    # Add the current key to the set of enhanced columns
                    for erow in csv.reader(enhancecsv, delimiter="\t"):
                        try:
                            # If the row does not start with "#", add it to the enhancebook
                            if not erow[0].startswith("#"):
                                enhancebook[key][target][erow[0]] = [erow[1], 0]
                        # If an IndexError occurs, print an error message
                        except IndexError:
                            log.error(f"Could not import enhancement, erow is: {erow}")
            log.debug(
                "Enhance book for %s: %s", key, ", ".join(enhancebook[key].keys())
            )

# Build the filter book
filterbook: Dict[str, list] = {}
for key in keys:
    # Throw the rules in a dict, e.g. rules['localite'] - according to
    # key->filename
    # Ignore IOError, means no filter for this column
    with suppress(IOError):
        with open(
            "filters/" + args.source + "/" + key + ".csv", encoding="utf-8"
        ) as filtercsv:
            filterbook[key] = {}
            for row in csv.reader(filtercsv, delimiter="\t"):
                if not row[0].startswith("#"):
                    filterbook[key][row[0]] = 0
        log.debug("Filter book for %s is %i entries big.", key, len(filterbook[key]))

# For each row, for each column, if there's a corresponding rule, replace.
# if rules['localite'][address['localite']:
#     address['localite'] = rules['localite'][address['localite']
# If there's an enhancement, add that column in the same way.
# Is there a more pythonic way to write this? Lambda function? Dict
# comprehension?

substitutions = 0
filtered = 0
len_data = len(data)

# apply filters using list comprehension (wheee)
for key in filterbook:
    # We don't replace in place because we want a count
    filtered_data = [row for row in data if row[key] not in filterbook[key].keys()]
    for deleted in [row for row in data if row[key] in filterbook[key].keys()]:
        # print(deleted)
        filterbook[key][deleted[key]] += 1
        # log.debug("Filter deleted %s", deleted)
    filtered += len(data) - len(filtered_data)
    data = filtered_data

for row in data:
    for key in keys:

        # apply rules
        orig = row.get(key)
        try:
            if orig is not None:
                row[key] = rulebook[key][orig][0]
                log.debug("Rule: replacing [%s] %s with %s", key, orig, row[key])
                rulebook[key][orig][1] += 1
                substitutions += 1
            else:
                raise KeyError
        except KeyError:
            log.debug("No rule for [%s] %s", key, orig)

        # apply enhancement
        try:
            for enhancement in enhancebook[key]:
                try:
                    row[enhancement] = enhancebook[key][enhancement][row[key]][0]
                    enhancebook[key][enhancement][row[key]][1] += 1
                except KeyError:
                    # No enhancement found for this value
                    pass
        except KeyError:
            log.debug("No enhancements for [%s]", key)
    # Check if all enhanced columns in the row got added
    for enhanced_column in enhanced:
        if enhanced_column not in row:
            log.error("No enhancement found for %s in row %s", enhanced_column, row)


# After substitutions and additions done, spit out new csv.

csv_out = args.output
# extrasaction='ignore' ignores extra fields
# http://www.lucainvernizzi.net/blog/2015/08/03/8x-speed-up-for-python-s-csv-dictwriter/
writer = csv.DictWriter(csv_out, fieldnames=keys, extrasaction="ignore")

writer.writeheader()
writer.writerows(data)
log.info(
    "{} values out of {} dropped, {:.2%}".format(
        filtered, len_data, filtered / len_data
    )
)
log.info(
    "{} values out of {} replaced, {:.2%}".format(
        substitutions, len(data), substitutions / len(data)
    )
)

for key in rulebook:
    for rule in rulebook[key]:
        if rulebook[key][rule][1] == 0:
            log.info(
                'Did not use [{}] rule "{}" -> "{}"'.format(
                    key, rule, rulebook[key][rule][0]
                )
            )
        else:
            log.debug(
                "Used [{}] rule {} {} times".format(key, rule, rulebook[key][rule][1])
            )

for key in enhancebook:
    for enhancement in enhancebook[key].keys():
        for tkey in enhancebook[key][enhancement]:
            if enhancebook[key][enhancement][tkey][1] == 0:
                log.info(
                    'Did not use enhancement [{}] "{}" -> [{}] "{}"'.format(
                        key, tkey, enhancement, enhancebook[key][enhancement][tkey][0]
                    )
                )

for key in filterbook:
    for filter in filterbook[key].keys():
        if filterbook[key][filter] == 0:
            log.info("Did not use filter [{}] {}".format(key, filter))
