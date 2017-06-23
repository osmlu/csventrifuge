csventrifuge
=====

A flexible csv filter/rewriter, built for Luxembourg's addresses and street lists, but should be adaptable for others.

sources -> obtain the values from anywhere you want
rules -> modify values
enhance -> add values
filter -> drop values

See `run.sh` for an example of how to use this.

To convert addresses csv to osm, open it with josm and save to csventrifuge-out.osm. Then run

    grep -vE (luref|id_caclr_rue|commune) csventrifuge-out.osm | sed -e "s/localite/addr:city/; s/id_caclr_bat/ref:caclr/; s/'rue/'addr:street/; s/numero/addr:housenumber/; s/code_postal/addr:postcode/; s/action='modify' //;" >| 2016-09-26-addresses.osm

Unfortunately https://github.com/pnorman/ogr2osm has https://github.com/pnorman/ogr2osm/issues/31. Pnorman recommends pre-processing in postgis.
