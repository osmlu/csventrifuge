#!/usr/bin/env python

# TODO use a generator instead of loading everything in ram
# TODO count how many times a rule is used, and show unused rules
# DONE deal with rules that apply only in one city, e.g. Rue Churchill
#  which becomes Bd Churchill in Esch only - use an enhancement

import argparse
import csv
import importlib
import logging
import os
import re
from contextlib import suppress
from typing import Dict

logging.basicConfig(level=logging.WARNING)
log = logging.getLogger(__name__)


def load_module(wanted_module, origin):
    pysearchre = re.compile(".py$", re.IGNORECASE)
    modulefiles = filter(
        pysearchre.search, os.listdir(os.path.join(os.path.dirname(__file__), origin))
    )
    modules = map(form_module, modulefiles)
    # import parent module / namespace
    importlib.import_module(origin)
    for module in modules:
        if module == "." + wanted_module:
            log.debug("Loading module %s", module)
            return importlib.import_module(module, package="sources")
    # If we reach this point, we haven't found anything
    raise ImportError('module not found "{}" ({})'.format(wanted_module, origin))


def form_module(fp):
    return "." + os.path.splitext(fp)[0]


def is_valid_source(parser, arg):
    if not os.path.exists("sources/" + arg + ".py"):
        parser.error(
            "The input source definition sources/{}.py does not exist".format(arg)
        )
        return False
    return arg


def is_valid_output(parser, arg):
    try:
        output = open(arg, "w", encoding="utf-8", newline="")
    except OSError:
        parser.error("Unable to write to file {}".format(arg))
    else:
        return output


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
args = parser.parse_args()


source = load_module(args.source, "sources")

get_data = getattr(source, "get", None)

if get_data is None:
    raise ImportError('function not found "{}" ({})'.format("get", args.source))

# Load it all up in memory
data, keys = get_data()

log.debug("Keys are %s", ", ".join(keys))

# Build the rulebook
rulebook: Dict[str, dict] = {}
for key in keys:
    # Throw the rules in a dict, e.g. rules['localite'] - according to
    # key->filename
    # Ignore IOError, means no rules for this column
    with suppress(IOError):
        with open(
            "rules/" + args.source + "/" + key + ".csv", encoding="utf-8"
        ) as rulecsv:
            rulebook[key] = {}
            for row in csv.reader(rulecsv, delimiter="\t"):
                try:
                    if not row[0].startswith("#"):
                        rulebook[key][row[0]] = [row[1], 0]
                except IndexError:
                    log.error("Could not import rule: %s", row)

# Build the enhancement book
enhancebook: Dict[str, dict] = {}
enhanced = set()
for key in keys:
    # Ignore OSError, means no enhancements for this column
    with suppress(OSError):
        enhancepath = "enhance/" + args.source + "/" + key
        enhancements = os.listdir(enhancepath)
        if enhancements:
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
                    enhanced.add(target)
                    enhancebook[key][target] = {}
                    log.debug("Adding enhance target " + target + " key " + key)
                    for erow in csv.reader(enhancecsv, delimiter="\t"):
                        try:
                            if not erow[0].startswith("#"):
                                enhancebook[key][target][erow[0]] = [erow[1], 0]
                        except IndexError:
                            log.error("erow: %s", str(erow))
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
        try:
            orig = row[key]
            row[key] = rulebook[key][row[key]][0]
            log.debug("Rule: replacing [%s] %s with %s", key, orig, row[key])
            rulebook[key][orig][1] += 1
            substitutions += 1
        except KeyError:
            log.debug("No rule for [%s] %s", key, orig)

        # apply enhancement
        try:
            for enhancement in enhancebook[key].keys():
                # Ignore when no enhancement
                with suppress(KeyError):
                    orig = row[enhancement]
                    row[enhancement] = enhancebook[key][enhancement][row[key]][0]
                    enhancebook[key][enhancement][row[key]][1] += 1
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
