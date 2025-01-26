from db import Base
from db import engine
from sqlalchemy import Table


class Scale(Base):
    __table__ = Table(
        'scale', Base.metadata, autoload_with=engine
    )
