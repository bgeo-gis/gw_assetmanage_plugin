"""
This file is part of Giswater 3
The program is free software: you can redistribute it and/or modify it under the terms of the GNU
General Public License as published by the Free Software Foundation, either version 3 of the License,
or (at your option) any later version.
"""
# -*- coding: utf-8 -*-

import psycopg2
from inspect import getsourcefile
from pathlib import Path

# Connection parameters
DBNAME = "postgres"
USER = "postgres"
PASSWORD = "postgres"
HOST = "localhost"
PORT = "5432"

# Giswater schema parameters
PARENT_SCHEMA = "dev_3_5_031_assetmanage"
SCHEMA_SRID = "25831"
LANGUAGE = "es_ES"

if (
    not DBNAME
    or not USER
    or not PASSWORD
    or not HOST
    or not PORT
    or not PARENT_SCHEMA
    or not SCHEMA_SRID
    or not LANGUAGE
):
    print("There are some constants that have not been defined.")
    exit()

sql_folder = Path(getsourcefile(lambda: 0)).parent
files = ["ddl.sql", "tablect.sql", "dml.sql", f"i18n/{LANGUAGE}.sql", "sample.sql"]

conn = psycopg2.connect(
    dbname=DBNAME, user=USER, password=PASSWORD, host=HOST, port=PORT
)
cur = conn.cursor()

try:
    for file in files:
        with open(sql_folder / file, encoding='utf8') as f:
            sql = (
                f.read()
                .replace("PARENT_SCHEMA", PARENT_SCHEMA)
                .replace("SCHEMA_SRID", SCHEMA_SRID)
            )
        cur.execute(sql)
    conn.commit()
    print("Success!")
except Exception as e:
    conn.rollback()
    print(e)
finally:
    cur.close()
    conn.close()
