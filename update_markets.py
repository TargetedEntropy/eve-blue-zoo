"""ESI Contract searches
"""
# -*- encoding: utf-8 -*-
import hashlib
import ast
import json
from datetime import datetime
from esipy import EsiApp
from dotenv import dotenv_values
from genericpath import exists
import logging
from xmlrpc.client import Boolean
from requests import request
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, BigInteger, String, Float, DateTime, Text, Boolean
from esipy import EsiClient, EsiSecurity


from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# logger stuff
logger = logging.getLogger(__name__)
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
console = logging.StreamHandler()
console.setLevel(logging.DEBUG)
console.setFormatter(formatter)
logger.addHandler(console)

config = dotenv_values(".env")




# metadata_obj = MetaData()

from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, create_engine, BigInteger, func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class MarketOrder(Base):
    __tablename__ = 'MarketOrders'
    
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

class MarketHashes(Base):
    __tablename__ = 'MarketHashes'
    
    id = Column(Integer, primary_key=True)
    hash_value = Column(String(255))

class MarketUpdates(Base):
    __tablename__ = 'MarketUpdates'
    
    regionID = Column(BigInteger, primary_key=True, nullable=False)
    updated_data = Column(DateTime, nullable=False, default=func.now())

class MapRegion(Base):
    __tablename__ = 'mapRegions'
    
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


engine = create_engine(config["SQLALCHEMY_DATABASE_URI"])

connection = engine.connect()

Base.metadata.create_all(engine)



# Create a configured "Session" class
Session = sessionmaker(bind=engine)

# Create a session
session = Session()


# create the app
print("Creating App")

esi_app = EsiApp()
esiapp = esi_app.get_latest_swagger


# init the security object
print("Creating esisecurity object")
esisecurity = EsiSecurity(
    #    app=esiapp,
    redirect_uri=config['ESI_CALLBACK'],
    client_id=config['ESI_CLIENT_ID'],
    secret_key=config['ESI_SECRET_KEY'],
    headers={"User-Agent": "merriam@gmail.com"},
)

# init the client
print("Initialize EsiClient")
esiclient = EsiClient(security=esisecurity, cache=None, headers={
    "User-Agent": config['ESI_USER_AGENT']})


def get_region_id_by_date():
    result = session.query(MarketUpdates.regionID).order_by(MarketUpdates.updated_data.asc()).first()
    return result[0]

def get_region_name(region_id):
    result = session.query(MapRegion.regionName).filter_by(regionID=region_id).first()
    return result[0]

def get_market_data(region_id):

    # we want to know how much pages there are for The Forge
    # so we make a HEAD request first
    op = esiapp.op['get_markets_region_id_orders'](
        region_id=region_id,
        page=1,
        order_type='all',
    )
    res = esiclient.head(op)

    # if we have HTTP 200 OK, then we continue
    if res.status == 200:
        number_of_page = res.header['X-Pages'][0]

        # now we know how many pages we want, let's prepare all the requests
        operations = []
        for page in range(1, number_of_page+1):
            operations.append(
                esiapp.op['get_markets_region_id_orders'](
                    region_id=region_id,
                    page=page,
                    order_type='all',
                )
            )

        results = esiclient.multi_request(operations)
        return results
    else:
        return []

def save_market_data(response_data):

    # Create a new MarketOrder instance
    new_order = MarketOrder(
        duration=response_data.duration,
        is_buy_order=response_data.is_buy_order,
        issued=response_data.issued,
        location_id=response_data.location_id,
        min_volume=response_data.min_volume,
        order_id=response_data.order_id,
        price=response_data.price,
        range=response_data.range,
        system_id=response_data.system_id,
        type_id=response_data.type_id,
        volume_remain=response_data.volume_remain,
        volume_total=response_data.volume_total
    )

    
    # Add the new order to the session & Commit
    session.merge(new_order)
    session.commit()

def save_market_hash(hex_hash):
    new_hash = MarketHashes(
        hash_value=hex_hash
    )
    session.add(new_hash)
    session.commit()    


def update_region_timestamp(regionID):

    # Query the row to update
    update_row = session.query(MarketUpdates).filter_by(regionID=regionID).first()

    if update_row:
        # Update the updated_data field to the current timestamp
        update_row.updated_data = datetime.now()

        # Commit the transaction to persist the update
        session.commit()
    else:
        new_region = MarketUpdates(regionID=regionID)
        session.add(new_region)
        session.commit()
        
def get_hex_hash(response_data):
    
    try:
        json_data = json.dumps(response_data, default=str)
        hash_obj = hashlib.sha256(str(json_data).encode())
        hex_hash = hash_obj.hexdigest()    
        
        return hex_hash
    except Exception as error:
        print(f"Error getting hash, error: {error}")



def does_market_row_exist(hex_hash):
    """Check if market data has been stored

    Returns:
        boolean: Does it exist or not
    """
    return session.query(MarketHashes.id).filter_by(hash_value=hex_hash).first() is not None


def get_orders_for_region(region_id):
    order_count, insert_count = 0, 0
    print(f"Getting orders for region, {get_region_name(region_id)}")

    market_datas = get_market_data(region_id)
    for market_data in market_datas:
        request, response = market_data
        for response_data in response.data:
            order_count += 1
            # Get Hex hash
            hex_hash = get_hex_hash(response_data)

            # Check if row exits
            if does_market_row_exist(hex_hash): continue

            # Save Market Data
            save_market_data(response_data)

            # Save the Hash
            save_market_hash(hex_hash)
            
            insert_count += 1
    region_count += 1        
    
    update_region_timestamp(region_id)
        
    print(f"toal_order_count:{order_count}, total_insert_count:{insert_count}")
    

if __name__ == "__main__":
    region_id = get_region_id_by_date()
    get_orders_for_region(region_id)