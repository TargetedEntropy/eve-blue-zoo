"""Common Eve Models"""


# from sqlalchemy.ext.declarative import declared_attr

# from apps import db, login_manager

# from apps.authentication.util import hash_pass

from sqlalchemy.orm import relationship, backref
from sqlalchemy import (
    Column,
    Integer,
    BigInteger,
    Boolean,
    String,
    Float,
    Text,
    ForeignKey,
    DECIMAL,
    JSON,
)
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class MapSolarSystems(Base):
    __tablename__ = "mapSolarSystems"

    regionID = Column(Integer, nullable=True, index=True)
    constellationID = Column(Integer, nullable=True, index=True)
    solarSystemID = Column(Integer, primary_key=True)
    solarSystemName = Column(String(100), nullable=True)
    x = Column(Float, nullable=True)
    y = Column(Float, nullable=True)
    z = Column(Float, nullable=True)
    xMin = Column(Float, nullable=True)
    xMax = Column(Float, nullable=True)
    yMin = Column(Float, nullable=True)
    yMax = Column(Float, nullable=True)
    zMin = Column(Float, nullable=True)
    zMax = Column(Float, nullable=True)
    luminosity = Column(Float, nullable=True)
    border = Column(Boolean, nullable=True)
    fringe = Column(Boolean, nullable=True)
    corridor = Column(Boolean, nullable=True)
    hub = Column(Boolean, nullable=True)
    international = Column(Boolean, nullable=True)
    regional = Column(Boolean, nullable=True)
    constellation = Column(Boolean, nullable=True)
    security = Column(Float, nullable=True, index=True)
    factionID = Column(Integer, nullable=True)
    radius = Column(Float, nullable=True)
    sunTypeID = Column(Integer, nullable=True)
    securityClass = Column(String(2), nullable=True)


class MapRegion(Base):
    __tablename__ = "mapRegions"

    regionID = Column(Integer, primary_key=True, nullable=False)
    regionName = Column(String(100), nullable=True)
    x = Column(Float, nullable=True)
    y = Column(Float, nullable=True)
    z = Column(Float, nullable=True)
    xMin = Column(Float, nullable=True)
    xMax = Column(Float, nullable=True)
    yMin = Column(Float, nullable=True)
    yMax = Column(Float, nullable=True)
    zMin = Column(Float, nullable=True)
    zMax = Column(Float, nullable=True)
    factionID = Column(Integer, nullable=True)
    nebula = Column(Integer, nullable=True)
    radius = Column(Float, nullable=True)


class StaStation(Base):
    __tablename__ = "staStations"

    # Primary key
    stationID = Column(BigInteger, primary_key=True, nullable=False)

    # Security and operational data
    security = Column(Float, nullable=True)
    dockingCostPerVolume = Column(Float, nullable=True)
    maxShipVolumeDockable = Column(Float, nullable=True)
    officeRentalCost = Column(Integer, nullable=True)
    operationID = Column(Integer, nullable=True)

    # Station classification
    stationTypeID = Column(Integer, nullable=True)
    corporationID = Column(Integer, nullable=True)

    # Location hierarchy
    solarSystemID = Column(Integer, nullable=True)
    constellationID = Column(Integer, nullable=True)
    regionID = Column(Integer, nullable=True)

    # Station information
    stationName = Column(String(100), nullable=True)

    # Coordinate information
    x = Column(Float, nullable=True)
    y = Column(Float, nullable=True)
    z = Column(Float, nullable=True)

    # Reprocessing information
    reprocessingEfficiency = Column(Float, nullable=True)
    reprocessingStationsTake = Column(Float, nullable=True)
    reprocessingHangarFlag = Column(Integer, nullable=True)


class ActivityProduct(Base):
    __tablename__ = "activity_products"

    # Primary key - you might want to add an auto-incrementing ID
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Data columns based on your CSV
    type_id = Column(Integer, nullable=False)
    activity_id = Column(Integer, nullable=False)
    product_type_id = Column(Integer, nullable=False)
    quantity = Column(Integer, nullable=False)


class InvType(Base):
    __tablename__ = "invTypes"

    typeID = Column(BigInteger, primary_key=True)
    groupID = Column(BigInteger, index=True)
    typeName = Column(String(100))
    description = Column(Text)
    mass = Column(Float)
    volume = Column(Float)
    capacity = Column(Float)
    portionSize = Column(BigInteger)
    raceID = Column(BigInteger)
    basePrice = Column(DECIMAL(19, 4))
    published = Column(Boolean)
    marketGroupID = Column(BigInteger)
    iconID = Column(BigInteger)
    soundID = Column(BigInteger)
    graphicID = Column(BigInteger)


class Features(Base):
    __tablename__ = "features"

    id = Column(Integer, primary_key=True)
    character_id = Column(
        BigInteger,
        ForeignKey("Characters.character_id"),
        nullable=False,
        unique=True,
    )

    # Store feature names and their enabled status as a JSON object
    features = Column(JSON, default={})

    character = relationship("Characters", backref=backref("features", uselist=False))
