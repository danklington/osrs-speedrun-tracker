from config import DB_CREDENTIALS
from sqlalchemy import create_engine, event
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker
import time

# Create a connection to the database
DB_USERNAME = DB_CREDENTIALS['DB_USERNAME']
DB_PASSWORD = DB_CREDENTIALS['DB_PASSWORD']
DB_NAME = DB_CREDENTIALS['DB_NAME']
DB_HOST = DB_CREDENTIALS['DB_HOST']
DB_PORT = DB_CREDENTIALS['DB_PORT']

connection_string = (
    'mariadb+mariadbconnector://'
    f'{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
)
engine = create_engine(
    connection_string,
    pool_recycle=3600,
    pool_size=1,
    pool_pre_ping=True,
    connect_args={'ssl': False}
)

# Retry connecting to the database if the connection is lost.
def connect_with_retry(dbapi_connection, connection_record, connection_proxy):
    retries = 5
    for attempt in range(retries):
        try:
            dbapi_connection.ping()
            break
        except OperationalError:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
            else:
                raise

event.listen(engine, 'engine_connect', connect_with_retry)


Base = declarative_base()
Base.metadata.bind = engine
Session = scoped_session(sessionmaker(bind=engine))
