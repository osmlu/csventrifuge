#!/bin/bash
source venv/bin/activate
echo "Addresses..."
./csventrifuge.py luxembourg_addresses luxembourg-addresses.csv
echo "Streets..."
./csventrifuge.py luxembourg-caclr-dicacolo luxembourg-streets.csv
echo "Importing addresses into postgres..."
psql -d gis -f ../addresses/import_addresses.sql
echo "Copying to openstreetmap.lu..."
scp luxembourg-addresses.csv luxembourg-streets.csv root@stereo.lu:/home/openstreetmap/www/
