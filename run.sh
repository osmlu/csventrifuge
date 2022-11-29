#!/bin/bash
# TODO https://stackoverflow.com/questions/41696675/how-to-copy-a-csv-file-from-a-url-to-postgresql
#source venv/bin/activate
echo "Addresses..."
python3 csventrifuge.py luxembourg_addresses luxembourg-addresses.csv
echo "Streets..."
python3 ./csventrifuge.py luxembourg-caclr-dicacolo_local luxembourg-streets.csv
echo "CACLR..."
python3 ./csventrifuge.py luxembourg-caclr-commuall_local luxembourg-communes.csv
if command -v psql &> /dev/null
then
    # TODO https://stackoverflow.com/questions/41696675/how-to-copy-a-csv-file-from-a-url-to-postgresql
    echo "Importing addresses into postgres..."
    psql -d osmlu -f ../import_addresses.sql
    psql -d osmlu -f ../import_cadastre.sql
fi
cp luxembourg-addresses.csv ../public_html/csventrifuge/.
cp luxembourg-streets.csv ../public_html/csventrifuge/.
echo "Converting for JOSM"
echo addr:street,addr:housenumber,addr:city,addr:postcode,ref:caclr,lat_wgs84,lon_wgs84,commune > "$(date +%Y-%m-%d)-addresses.csv"
cut -d , -f 3-6,8-10 luxembourg-addresses.csv | tail -n +2 >> "$(date +%Y-%m-%d)-addresses.csv"
cp $(date +%Y-%m-%d)-addresses.csv  ../public_html/csventrifuge/$(date +%Y-%m-%d)-addresses-josm.csv
cd ../public_html/csventrifuge
rm latest-addresses.csv
ln -s "$(date +%Y-%m-%d)-addresses-josm.csv" latest-addresses.csv
ogr2ogr -f geojson luxembourg-addresses.geojson luxembourg-addresses.vrt
