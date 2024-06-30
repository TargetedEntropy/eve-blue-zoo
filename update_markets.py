"""ESI Contract searches
"""
# -*- encoding: utf-8 -*-
from esipy import EsiApp
from dotenv import dotenv_values
from genericpath import exists
import logging
from xmlrpc.client import Boolean
from requests import request
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, BigInteger, String, Float, DateTime, Text, Boolean
from esipy import EsiClient, EsiSecurity


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

from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class MarketOrder(Base):
    __tablename__ = 'MarketOrders'
    
    duration = Column(Integer, nullable=False)
    is_buy_order = Column(Boolean, nullable=False)
    issued = Column(DateTime, nullable=False)
    location_id = Column(Integer, nullable=False)
    min_volume = Column(Integer, nullable=False)
    order_id = Column(Integer, primary_key=True)
    price = Column(Float, nullable=False)
    range = Column(String(16), nullable=False)
    system_id = Column(Integer, nullable=False)
    type_id = Column(Integer, nullable=False)
    volume_remain = Column(Integer, nullable=False)
    volume_total = Column(Integer, nullable=False)


engine = create_engine(config["SQLALCHEMY_DATABASE_URI"])

connection = engine.connect()

Base.metadata.create_all(engine)

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


def get_all_regions():
    cursor = connection.execute(
        f"select distinct(regionID) from mapRegions"
    )

    region_list = cursor.fetchall()
    return region_list


def get_market_data(region_id):

    # we want to know how much pages there are for The Forge
    # so we make a HEAD request first
    op = app.op['get_markets_region_id_orders'](
        region_id=region_id,
        page=1,
        order_type='all',
    )
    res = client.head(op)

    # if we have HTTP 200 OK, then we continue
    if res.status == 200:
        number_of_page = res.header['X-Pages'][0]

        # now we know how many pages we want, let's prepare all the requests
        operations = []
        for page in range(1, number_of_page+1):
            operations.append(
                app.op['get_markets_region_id_orders'](
                    region_id=region_id,
                    page=page,
                    order_type='all',
                )
            )

        results = client.multi_request(operations)
        return results
    else:
        return []

def does_market_row_exist(market_data):
    """Check if market data has been stored

    Returns:
        boolean: Does it exist or not
    """
    exists = db.session.query(User.id).filter_by(name='davidism').first() is not None
    return exists
#    query = f"bool(User.query.filter_by(name='John Smith').first())"
#    select id from MiningLedger where character_id = {ledger_data['character_id']} and date = '{ledger_data['date']}' and quantity = {ledger_data['quantity']} and solar_system_id = {ledger_data['solar_system_id']} and type_id = {ledger_data['type_id']}"
#    cursor = connection.execute(query)
#    data = cursor.fetchone()
#    if data:
#        return True
#    else:
#        return False


# print("Getting characters")
# regions = get_all_regions()
# for region in regions:
#     # character_id = character_id[0]
#     character_id, character_name, refresh_token = character
#     print(character_id)
#     print(character_name)

#     print("Refreshing the token")
#     token = refresh_esi_token(refresh_token)

#     print("Getting ledger details")
#     ledger_data = get_mining_ledger(character_id)
#     for ld in ledger_data:
#         ld['character_id'] = character_id
#         if does_ledger_row_exist(ld):
#             continue
#         ledger_query = mining_ledger.insert().values(
#             character_id=ld['character_id'],
#             date=ld['date'],
#             quantity=ld['quantity'],
#             solar_system_id=ld['solar_system_id'],
#             type_id=ld['type_id']
#         )
#         result = connection.execute(ledger_query)

#     print("Getting Blueprint Details")
#     blueprint_data = get_blueprints(character_id)

#     for bp in blueprint_data:

#         bp['character_id'] = character_id
#         if does_bp_row_exist(bp):
#             continue
#         print(bp)
#         bp_query = blueprints_table.insert().values(
#             item_id=bp['item_id'],
#             character_id=character_id,
#             location_flag=bp['location_flag'],
#             location_id=bp['location_id'],
#             material_efficiency=bp['material_efficiency'],
#             quantity=bp['quantity'],
#             runs=bp['runs'],
#             time_efficiency=bp['time_efficiency'],
#             type_id=bp['type_id']
#         )
#         print(bp_query)
#         result = connection.execute(bp_query)
