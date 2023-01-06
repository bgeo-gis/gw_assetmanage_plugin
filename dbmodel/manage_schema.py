import psycopg2
from inspect import getsourcefile
from pathlib import Path

# Connection parameters
DBNAME = None
USER = None
PASSWORD = None
HOST = None
PORT = None

# Giswater schema parameters
PARENT_SCHEMA = None
SCHEMA_SRID = None

if (
    not DBNAME
    or not USER
    or not PASSWORD
    or not HOST
    or not PORT
    or not PARENT_SCHEMA
    or not SCHEMA_SRID
):
    print("There are some constants that have not been defined.")
    exit()

files = ["ddl.sql", "tablect.sql"]
sql_folder = Path(getsourcefile(lambda: 0)).parent

conn = psycopg2.connect(
    dbname=DBNAME, user=USER, password=PASSWORD, host=HOST, port=PORT
)
cur = conn.cursor()

try:
    for file in files:
        with open(sql_folder / file) as f:
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
