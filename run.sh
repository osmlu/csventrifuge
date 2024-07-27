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
#echo addr:street,addr:housenumber,addr:city,addr:postcode,ref:caclr,lat_wgs84,lon_wgs84,commune > "$(date +%Y-%m-%d)-addresses.csv"
#cut -d , -f 3-6,8-10 luxembourg-addresses.csv | tail -n +2 >> "$(date +%Y-%m-%d)-addresses.csv"
# Add the new column header in the desired order
echo addr:housenumber,addr:street,addr:place,addr:postcode,addr:city,commune,lat_wgs84,lon_wgs84,ref:caclr > "$(date +%Y-%m-%d)-addresses.csv"

# Process the input file and add the new column with the specified conditions
tail -n +2 luxembourg-addresses.csv | while IFS=, read -r rue_orig code_commune rue numero localite code_postal id_caclr_rue id_caclr_bat lat_wgs84 lon_wgs84 coord_est_luref coord_nord_luref id_geoportail commune lau2; do
    addr_street="$rue"
    addr_housenumber="$numero"
    addr_city="$localite"
    addr_postcode="$code_postal"
    ref_caclr="$id_caclr_bat"
    
    if [ "$addr_street" == "Maison" ]; then
        addr_street=""
        addr_place="$addr_city"
    else
        addr_place=""
    fi
    echo "$addr_housenumber,$addr_street,$addr_place,$addr_postcode,$addr_city,$commune,$lat_wgs84,$lon_wgs84,$ref_caclr" >> "$(date +%Y-%m-%d)-addresses.csv"
done
cp $(date +%Y-%m-%d)-addresses.csv  ../public_html/csventrifuge/$(date +%Y-%m-%d)-addresses-josm.csv
cd ../public_html/csventrifuge
rm latest-addresses.csv luxembourg-addresses.geojson
ln -s "$(date +%Y-%m-%d)-addresses-josm.csv" latest-addresses.csv
ogr2ogr -f geojson luxembourg-addresses.geojson luxembourg-addresses.vrt
echo "Conversion complete."
