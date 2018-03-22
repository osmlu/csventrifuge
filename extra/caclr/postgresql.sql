/*
Adapté avec gratitude à partir de la structure pour Oracle de Paul Mootz,
Administration du Cadastre et de la Topographie.

NB: les extraits CACLR officiels trient les rues bas de casse avant capitales
(Rue _d_e l'Eglise avant Rue _B_elair). Postgresql utilise l'ordre ascii (Rue
Zénon Bernard avant Rue de l'Atert). On pourrait utiliser RUE.MOT_TRI ;
l'exercice est laissé au lecteur.

Guillaume Rischard 2013-07-19
*/


set client_encoding = 'latin1';
set client_min_messages='warning';

DROP TABLE IF EXISTS ALIAS_LOCALITE  ;
CREATE TABLE  ALIAS_LOCALITE
    (NUMERO_SEQUENTIEL                  NUMERIC(3)           NOT NULL,
     NOM                                VARCHAR(40)          NOT NULL,
     NOM_MAJUSCULE                      VARCHAR(40)          NOT NULL,
     LANGUE                             CHAR(1)
       CHECK (LANGUE IN (Null, 'A', 'F', 'L')),
     DS_TIMESTAMP_MODIF                 DATE                 NOT NULL,
     FK_LOCAL_NUMERO                    NUMERIC(5)           NOT NULL,
    CONSTRAINT IALLOC01
    PRIMARY KEY
      (FK_LOCAL_NUMERO                    ,
       NUMERO_SEQUENTIEL                  )
      );

DROP TABLE IF EXISTS ALIAS_RUE  ;
CREATE TABLE  ALIAS_RUE
    (NUMERO_SEQUENTIEL                  NUMERIC(3)           NOT NULL,
     NOM                                VARCHAR(40)          NOT NULL,
     NOM_MAJUSCULE                      VARCHAR(40)          NOT NULL,
     LANGUE                             CHAR(1)
       CHECK (LANGUE IN (Null, 'A', 'F', 'L')),
     DS_TIMESTAMP_MODIF                 DATE                 NOT NULL,
     FK_RUE_NUMERO                      NUMERIC(5)           NOT NULL,
     DESCRIPTION                        VARCHAR(80)          ,
    CONSTRAINT IALRUE01
    PRIMARY KEY
      (FK_RUE_NUMERO                      ,
       NUMERO_SEQUENTIEL                  )
      );

DROP TABLE IF EXISTS CANTON  ;
CREATE TABLE  CANTON
    (CODE                               NUMERIC(2)           NOT NULL,
     NOM                                VARCHAR(40)          NOT NULL,
     DS_TIMESTAMP_MODIF                 DATE                 NOT NULL,
     FK_DISTR_CODE                      CHAR(4)              ,
    CONSTRAINT ICANTO02
    PRIMARY KEY
      (CODE                               )
      );

DROP TABLE IF EXISTS CODE_POSTAL  ;
CREATE TABLE  CODE_POSTAL
    (NUMERO_POSTAL                      NUMERIC(4)           NOT NULL,
     LIB_POST_MAJUSCULE                 VARCHAR(40)          NOT NULL,
     TYPE_CP                            CHAR(1)              NOT NULL
       CHECK (TYPE_CP IN ('B', 'N', 'U')),
     LIMITE_INF_BP                      NUMERIC(4)           NOT NULL,
     LIMITE_SUP_BP                      NUMERIC(4)           NOT NULL,
     DS_TIMESTAMP_MODIF                 DATE                 NOT NULL,
    CONSTRAINT ICODPT01
    PRIMARY KEY
      (NUMERO_POSTAL                      )
      );

DROP TABLE IF EXISTS CODE_PTS_CHSSEES  ;
CREATE TABLE  CODE_PTS_CHSSEES
    (TYPE_RUE                           VARCHAR(2)           NOT NULL
       CHECK (TYPE_RUE IN ('N', 'CR')),
     NUMERO_RUE                         VARCHAR(4)           NOT NULL,
     DS_TIMESTAMP_MODIF                 DATE                 NOT NULL,
    CONSTRAINT ICPTCH01
    PRIMARY KEY
      (TYPE_RUE                           ,
       NUMERO_RUE                         )
      );

