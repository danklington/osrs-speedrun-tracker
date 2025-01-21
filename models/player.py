from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, BigInteger

Base = declarative_base()

class Player(Base):
    __tablename__ = 'player'

    id = Column(Integer, primary_key=True)
    name = Column(String(32), nullable=False)
    discord_id = Column(BigInteger, nullable=False)
