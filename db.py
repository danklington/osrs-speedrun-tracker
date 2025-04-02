from config import DB_CREDENTIALS
from contextlib import contextmanager
from sqlalchemy import create_engine, event
from sqlalchemy.pool import Pool
from sqlalchemy.exc import DisconnectionError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker

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
    pool_use_lifo=True,
    connect_args={'ssl': False}
)


@event.listens_for(Pool, "checkout")
def checkout_listener(dbapi_connection, connection_record, connection_proxy):
    """ Ensure connection is alive when checking out of pool. """
    try:
        try:
            dbapi_connection.ping(False)
        except TypeError:
            dbapi_connection.ping()
    except dbapi_connection.OperationalError as e:
        # Raise DisconnectionError - pool will try connecting again up to three
        # times before raising.
        if e.args[0] in (2006, 2013, 2014, 2045, 2055):
            raise DisconnectionError
        else:
            raise


Base = declarative_base()
Base.metadata.bind = engine


@contextmanager
def get_session():
    session = scoped_session(sessionmaker(bind=engine))
    try:
        yield session
    finally:
        session.close()
