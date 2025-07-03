"""Contract Models"""

from sqlalchemy import Column, Integer, BigInteger, Boolean, DateTime, Float, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Contract(Base):
    """Contracts themselves"""

    __tablename__ = "contracts"
    id = Column(Integer, primary_key=True)
    buyout = Column(Float, nullable=True)
    collateral = Column(Float, nullable=True)
    date_expired = Column(DateTime, nullable=False)
    date_issued = Column(DateTime, nullable=False)
    days_to_complete = Column(Integer, nullable=True)
    end_location_id = Column(BigInteger, nullable=True)
    for_corporation = Column(Boolean, nullable=True)
    issuer_corporation_id = Column(Integer, nullable=False)
    issuer_id = Column(Integer, nullable=False)
    price = Column(Float, nullable=True)
    reward = Column(Float, nullable=True)
    start_location_id = Column(BigInteger, nullable=True)
    title = Column(Text, nullable=True)
    type = Column(Text, nullable=False)
    volume = Column(Float, nullable=True)


class ContractItem(Base):
    """Each Contract Details"""

    __tablename__ = "contract_items"
    id = Column(Integer, primary_key=True)
    contract_id = Column(BigInteger, nullable=False)
    record_id = Column(BigInteger, nullable=False)
    is_blueprint_copy = Column(Boolean, nullable=True)
    is_included = Column(Boolean, nullable=False)
    item_id = Column(BigInteger, nullable=True)
    material_efficiency = Column(Integer, nullable=True)
    quantity = Column(Integer, nullable=False)
    runs = Column(Integer, nullable=True)
    time_efficiency = Column(Integer, nullable=True)
    type_id = Column(Integer, nullable=False)


class ContractTrack(Base):
    """Which contracts have been parse"""

    __tablename__ = "contract_watch"
    id = Column(Integer, primary_key=True)
    character_id = Column(Integer, nullable=False)
    type_id = Column(BigInteger, nullable=True)
    located = Column(Boolean, default=False)
    notified = Column(Boolean, default=False)


class ContractNotify(Base):
    """Whom have we already notified?"""

    __tablename__ = "contract_notify"
    id = Column(Integer, primary_key=True)
    character_id = Column(Integer, nullable=False)
    contract_id = Column(BigInteger, nullable=True)
