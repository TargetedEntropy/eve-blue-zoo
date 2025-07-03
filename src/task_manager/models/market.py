"""Market classes!"""

from sqlalchemy import Column, Integer, BigInteger, DateTime, Float, Text, Date, func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class MarketHistory(Base):
    __tablename__ = "market_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    typeID = Column(BigInteger)
    regionID = Column(Integer, nullable=False)
    average = Column(Float, nullable=False)
    date = Column(Date, nullable=False)
    highest = Column(Float, nullable=False)
    lowest = Column(Float, nullable=False)
    order_count = Column(Integer, nullable=False)
    volume = Column(Integer, nullable=False)
    updated_date = Column(DateTime, nullable=False, default=func.now())


class Transactions(Base):
    __tablename__ = "Transactions"

    character_id = Column(BigInteger, primary_key=True)
    amount = Column(Float, nullable=True)
    balance = Column(Float, nullable=True)
    context_id = Column(BigInteger, nullable=True)
    context_id_type = Column(Text, nullable=True)
    date = Column(DateTime(), nullable=True)
    description = Column(Text, nullable=True)
    first_party_id = Column(BigInteger, nullable=True)
    reason = Column(Text, nullable=True)
    ref_type = Column(Text, nullable=True)
    second_party_id = Column(BigInteger, nullable=True)
    tax = Column(Float, nullable=True)
    tax_receiver_id = Column(BigInteger, nullable=True)
