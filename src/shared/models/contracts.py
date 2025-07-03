""" Contract Models """
from sqlalchemy import Column, Integer, BigInteger, Boolean
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class ContractItem(Base):
    """ Each Contract itself """
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
    """ Which contracts have been parse """
    __tablename__ = "contract_watch"
    id = Column(Integer, primary_key=True)
    character_id = Column(Integer, nullable=False)
    type_id = Column(BigInteger, nullable=True)
    located = Column(Boolean, default=False)
    notified = Column(Boolean, default=False)


class ContractNotify(Base):
    """ Whom have we already notified? """
    __tablename__ = "contract_notify"
    id = Column(Integer, primary_key=True)
    character_id = Column(Integer, nullable=False)
    contract_id = Column(BigInteger, nullable=True)
