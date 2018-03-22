-- Import all the dataFROM CACLR into pgsql.
-- Corrections can be made with things like
-- UPDATE road_names_cad set commune = 'Pétange' WHERE commune = 'Petange';
-- UPDATE road_names_cad set code_postal = NULL WHERE code_postal = '';

-- TODO: Use nullif to have null instead of '' where applicable.
-- TODO: Should be allowed to be null: code_multiple, langue

set client_encoding = 'latin1';

CREATE TEMPORARY TABLE caclr_staging(data text);
\COPY caclr_staging FROM 'caclr-export/ALIAS.LOCALITE' -- symlink to the real file

INSERT INTO ALIAS_LOCALITE(NUMERO_SEQUENTIEL, NOM, NOM_MAJUSCULE, LANGUE, DS_TIMESTAMP_MODIF, FK_LOCAL_NUMERO) SELECT
  substring(data, 1,   3)::integer AS NUMERO_SEQUENTIEL,
  trim(substring(data, 4,  40)) AS NOM,
  trim(substring(data, 44, 40)) AS NOM_MAJUSCULE,
  nullif(substring(data, 84,  1), '') AS LANGUE,
  substring(data, 85,  10)::date  AS DS_TIMESTAMP_MODIF,
  substring(data, 95,  5)::integer AS FK_LOCAL_NUMERO
FROM caclr_staging;

TRUNCATE caclr_staging;
\COPY caclr_staging FROM 'caclr-export/ALIAS.RUE' -- symlink to the real file

INSERT INTO ALIAS_RUE(NUMERO_SEQUENTIEL, NOM, NOM_MAJUSCULE, LANGUE, DS_TIMESTAMP_MODIF, FK_RUE_NUMERO, DESCRIPTION) SELECT
  substring(data, 1,   3)::integer AS NUMERO_SEQUENTIEL,
  trim(substring(data, 4,  40)) AS NOM,
  trim(substring(data, 44, 40)) AS NOM_MAJUSCULE,
  substring(data, 84,  1) AS LANGUE,
  substring(data, 85,  10)::date  AS DS_TIMESTAMP_MODIF,
  substring(data, 95,  5)::integer AS FK_LOCAL_NUMERO,
  nullif(trim(substring(data, 100,  80)), '') AS DESCRIPTION
FROM caclr_staging;

TRUNCATE caclr_staging;
\COPY caclr_staging FROM 'caclr-export/CANTON' -- symlink to the real file

INSERT INTO CANTON(CODE, NOM, DS_TIMESTAMP_MODIF, FK_DISTR_CODE) SELECT
  substring(data, 1,   2)::integer AS CODE,
  trim(substring(data, 3,  40)) AS NOM,
  substring(data, 43,  10)::date  AS DS_TIMESTAMP_MODIF,
  trim(substring(data, 53,  4)) AS FK_DISTR_CODE
FROM caclr_staging;

TRUNCATE caclr_staging;
\COPY caclr_staging FROM 'caclr-export/CODEPT' -- symlink to the real file

INSERT INTO CODE_POSTAL(NUMERO_POSTAL, LIB_POST_MAJUSCULE, TYPE_CP, LIMITE_INF_BP, LIMITE_SUP_BP, DS_TIMESTAMP_MODIF) SELECT
  substring(data, 1,   4)::integer AS NUMERO_POSTAL,
  trim(substring(data, 5,  40)) AS LIB_POST_MAJUSCULE,
  trim(substring(data, 45,  1)) AS TYPE_CP,
  substring(data, 46,   4)::integer as LIMITE_INF_BP,
  substring(data, 50,   4)::integer as LIMITE_SUP_BP,
  substring(data, 54,  10)::date  AS DS_TIMESTAMP_MODIF
FROM caclr_staging;

TRUNCATE caclr_staging;
\COPY caclr_staging FROM 'caclr-export/CPTCH' -- symlink to the real file

INSERT INTO CODE_PTS_CHSSEES(TYPE_RUE, NUMERO_RUE, DS_TIMESTAMP_MODIF) SELECT
  trim(substring(data, 1,  2)) AS TYPE_RUE,
  trim(substring(data, 3,  4)) AS NUMERO_RUE,
  substring(data, 7,  10)::date  AS DS_TIMESTAMP_MODIF
FROM caclr_staging;

TRUNCATE caclr_staging;
\COPY caclr_staging FROM 'caclr-export/COMMUNE' -- symlink to the real file

INSERT INTO COMMUNE(CODE, NOM, NOM_MAJUSCULE, DS_TIMESTAMP_MODIF, FK_CANTO_CODE) SELECT
  substring(data, 1,   2)::integer AS CODE,
  trim(substring(data, 3,  40)) AS NOM,
  trim(substring(data, 43, 40)) AS NOM_MAJUSCULE,
  substring(data, 83,  10)::date  AS DS_TIMESTAMP_MODIF,
  substring(data, 93,  2)::integer AS FK_CANTO_CODE
FROM caclr_staging;

TRUNCATE caclr_staging;
\COPY caclr_staging FROM 'caclr-export/DISTRICT' -- symlink to the real file

INSERT INTO DISTRICT_ADMIN(CODE, NOM, DS_TIMESTAMP_MODIF) SELECT
  trim(substring(data, 1,   4)) AS CODE,
  trim(substring(data, 5,  40)) AS NOM,
  substring(data, 45,  10)::date  AS DS_TIMESTAMP_MODIF
FROM caclr_staging;

TRUNCATE caclr_staging;
\COPY caclr_staging FROM 'caclr-export/IMMEUBLE' -- symlink to the real file

