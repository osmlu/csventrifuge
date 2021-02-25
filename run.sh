#!/bin/bash
# TODO https://stackoverflow.com/questions/41696675/how-to-copy-a-csv-file-from-a-url-to-postgresql
source venv/bin/activate
echo "Addresses..."
./csventrifuge.py luxembourg_addresses luxembourg-addresses.csv
echo "Streets..."
./csventrifuge.py luxembourg-caclr-dicacolo luxembourg-streets.csv
if command -v psql &> /dev/null
then
    # TODO https://stackoverflow.com/questions/41696675/how-to-copy-a-csv-file-from-a-url-to-postgresql
    echo "Importing addresses into postgres..."
    psql -d gis -f ../addresses/import_addresses.sql
    psql -d gis -f ../import_cadastre.sql
fi
echo "Converting for JOSM"
echo addr:street,addr:housenumber,addr:city,addr:postcode,ref:caclr,lat_wgs84,lon_wgs84,commune > "$(date +%Y-%m-%d)-addresses.csv"
cut -d , -f 2-5,7-9 luxembourg-addresses.csv | tail -n +2 >> "$(date +%Y-%m-%d)-addresses.csv"
rm latest-addresses.csv
ln -s "$(date +%Y-%m-%d)-addresses.csv" latest-addresses.csv
echo "Done! To open, copy-paste:"
echo "open -a JOSM.app $(date +%Y-%m-%d)-addresses.csv"
