-- rue,numero,localite,code_postal,id_caclr_rue,id_caclr_bat,lat_wgs84,lon_wgs84,coord_est_luref,coord_nord_luref,id_geoportail,commune,commune
DROP TABLE IF EXISTS addresses;
drop table if exists addresses_staging;
CREATE Table addresses_staging (
    rue VARCHAR(64),
    numero VARCHAR(256), -- too high?
    localite VARCHAR(64),
    code_postal NUMERIC(4),
    id_caclr_rue NUMERIC(5),
    id_caclr_bat VARCHAR(512), -- too high?
    lat_wgs84 double precision,
    lon_wgs84 double precision,
    coord_est_luref double precision,
    coord_nord_luref double precision,
    id_geoportail varchar(32),
    commune VARCHAR(32)
);

create table addresses (like addresses_staging);

\copy addresses_staging from '/Users/you/osm/csventrifuge/luxembourg-addresses.csv' WITH CSV HEADER DELIMITER AS ','

insert into addresses
  SELECT rue,
         string_agg(numero, ',' order by numero) AS numero,
         localite,
         code_postal,
         id_caclr_rue,
         string_agg(id_caclr_bat, ';' order by id_caclr_bat) AS id_caclr_bat,
         lat_wgs84,
         lon_wgs84,
         coord_est_luref,
         coord_nord_luref,
         id_geoportail,
         commune
  FROM addresses_staging
  WHERE numero IS NOT NULL
  GROUP BY rue,
           localite,
           code_postal,
           id_caclr_rue,
           lat_wgs84,
           lon_wgs84,
           coord_est_luref,
           coord_nord_luref,
           id_geoportail,
           commune;


SELECT AddGeometryColumn('addresses', 'geom', 4326, 'POINT', 2);

UPDATE addresses SET geom = ST_GeomFromText('POINT(' || lon_wgs84 || ' ' || lat_wgs84 || ')',4326);

ALTER TABLE addresses ADD matches VARCHAR(32);

CREATE INDEX idx_addresses_geom ON addresses USING gist(geom);
