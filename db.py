from config import DB_CREDENTIALS
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

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
engine = create_engine(connection_string)

Session = sessionmaker(bind=engine)
