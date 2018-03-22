#!/bin/sh

dropdb caclr || exit 1

cd $(dirname $0) || exit 2

createdb -E UTF8 caclr

# Create db structure
psql -d caclr -f postgresql.sql

# Fill her up!
psql -d caclr -f import_caclr.sql