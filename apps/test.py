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


engine = create_engine(config["SQLALCHEMY_DATABASE_URI"])

connection = engine.connect()

metadata_obj = MetaData()

mining_ledger = Table(
    'MiningLedger',
    metadata_obj,
    Column('id', BigInteger,  primary_key=True),
    Column('character_id', BigInteger),
    Column('date', DateTime),
    Column('quantity', BigInteger),
    Column('solar_system_id', BigInteger),
    Column('type_id', BigInteger)
)

import datetime

def get_price(type_id, quantity):
    query = f"select `avg` from itemPrices where type_id = {type_id} order by date_created limit 1"
    cursor = connection.execute(query)
    try:
        price_data = cursor.fetchone()[0]
    except Exception as e:
        print(f"Failed to execute query: {query} : {e}")
    print(f"{type_id}:{price_data*quantity}")
    
    value = price_data * quantity
    return value

cursor = connection.execute("select distinct(date) from MiningLedger")
all_dates = cursor.fetchall()

data = []
for ledger_date in all_dates:
    daily_total = 0
    ledger_date = ledger_date[0]
    date_str = ledger_date.strftime('%Y-%m-%d')
    cursor = connection.execute(
        f"select Characters.character_name,MiningLedger.type_id,invTypes.TypeName,MiningLedger.quantity,mapSolarSystems.solarSystemName from MiningLedger INNER JOIN Characters ON MiningLedger.character_id = Characters.character_id INNER JOIN invTypes ON MiningLedger.type_id = invTypes.typeID  INNER JOIN mapSolarSystems ON MiningLedger.solar_system_id = mapSolarSystems.solarSystemID where date = '{date_str}' group by Characters.character_name,quantity,solar_system_id,type_id,type_id order by MiningLedger.quantity desc"
    )

    ledger_data = cursor.fetchall()
    #print(ledger_data)
    for ledger_row in ledger_data:
        character_name, typeId, typeName, quantity, solar_system_name = ledger_row
        
        value = get_price(typeId, quantity)

        # print(f"{character_name}:{typeName}:{solar_system_name}:{quantity}:{value}")
        data.append([ledger_date,character_name, typeName, quantity, solar_system_name, value])
        daily_total = daily_total + value
    data.append([ledger_date, "Total", "", "", "", daily_total])

#print(data)