DROP TABLE IF EXISTS COMMUNE  ;
CREATE TABLE  COMMUNE
    (CODE                               NUMERIC(2)           NOT NULL,
     NOM                                VARCHAR(40)          NOT NULL,
     NOM_MAJUSCULE                      VARCHAR(40)          NOT NULL,
     DS_TIMESTAMP_MODIF                 DATE                 NOT NULL,
     FK_CANTO_CODE                      NUMERIC(2)           NOT NULL,
    CONSTRAINT ICOMMU01
    PRIMARY KEY
      (FK_CANTO_CODE                      ,
       CODE                               )
      );

DROP TABLE IF EXISTS DISTRICT_ADMIN  ;
CREATE TABLE  DISTRICT_ADMIN
    (CODE                               CHAR(4)              NOT NULL,
     NOM                                VARCHAR(40)          NOT NULL,
     DS_TIMESTAMP_MODIF                 DATE                 NOT NULL,
    CONSTRAINT IDISTR01
    PRIMARY KEY
      (CODE                               )
      );

DROP TABLE IF EXISTS IMMEUBLE  ;
CREATE TABLE  IMMEUBLE
    (NUMERO_INTERNE                     NUMERIC(8)           NOT NULL,
     NUMERO                             NUMERIC(3)           NOT NULL,
     CODE_MULTIPLE                      VARCHAR(6)           NOT NULL, -- "-.." is leftover from previous database structure where long CODE_MULTIPLE wouldn't fit in three characters, for numbers like 100-102. They should disappear soon.
     DATE_FIN_VALID                     DATE                 ,
     DS_TIMESTAMP_MODIF                 DATE                 NOT NULL,
     FK_CODPT_NUMERO                    NUMERIC(4)           ,
     FK_QUART_NUMERO                    NUMERIC(5)           ,
     FK_RUE_NUMERO                      NUMERIC(5)           NOT NULL,
     INDIC_NO_INDEF                     CHAR(1)              NOT NULL -- permet de définir si l'immeuble a un numéro ou pas. Les immeubles qui ne possèdent pas de numéro permettent d'attribuer un code postal à une rue. 
       CHECK (INDIC_NO_INDEF IN ('O', 'N')),
     INDIC_PROVISOIRE                   CHAR(1)              NOT NULL -- Immeuble provisoire (?)
       CHECK (INDIC_PROVISOIRE IN ('O', 'N')),
     DESIGNATION                        VARCHAR(40)          ,
    CONSTRAINT IIMMEU02
    PRIMARY KEY
      (NUMERO_INTERNE                     )
      );

DROP TABLE IF EXISTS LOCALITE  ;
CREATE TABLE  LOCALITE
    (NUMERO                             NUMERIC(5)           NOT NULL,
     NOM                                VARCHAR(40)          NOT NULL,
     NOM_MAJUSCULE                      VARCHAR(40)          NOT NULL,
     CODE                               NUMERIC(2)           NOT NULL,
     INDIC_VILLE                        VARCHAR(1)           NOT NULL
       CHECK (INDIC_VILLE IN ('O', 'N')),
     DATE_FIN_VALID                     DATE                 ,
     DS_TIMESTAMP_MODIF                 DATE                 NOT NULL,
     FK_CANTO_CODE                      NUMERIC(2)           NOT NULL,
     FK_COMMU_CODE                      NUMERIC(2)           NOT NULL,
    CONSTRAINT ILOCAL02
    PRIMARY KEY
      (NUMERO                             )
      );

DROP TABLE IF EXISTS QUARTIER  ;
CREATE TABLE  QUARTIER
    (NUMERO                             NUMERIC(5)           NOT NULL,
     NOM                                VARCHAR(40)          NOT NULL,
     DS_TIMESTAMP_MODIF                 DATE                 NOT NULL,
     FK_LOCAL_NUMERO                    NUMERIC(5)           ,
    CONSTRAINT IQUART02
    PRIMARY KEY
      (NUMERO                             )
      );

