"""Blueprint Models"""

from datetime import datetime
from sqlalchemy import Column, Integer, BigInteger, Boolean, DateTime, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class BlueprintLongDurationOrder(Base):
    """Blueprints available at NPC stations"""

    __tablename__ = "blueprint_long_duration_orders"
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(BigInteger, nullable=False, unique=True)
    type_id = Column(Integer, nullable=False)  # ItemID from market orders
    location_id = Column(BigInteger, nullable=False)
    system_id = Column(Integer, nullable=True)
    price = Column(BigInteger, nullable=False)
    duration = Column(Integer, nullable=False)  # Store the actual duration
    is_buy_order = Column(Boolean, nullable=False)
    first_detected = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_updated = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False)


class Blueprints(Base):
    """User's blueprints"""

    __tablename__ = "Blueprints"

    item_id = Column(BigInteger, primary_key=True)
    character_id = Column(BigInteger)
    location_flag = Column(String(64))
    location_id = Column(BigInteger)
    material_efficiency = Column(Integer)
    quantity = Column(Integer)
    runs = Column(Integer)
    time_efficiency = Column(Integer)
    type_id = Column(BigInteger)
