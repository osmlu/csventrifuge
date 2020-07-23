csventrifuge
=====

A flexible csv filter/rewriter, built for Luxembourg's addresses and street lists, but should be adaptable for others.

### Folder Description

* sources -> obtain the values from anywhere you want
* rules -> modify values
* enhance -> add values, or replace based on another key
* filter -> drop values

### How to use

* Execute the utility to produce the required .csv files. See `run.sh` for an example of how to do this.
* Open `luxembourg-addresses.csv` in [JOSM](https://josm.openstreetmap.de/), right-click the layer, select `Save As...` and save it as `csventrifuge-out.osm`. Make sure to install the [OpenData](https://wiki.openstreetmap.org/wiki/JOSM/Plugins/OpenData) plugin in JOSM first.
* Run the following command:

``` shell
grep -vE "(luref|id_caclr_rue|commune|id_geoportail)" csventrifuge-out.osm | sed -e "s/localite/addr:city/; s/id_caclr_bat/ref:caclr/; s/'rue/'addr:street/; s/numero/addr:housenumber/; s/code_postal/addr:postcode/; s/action='modify' //;" >| $(date +%Y-%m-%d)-addresses.osm
```
* That's it! You can now open `2018-09-10-addresses.osm` in JOSM.

Another way of doing it if you don't need action=modify:

``` shell
echo addr:street,addr:housenumber,addr:city,addr:postcode,ref:caclr,lat_wgs84,lon_wgs84,commune > $(date +%Y-%m-%d)-addresses.csv
cut -d , -f 2-5,7-9 luxembourg-addresses.csv | tail -n +2 >> $(date +%Y-%m-%d)-addresses.csv
open -a JOSM.app $(date +%Y-%m-%d)-addresses.csv
```

### Notes

Unfortunately https://github.com/pnorman/ogr2osm has https://github.com/pnorman/ogr2osm/issues/31. Pnorman recommends pre-processing in postgis.