INSERT INTO IMMEUBLE(NUMERO_INTERNE, NUMERO, CODE_MULTIPLE, DATE_FIN_VALID, DS_TIMESTAMP_MODIF, FK_CODPT_NUMERO, FK_QUART_NUMERO, FK_RUE_NUMERO, INDIC_NO_INDEF, INDIC_PROVISOIRE) SELECT
  substring(data, 1,   8)::integer AS NUMERO_INTERNE,
  substring(data, 9,   3)::integer AS NUMERO,
  trim(substring(data, 12,  6)) AS CODE_MULTIPLE,
  nullif(substring(data, 18,  10), '          ')::date  AS DATE_FIN_VALID,
  substring(data, 29,  10)::date  AS DS_TIMESTAMP_MODIF,
  nullif(substring(data, 39,  4), '    ')::integer AS FK_CODPT_NUMERO,
  nullif(substring(data, 44,  5), '     ')::integer AS FK_QUART_NUMERO,
  nullif(substring(data, 50,  5), '     ')::integer AS FK_RUE_NUMERO,
  substring(data, 56,  1) AS INDIC_NO_INDEF,
  substring(data, 57,  1) AS INDIC_PROVISOIRE
  -- trim(substring(data, 55,  40)) AS DESIGNATION -- not present in this file; update table with IMMDESIG afterwards
FROM caclr_staging;

TRUNCATE caclr_staging;
\COPY caclr_staging FROM 'caclr-export/IMMDESIG' -- symlink to the real file


UPDATE IMMEUBLE
SET DESIGNATION = newdata.DESIGNATION
 FROM (
   SELECT
   substring(data, 1,   8)::integer AS NUMERO_INTERNE,
   trim(substring(data, 57,  40)) AS DESIGNATION
   FROM caclr_staging
 ) newdata
WHERE IMMEUBLE.NUMERO_INTERNE = newdata.NUMERO_INTERNE;


TRUNCATE caclr_staging;
\COPY caclr_staging FROM 'caclr-export/LOCALITE' -- symlink to the real file

INSERT INTO LOCALITE(NUMERO, NOM, NOM_MAJUSCULE, CODE, INDIC_VILLE, DATE_FIN_VALID, DS_TIMESTAMP_MODIF, FK_CANTO_CODE, FK_COMMU_CODE) SELECT
  substring(data, 1,   5)::integer AS NUMERO,
  trim(substring(data, 6,  40)) AS NOM,
  trim(substring(data, 46,  40)) AS NOM_MAJUSCULE,
  substring(data, 86,   2)::integer AS CODE,
  trim(substring(data, 88,  1)) AS INDIC_VILLE,
  nullif(substring(data, 89,  10), '          ')::date  AS DATE_FIN_VALID,
  substring(data, 100,  10)::date  AS DS_TIMESTAMP_MODIF,
  substring(data, 110,   2)::integer AS FK_CANTO_CODE,
  substring(data, 113,   2)::integer AS FK_COMMU_CODE
FROM caclr_staging;


TRUNCATE caclr_staging;
\COPY caclr_staging FROM 'caclr-export/QUARTIER' -- symlink to the real file

INSERT INTO QUARTIER(NUMERO, NOM, DS_TIMESTAMP_MODIF, FK_LOCAL_NUMERO) SELECT
  substring(data, 1,   5)::integer AS NUMERO,
  trim(substring(data, 6,  40)) AS NOM,
  substring(data, 46,  10)::date  AS DS_TIMESTAMP_MODIF,
  nullif(substring(data, 56,  5), '    ')::integer AS FK_LOCAL_NUMERO
FROM caclr_staging;

TRUNCATE caclr_staging;
\COPY caclr_staging FROM 'caclr-export/RUE' -- symlink to the real file

INSERT INTO RUE(NUMERO, NOM, NOM_MAJUSCULE, MOT_TRI, CODE_NOMENCLATURE, INDIC_LIEU_DIT, DATE_FIN_VALID, DS_TIMESTAMP_MODIF, FK_CPTCH_TYPERUE, FK_CPTCH_NUMERORUE, FK_LOCAL_NUMERO, INDIC_PROVISOIRE, NOM_ABREGE) SELECT
  substring(data, 1,   5)::integer AS NUMERO,
  trim(substring(data,6,40)) AS NOM,
  trim(substring(data, 46,  40)) AS NOM_MAJUSCULE,
  trim(substring(data, 86,  10)) AS MOT_TRI,
  nullif(substring(data, 96,  5), '     ')::integer AS CODE_NOMENCLATURE,
  trim(substring(data, 102,  1)) AS INDIC_LIEU_DIT,
  nullif(substring(data, 103,  10), '          ')::date  AS DATE_FIN_VALID,
  substring(data, 114,  10)::date  AS DS_TIMESTAMP_MODIF,
  nullif(substring(data, 124,  2), '  ') AS FK_CPTCH_TYPERUE,
  nullif(substring(data, 127,  2), '  ') AS FK_CPTCH_NUMERORUE,
  nullif(substring(data, 132,  5), '     ')::integer AS FK_LOCAL_NUMERO,
  nullif(substring(data, 138,  1), ' ') AS INDIC_PROVISOIRE,
  trim(substring(data, 139,  30)) AS NOM_ABREGE
FROM caclr_staging;

TRUNCATE caclr_staging;
\COPY caclr_staging FROM 'caclr-export/TR.RUE.CODEPT' -- symlink to the real file

-- TODO ↓
-- INSERT INTO R_RUE_CODEPT()

-- Corrections

set client_encoding = 'UTF8';

UPDATE QUARTIER set nom = 'Mühlenbach' WHERE nom = 'Muhlenbach';

reset client_encoding;