DROP TABLE IF EXISTS RUE  ;
CREATE TABLE  RUE
    (NUMERO                             NUMERIC(5)           NOT NULL,
     NOM                                VARCHAR(60)          NOT NULL, -- updated to 60 for long names GR
     NOM_MAJUSCULE                      VARCHAR(40)          NOT NULL,
     MOT_TRI                            VARCHAR(10)          NOT NULL,
     CODE_NOMENCLATURE                  NUMERIC(5)           ,
     INDIC_LIEU_DIT                     VARCHAR(1)           NOT NULL
       CHECK (INDIC_LIEU_DIT IN ('O', 'N')),
     DATE_FIN_VALID                     DATE                 ,
     DS_TIMESTAMP_MODIF                 DATE                 NOT NULL,
     FK_CPTCH_TYPERUE                   CHAR(2)
       CHECK (FK_CPTCH_TYPERUE IN ('N', 'CR')),
     FK_CPTCH_NUMERORUE                 VARCHAR(4)           ,
     FK_LOCAL_NUMERO                    NUMERIC(5)           NOT NULL,
     INDIC_PROVISOIRE                   CHAR(1)              NOT NULL
       CHECK (INDIC_PROVISOIRE IN ('N', 'O')),
     NOM_ABREGE                         VARCHAR(30)          NOT NULL,
    CONSTRAINT IRUE02
    PRIMARY KEY
      (NUMERO                             )
      );

-- DROP TABLE IF EXISTS R_RUE_CODEPT  ;
-- CREATE TABLE  R_RUE_CODEPT
--     (RUE_NUMERO                         NUMERIC(5)           ,
--      CODE_POSTAL                        VARCHAR(4)           ,
--     CONSTRAINT IRUEPT02
--     PRIMARY KEY
--       (RUE_NUMERO                         ,
--        CODE_POSTAL                        )
--       );

-----------
-- VIEWS --
-----------

CREATE OR REPLACE VIEW R_RUE_CODEPT AS
   SELECT RUE.NUMERO         AS RUE_NUMERO,
    IMMEUBLE.FK_CODPT_NUMERO AS CODE_POSTAL
   FROM IMMEUBLE
   
   JOIN RUE ON RUE.NUMERO = IMMEUBLE.FK_RUE_NUMERO
   GROUP BY RUE_NUMERO, CODE_POSTAL;

CREATE OR REPLACE VIEW R_LOCALITE_CODEPT AS
    SELECT
     commune.NOM              AS COMMUNE_NOM,
     localite.NOM             AS LOCALITE_NOM,
     immeuble.FK_CODPT_NUMERO AS CODE_POSTAL
    FROM IMMEUBLE
    JOIN RUE      ON IMMEUBLE.FK_RUE_NUMERO = RUE.NUMERO
    JOIN LOCALITE ON LOCALITE.NUMERO = RUE.FK_LOCAL_NUMERO
    JOIN COMMUNE  ON COMMUNE.CODE = LOCALITE.FK_COMMU_CODE AND COMMUNE.FK_CANTO_CODE = LOCALITE.FK_CANTO_CODE
    WHERE IMMEUBLE.INDIC_PROVISOIRE = 'N' -- La vue ne tient pas compte des immeubles provisoires.
    GROUP BY COMMUNE_NOM, LOCALITE_NOM, CODE_POSTAL
    ORDER BY COMMUNE_NOM, LOCALITE_NOM, CODE_POSTAL;

CREATE OR REPLACE VIEW R_CANTCOMM_LOCALITE AS
	SELECT
     CANTON.NOM               AS CANTON_NOM,
     COMMUNE.NOM              AS COMMUNE_NOM,
     LOCALITE.NOM             AS LOCALITE_NOM,
     LOCALITE.FK_CANTO_CODE   AS CANTON_CODE,
     LOCALITE.FK_COMMU_CODE   AS COMMUNE_CODE,
     LOCALITE.NUMERO          AS LOCALITE_CODE
    FROM LOCALITE
    JOIN COMMUNE  ON COMMUNE.CODE = LOCALITE.FK_COMMU_CODE AND COMMUNE.FK_CANTO_CODE = LOCALITE.FK_CANTO_CODE
    JOIN CANTON   ON CANTON.CODE = LOCALITE.FK_CANTO_CODE
    ORDER BY CANTON_NOM, COMMUNE_NOM, LOCALITE_NOM;

