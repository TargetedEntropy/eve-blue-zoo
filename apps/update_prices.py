from datetime import datetime
import re
from MySQLdb import TIMESTAMP, Timestamp
from esipy import EsiApp
from dotenv import dotenv_values
from genericpath import exists
import logging
from xmlrpc.client import Boolean
from requests import request
import requests
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, BigInteger, String, Float, DateTime, Text, Boolean, TIMESTAMP
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


engine = create_engine(config["SQLALCHEMY_DATABASE_URI"])

connection = engine.connect()

metadata_obj = MetaData()


itemPrices = Table(
    'itemPrices',
    metadata_obj,
    Column('date_created', DateTime),
    Column('type_id', BigInteger),
    Column('avg', Float),
    Column('market_name', String(256))
)

metadata_obj.create_all(engine)


cursor = connection.execute('select invTypes.typeID,invTypes.TypeName from invTypes INNER JOIN invGroups ON invTypes.groupID = invGroups.groupID where invGroups.categoryID = 25')
#cursor = connection.execute('select invTypes.typeID,invTypes.TypeName from invTypes INNER JOIN invGroups ON invTypes.groupID = invGroups.groupID where invTypes.groupID = 711')
items_to_update = cursor.fetchall()


ep_json = {"market_name": "jita"}

# Build the list of items we're going to request
items = []
for item in items_to_update:
    typeID, typeName = item
    if "Compressed" in typeName: continue
    items.append({"type_id": typeID})

ep_json['items'] = items

req = requests.post("https://evepraisal.com/appraisal/structured.json", json=ep_json)

# Convert the timestamp to a dt object and set our market
date_created = dt_object = datetime.fromtimestamp(req.json()['appraisal']['created'])
market_name = req.json()['appraisal']['market_name']

for item in req.json()['appraisal']['items']:
    item_insert = itemPrices.insert().values(date_created=date_created, type_id=item['typeID'], avg=item['prices']['sell']['avg'], market_name=market_name)
    try:
        result = connection.execute(item_insert)
    except Exception as e:
        print(f"Failed:{e}")

