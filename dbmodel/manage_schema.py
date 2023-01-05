import psycopg2

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
