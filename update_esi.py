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

#metadata_obj.create_all(engine)

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


def get_all_users():
    cursor = connection.execute(
        f"select character_id,character_name,refresh_token from Characters"
    )

    character_list = cursor.fetchall()
    return character_list

def refresh_esi_token(refresh_token):

    print("Update token")
    esisecurity.update_token(
        {
            "access_token": "",  # leave this empty
            "expires_in": -1,  # seconds until expiry, so we force refresh anyway
            "refresh_token": refresh_token,
        }
    )

    print("Refresh token")
    tokens = esisecurity.refresh()

    return tokens

def get_mining_ledger(character_id):
    """Get mining ledger data for a character_id

    Args:
        character_id (_type_): an individual character's id
        
    Returns:
        string: contract data json structure        
    """
    esi_req = esiapp.op["get_characters_character_id_mining"](character_id=character_id)
    ledger_req = esiclient.request(esi_req)
    return ledger_req.data

def does_row_exist(ledger_data):
    """Check if a contract has been stored

    Args:
        contract_id (Integer): Contract identifier

    Returns:
        boolean: Does it exist or not
    """ 
    query = f"select id from MiningLedger where character_id = {ledger_data['character_id']} and date = '{ledger_data['date']}' and quantity = {ledger_data['quantity']} and solar_system_id = {ledger_data['solar_system_id']} and type_id = {ledger_data['type_id']}"   
    cursor = connection.execute(query)
    data = cursor.fetchone()
    if data:
        return True
    else:
        return False



print("Getting characters")
characters = get_all_users()
for character in characters:
    #character_id = character_id[0]
    character_id, character_name, refresh_token = character
    print(character_id)
    print(character_name)
    
    print("Refreshing the token")
    token = refresh_esi_token(refresh_token)
    
    print("Getting ledger details")
    ledger_data = get_mining_ledger(character_id)
    for ld in ledger_data:
        ld['character_id'] = character_id
        if does_row_exist(ld): continue
        ledger_query = mining_ledger.insert().values(
            character_id = character_id,
            date = ld['date'],
            quantity = ld['quantity'],
            solar_system_id = ld['solar_system_id'],
            type_id = ld['type_id']
        )
        result = connection.execute(ledger_query)
    