-- La vue ne semble pas tenir compte des immeubles sans CP s'il y a des immeubles avec CP dans cette rue
-- This does the join in the wrong direction, and misses RUEs with no IMMEUBLE.
CREATE OR REPLACE VIEW TR_DICACOLO_RUCP AS
    SELECT
     DISTRICT_ADMIN.NOM       AS DISTRICT_NOM,
     CANTON.NOM               AS CANTON_NOM,
     COMMUNE.NOM              AS COMMUNE_NOM,
     LOCALITE.NOM             AS LOCALITE_NOM,
     RUE.NOM                  AS RUE_NOM,
     IMMEUBLE.FK_CODPT_NUMERO AS CODE_POSTAL
    FROM IMMEUBLE
    
    JOIN RUE ON RUE.NUMERO = IMMEUBLE.FK_RUE_NUMERO
    JOIN LOCALITE ON LOCALITE.NUMERO = RUE.FK_LOCAL_NUMERO
    JOIN COMMUNE  ON COMMUNE.CODE = LOCALITE.FK_COMMU_CODE AND COMMUNE.FK_CANTO_CODE = LOCALITE.FK_CANTO_CODE
    JOIN CANTON   ON CANTON.CODE = LOCALITE.FK_CANTO_CODE
    JOIN DISTRICT_ADMIN   ON DISTRICT_ADMIN.CODE = CANTON.FK_DISTR_CODE
    -- Exclure les immeubles sans CP s'il y a des immeubles avec CP dans cette rue
    WHERE IMMEUBLE.INDIC_PROVISOIRE = 'N' -- La vue ne tient pas compte des immeubles provisoires.
    -- WHERE (
    --     IMMEUBLE.FK_CODPT_NUMERO is not null
    --     OR (NOT EXISTS (
    --         SELECT * FROM IMMEUBLE as immcomp
    --         WHERE immcomp.FK_CODPT_NUMERO is not null
    --         AND immcomp.date_fin_valid is null
    --         AND immcomp.fk_rue_numero = IMMEUBLE.fk_rue_numero
    --        ))
    --    )
    AND LOCALITE.DATE_FIN_VALID IS NULL AND RUE.DATE_FIN_VALID IS NULL AND IMMEUBLE.DATE_FIN_VALID IS NULL -- Le fichier ne contient compte que des données ‘effectives’ (DATE_FIN_VALID = NULL).
    GROUP BY DISTRICT_NOM, CANTON_NOM, COMMUNE_NOM, LOCALITE_NOM, RUE_NOM, CODE_POSTAL
    ORDER BY DISTRICT_NOM, CANTON_NOM, COMMUNE_NOM, LOCALITE_NOM, RUE_NOM, CODE_POSTAL;

CREATE OR REPLACE VIEW R_CANTCOMM_LOCARUE AS
    SELECT
     CANTON_NOM, COMMUNE_NOM, LOCALITE_NOM, RUE_NOM
    FROM TR_DICACOLO_RUCP;

-------------
-- INDEXES --
-------------


CREATE INDEX  ICODPT02
    ON  CODE_POSTAL
    (LIB_POST_MAJUSCULE                   ASC);

CREATE INDEX  ICOMMU02
    ON  COMMUNE
    (NOM_MAJUSCULE                        ASC);

CREATE INDEX  IIMMEU01
    ON  IMMEUBLE
    (FK_RUE_NUMERO                        ASC);

CREATE INDEX  IIMMEU03
    ON  IMMEUBLE
    (NUMERO                               ASC,
     CODE_MULTIPLE                        ASC);

CREATE INDEX  IIMMEU04
    ON  IMMEUBLE
    (FK_CODPT_NUMERO                      ASC);

CREATE INDEX IIMMEU05
    ON IMMEUBLE
    (INDIC_PROVISOIRE                    ASC);

CREATE INDEX  ILOCAL01
    ON  LOCALITE
    (FK_CANTO_CODE                        ASC,
     FK_COMMU_CODE                        ASC);

CREATE INDEX  ILOCAL03
    ON  LOCALITE
    (NOM_MAJUSCULE                        ASC);

CREATE INDEX  IQUART01
    ON  QUARTIER
    (FK_LOCAL_NUMERO                      ASC);

CREATE INDEX  IRUE01
    ON  RUE
    (FK_LOCAL_NUMERO                      ASC);

CREATE INDEX  IRUE03
    ON  RUE
    (NOM_MAJUSCULE                        ASC);

RESET client_encoding;
RESET client_min_messages;
