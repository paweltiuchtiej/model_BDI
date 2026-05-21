# SELECT Z BAZY
import numpy as np
import pandas as pd
import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy import text

def merge_db_data():

    engine = create_engine(
        "mysql+pymysql://root:12PS89@192.168.100.12/geostar_test_3"
    )

    surface_strop = text("""
        SELECT
            gs_otwory.X, 
            gs_otwory.Y, 
            MAX(gs_otwory.H - gs_lit.strop) AS Z,
            0 as nugget,
            concat("S_top_",gs_lit.seria) AS surface
        FROM gs_lit
        INNER JOIN gs_otwory
        ON gs_lit.nazw = gs_otwory.nazw
        WHERE gs_lit.NAZW LIKE '%59+971.37%' AND gs_lit.nazw NOT LIKE '59+971.37/MS-100/13'  AND gs_lit.seria is not null
        GROUP BY surface, gs_otwory.nazw
    """)

    surface_spag = text("""
        SELECT 
            gs_otwory.X, 
            gs_otwory.Y, 
            MIN(gs_otwory.H - gs_lit.strop - IFNULL(gs_lit.grub, 0)) AS Z,
            0 as nugget,
            concat("S_top_",gs_lit.seria) AS surface
        FROM gs_lit
        INNER JOIN gs_otwory
        ON gs_lit.nazw = gs_otwory.nazw 
        WHERE gs_lit.NAZW LIKE '%59+971.37%' AND gs_lit.nazw NOT LIKE '59+971.37/MS-100/13' AND gs_lit.seria IN (2001, 2002, 202, 203, 2102, 2103, 204, 205, 206, 207, 208)
        GROUP BY surface, gs_otwory.nazw
    """)

    soczewki_razem = text("""
        WITH params AS (
            SELECT 1.00 AS t,  0.0 AS v UNION ALL   -- surface_soczewki	
            SELECT 0.95,       0.4      UNION ALL 	-- surface_soczewki_2
            SELECT 0.75,       0.0      UNION ALL	-- surface_soczewki_P75_T
            SELECT 0.75,       0.75     UNION ALL	-- surface_soczewki_P75_B
            SELECT 0.50,       0.0      UNION ALL	-- surface_soczewki_P50_T
            SELECT 0.50,       0.9      UNION ALL	-- surface_soczewki_P50_B
            SELECT 0.25,       0.0      UNION ALL	-- surface_soczewki_P25_T
            SELECT 0.25,       1.0					-- surface_soczewki_P25_B
        )
        SELECT DISTINCT
            ((1 - p.t) * t.x1 + p.t * t.xn)     AS X,
            ((1 - p.t) * t.y1 + p.t * t.yn)     AS Y,
            (t.H1 - l.STROP - p.v * l.grub)     AS Z,
            0                                   AS nugget,
            CONCAT('S_top_', l.seria)           AS surface
        FROM triangulacja_delaunay t
        INNER JOIN gs_lit l ON t.nazw = l.nazw
        CROSS JOIN params p
        WHERE l.seria IN (2001, 2002, 202, 203, 2102, 2103, 204, 205, 206, 207, 208)
        AND t.nazw_2 <> t.nazw      
    """)

    orient_strop = text("""
        SELECT
            gs_otwory.X, 
            gs_otwory.Y, 
            MAX(gs_otwory.H - gs_lit.strop) AS Z,
            0 AS G_x,
            0 AS G_y,
            -1 AS G_z,
            0 as nugget,
            concat("S_top_",gs_lit.seria) AS surface
        FROM gs_lit
        INNER JOIN gs_otwory
        ON gs_lit.nazw = gs_otwory.nazw 
        WHERE gs_lit.NAZW LIKE '%59+971.37%' AND gs_lit.nazw NOT LIKE '59+971.37/MS-100/13' AND gs_lit.seria is not NULL
        GROUP BY surface, gs_otwory.nazw
    """)


    orient_spag = text("""
        SELECT
            gs_otwory.X, 
            gs_otwory.Y, 
            MIN(gs_otwory.H - gs_lit.strop - IFNULL(gs_lit.grub, 0)) AS Z,
            0 AS G_x,
            0 AS G_y,
            1 AS G_z,
            0 as nugget,
            concat("S_top_",gs_lit.seria) AS surface
        FROM gs_lit
        INNER JOIN gs_otwory
        ON gs_lit.nazw = gs_otwory.nazw 
        WHERE gs_lit.NAZW LIKE '%59+971.37%' AND gs_lit.nazw NOT LIKE '59+971.37/MS-100/13' AND gs_lit.seria IN (2001, 2002, 202, 203, 2102, 2103, 204, 205, 206, 207, 208)
        GROUP BY surface, gs_otwory.nazw
    """)

    orient_soczewki_razem = text("""
        WITH params AS (
            SELECT 1.00 AS t, 0.0 AS v, -1 AS G_z UNION ALL  -- orient_soczewki
            SELECT 0.95,      0.4,       1        UNION ALL  -- orient_soczewki_2
            SELECT 0.75,      0.0,      -1        UNION ALL  -- orient_soczewki_P75_T
            SELECT 0.75,      0.9,       1        UNION ALL  -- orient_soczewki_P75_B
            SELECT 0.50,      0.0,      -1        UNION ALL  -- orient_soczewki_P50_T
            SELECT 0.50,      0.9,       1        UNION ALL  -- orient_soczewki_P50_B
            SELECT 0.25,      0.0,      -1        UNION ALL  -- orient_soczewki_P25_T
            SELECT 0.25,      1.0,       1                   -- orient_soczewki_P25_B
        )
        SELECT DISTINCT
            ((1 - p.t) * t.x1 + p.t * t.xn)     AS X,
            ((1 - p.t) * t.y1 + p.t * t.yn)     AS Y,
            (t.H1 - l.STROP - p.v * l.grub)     AS Z,
            0                                   AS G_x,
            0                                   AS G_y,
            p.G_z                               AS G_z,
            0                                   AS nugget,
            CONCAT('S_top_', l.seria)           AS surface
        FROM triangulacja_delaunay t
        INNER JOIN gs_lit l ON t.nazw = l.nazw
        CROSS JOIN params p
        WHERE l.seria IN (2001, 2002, 202, 203, 2102, 2103, 204, 205, 206, 207, 208)
        AND t.nazw_2 <> t.nazw
    """)

    boreholes = text("""
        SELECT 
            gs_otwory.NAZW,
            gs_otwory.X, 
            gs_otwory.Y, 
            (gs_otwory.H - gs_lit.strop) AS Z
        FROM gs_lit
        INNER JOIN gs_otwory
        ON gs_lit.nazw = gs_otwory.nazw 
        WHERE gs_lit.NAZW LIKE '%59+971.37%' AND gs_lit.nazw NOT LIKE '59+971.37/MS-100/13' AND gs_lit.seria is not NULL GROUP BY gs_otwory.NAZW
    """)

    przekroje_z_otworami = text("""
        WITH RECURSIVE numbers AS (
            SELECT 1 AS nr
            UNION ALL
            SELECT nr + 1 FROM numbers WHERE nr < (SELECT MAX(ST_NumPoints(shape)) FROM przekroje)
        ),
        przekroje_punkty AS (
            SELECT 
                nazwa,
                n.nr,
                ST_Y(ST_PointN(shape, n.nr)) AS x,
                ST_X(ST_PointN(shape, n.nr)) AS y
            FROM przekroje
            JOIN numbers n ON n.nr <= ST_NumPoints(shape)
        )
        SELECT 
            p.nazwa AS nazwa_przekroju,
            p.nr AS nr_punktu,
            o.nazw AS nazwa_otworu,
            p.x AS x,
            p.y AS y,
            o.H AS z,
            o.GLUB AS glebokosc
        FROM przekroje_punkty p
        LEFT JOIN gs_otwory o ON ABS(p.x - o.X) < 2 AND ABS(p.y - o.Y) < 2
        ORDER BY p.nazwa, p.nr;
    """)


    with engine.connect() as conn:
        df_surface_strop = pd.read_sql(surface_strop, conn)
        df_surface_spag = pd.read_sql(surface_spag, conn)
        df_soczewki_razem = pd.read_sql(soczewki_razem,conn) 
        df_orient_strop = pd.read_sql(orient_strop, conn)
        df_orient_spag = pd.read_sql(orient_spag, conn)
        df_orient_soczewki_razem = pd.read_sql(orient_soczewki_razem, conn)
        df_boreholes = pd.read_sql(boreholes, conn)
        df_przekroje_z_otworami = pd.read_sql(przekroje_z_otworami, conn)

    df_surface = pd.concat(
        [df_surface_strop, df_surface_spag, df_soczewki_razem],
        ignore_index=True
    )

    df_orient = pd.concat(
        [df_orient_strop, df_orient_spag, df_orient_soczewki_razem], #
        ignore_index=True
    )

    df_surface[['X','Y','Z','nugget']] = df_surface[['X','Y','Z', 'nugget']].astype(float)
    df_surface['surface'] = df_surface['surface'].astype(str)
    df_orient[['X','Y','Z','G_x','G_y','G_z']] = df_orient[['X','Y','Z','G_x','G_y','G_z']].astype(float)
    
    otwory_litologia = text("""
        WITH ordered AS (
            SELECT 
                gs_otwory.NAZW, 
                gs_lit.SYMBOL,
                gs_lit.strop,
                (gs_otwory.H - gs_lit.strop) AS Z,
                CONCAT('S_top_', gs_lit.seria) AS surface,
                ROW_NUMBER() OVER (PARTITION BY gs_lit.NAZW ORDER BY gs_lit.strop) AS rn
            FROM gs_lit
            INNER JOIN gs_otwory ON gs_lit.nazw = gs_otwory.nazw 
            WHERE gs_lit.NAZW LIKE '%59+971.37%' AND gs_lit.nazw NOT LIKE '59+971.37/MS-100/13' AND gs_lit.seria IS NOT NULL
        ),
        islands AS (
            SELECT *,
                rn - ROW_NUMBER() OVER (PARTITION BY NAZW, SYMBOL ORDER BY rn) AS grp
            FROM ordered
        )
        SELECT
            NAZW,
            SYMBOL,
            MIN(strop) AS strop_from,
            MAX(strop) AS strop_to,
            MAX(Z) AS Z_top,
            surface
        FROM islands
        GROUP BY NAZW, SYMBOL, grp, surface
        ORDER BY NAZW, strop_from;
    """)

    print("jeszcze poz mia")
    with engine.connect() as conn:
        df_otwory_z_litologia = pd.read_sql(otwory_litologia, conn)

    return df_surface, df_orient, df_boreholes, df_przekroje_z_otworami, df_otwory_z_litologia

