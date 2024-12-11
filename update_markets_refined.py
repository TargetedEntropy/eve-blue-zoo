# -*- encoding: utf-8 -*-
from sqlalchemy.exc import IntegrityError
from tqdm import tqdm
from datetime import datetime
from esipy import EsiApp, EsiClient, EsiSecurity
from dotenv import dotenv_values
from genericpath import exists
import logging
from requests import request
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    BigInteger,
    String,
    Float,
    DateTime,
    Boolean,
    func,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# logger setup
logger = logging.getLogger(__name__)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
console = logging.StreamHandler()
console.setLevel(logging.DEBUG)
console.setFormatter(formatter)
logger.addHandler(console)

config = dotenv_values(".env")
Base = declarative_base()

class MarketOrder(Base):
    __tablename__ = "MarketOrders"

    duration = Column(Integer, nullable=False)
    is_buy_order = Column(Boolean, nullable=False)
    issued = Column(DateTime, nullable=False)
    location_id = Column(BigInteger, nullable=False)
    min_volume = Column(Integer, nullable=False)
    order_id = Column(BigInteger, primary_key=True)
    price = Column(Float, nullable=False)
    range = Column(String(16), nullable=False)
    system_id = Column(BigInteger, nullable=False)
    type_id = Column(BigInteger, nullable=False)
    volume_remain = Column(BigInteger, nullable=False)
    volume_total = Column(BigInteger, nullable=False)

class MarketUpdates(Base):
    __tablename__ = "MarketUpdates"

    regionID = Column(BigInteger, primary_key=True, nullable=False)
    updated_data = Column(DateTime, nullable=False, default=func.now())

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

engine = create_engine(
    config["SQLALCHEMY_DATABASE_URI"],
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
)
connection = engine.connect()
Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()

esi_app = EsiApp()
esiapp = esi_app.get_latest_swagger

esisecurity = EsiSecurity(
    redirect_uri=config["ESI_CALLBACK"],
    client_id=config["ESI_CLIENT_ID"],
    secret_key=config["ESI_SECRET_KEY"],
    headers={"User-Agent": "merriam@gmail.com"},
)

esiclient = EsiClient(
    security=esisecurity, cache=None, headers={"User-Agent": config["ESI_USER_AGENT"]}
)

def get_region_id_by_date():
    result = (
        session.query(MarketUpdates.regionID)
        .order_by(MarketUpdates.updated_data.asc())
        .first()
    )
    return result[0]

def get_region_name(region_id):
    result = session.query(MapRegion.regionName).filter_by(regionID=region_id).first()
    return result[0]

def get_market_data(region_id):
    op = esiapp.op["get_markets_region_id_orders"](
        region_id=region_id,
        page=1,
        order_type="all",
    )
    res = esiclient.head(op)

    if res.status == 200:
        number_of_page = res.header["X-Pages"][0]
        print(f"Market Pages: {number_of_page}")
        # number_of_page = 10
        operations = []
        for page in range(1, number_of_page + 1):
            operations.append(
                esiapp.op["get_markets_region_id_orders"](
                    region_id=region_id,
                    page=page,
                    order_type="all",
                )
            )
        results = esiclient.multi_request(operations)
        return results
    else:
        return []

def save_market_data_bulk(response_data_list):
    """
    Save market data in bulk for better performance, handling duplicates gracefully.
    """
    new_orders = []
    for data in response_data_list:
        new_order = MarketOrder(
            duration=data.duration,
            is_buy_order=data.is_buy_order,
            issued=data.issued,
            location_id=data.location_id,
            min_volume=data.min_volume,
            order_id=data.order_id,
            price=data.price,
            range=data.range,
            system_id=data.system_id,
            type_id=data.type_id,
            volume_remain=data.volume_remain,
            volume_total=data.volume_total,
        )
        new_orders.append(new_order)

    try:
        session.bulk_save_objects(new_orders, update_changed_only=True)
        session.commit()
        return len(new_orders)
    except IntegrityError as e:
        session.rollback()
        logger.error(f"Error during bulk save: {e}")
        return 0


def update_region_timestamp(regionID):
    update_row = session.query(MarketUpdates).filter_by(regionID=regionID).first()

    if update_row:
        update_row.updated_data = datetime.now()
        session.commit()
    else:
        new_region = MarketUpdates(regionID=regionID)
        session.add(new_region)
        session.commit()

def get_orders_for_region(region_id):
    order_count, insert_count = 0, 0

    print(f"Getting orders for region: {get_region_name(region_id)}")
    market_datas = get_market_data(region_id)

    print(f"Storing orders for region: {get_region_name(region_id)}")
    for market_data in tqdm(market_datas, desc="Processing market data"):
        _, response = market_data
        order_count += len(response.data)

        # Save Market Data in bulk
        insert_count += save_market_data_bulk(response.data)

    update_region_timestamp(region_id)

    print(f"Total order count: {order_count}, total insert count: {insert_count}")

if __name__ == "__main__":
    region_id = "10000002"  # Jita
    get_orders_for_region(region_id)
