import os.path
from peewee import (Model, SqliteDatabase, Proxy)


DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                       '..', 'data', 'database.db'))
SCHEMA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                           'schema.sql'))
DB_PROXY = Proxy()
DATABASE = SqliteDatabase(DB_PATH)
DB_PROXY.initialize(DATABASE)


def reset_database():
    try:
        DATABASE.close()
    except:
        pass
    try:
        os.remove(DB_PATH)
    except FileNotFoundError:
        pass
    with open(SCHEMA_PATH) as f:
        query = f.read()
    DATABASE.init(DB_PATH)
    DATABASE.connect()
    DATABASE.get_cursor().executescript(query)


class BaseModel(Model):
    class Meta:
        database = DB_PROXY