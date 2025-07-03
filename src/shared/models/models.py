# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

import time
from datetime import datetime
from flask_login import UserMixin
from sqlalchemy import BigInteger, Column, Integer, ForeignKey, Boolean, func
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.ext.declarative import declared_attr

from apps import db, login_manager


from apps.authentication.util import hash_pass


class Contract(db.Model):
    __tablename__ = "contracts"

    id = db.Column(db.Integer, primary_key=True)
    buyout = db.Column(db.Float, nullable=True)
    collateral = db.Column(db.Float, nullable=True)
    date_expired = db.Column(db.DateTime, nullable=False)
    date_issued = db.Column(db.DateTime, nullable=False)
    days_to_complete = db.Column(db.Integer, nullable=True)
    end_location_id = db.Column(db.BigInteger, nullable=True)
    for_corporation = db.Column(db.Boolean, nullable=True)
    issuer_corporation_id = db.Column(db.Integer, nullable=False)
    issuer_id = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=True)
    reward = db.Column(db.Float, nullable=True)
    start_location_id = db.Column(db.BigInteger, nullable=True)
    title = db.Column(db.Text, nullable=True)
    type = db.Column(db.Text, nullable=False)
    volume = db.Column(db.Float, nullable=True)


class BlueprintLongDurationOrder(db.Model):
    __tablename__ = "blueprint_long_duration_orders"

    # Primary key
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Order reference
    order_id = db.Column(
        db.BigInteger, nullable=False, unique=True
    )  # Reference to the actual market order

    # Item information
    type_id = db.Column(db.Integer, nullable=False)  # ItemID from market orders

    # Location information
    location_id = db.Column(db.BigInteger, nullable=False)
    system_id = db.Column(db.Integer, nullable=True)

    # Price information
    price = db.Column(
        db.BigInteger, nullable=False
    )  # Price in cents (same as MarketOrder)

    # Order details
    duration = db.Column(db.Integer, nullable=False)  # Store the actual duration
    is_buy_order = db.Column(db.Boolean, nullable=False)

    # Additional metadata
    first_detected = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_updated = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class Features(db.Model):
    __tablename__ = "features"

    id = db.Column(db.Integer, primary_key=True)
    character_id = db.Column(
        db.BigInteger,
        db.ForeignKey("Characters.character_id"),
        nullable=False,
        unique=True,
    )

    # Store feature names and their enabled status as a JSON object
    features = db.Column(db.JSON, default={})

    character = db.relationship(
        "Characters", backref=db.backref("features", uselist=False)
    )


class SkillSet(db.Model):
    __tablename__ = "skillsets"

    id = db.Column(db.Integer, primary_key=True)
    character_id = db.Column(db.Integer, nullable=False)
    total_sp = db.Column(db.Integer, nullable=False)
    unallocated_sp = db.Column(db.Integer, nullable=False)


class CharacterNotifications(db.Model):
    __tablename__ = "character_notifications"
    id = db.Column(db.Integer, primary_key=True)
    character_id = db.Column(db.Integer, nullable=False)
    master_character_id = db.Column(db.BigInteger)
    enabled_notifications = db.Column(db.Text)


class SentNotifications(db.Model):
    __tablename__ = "sent_notifications"
    id = db.Column(db.Integer, primary_key=True)
    character_id = db.Column(db.Integer, nullable=False)
    master_character_id = db.Column(db.BigInteger)
    total_sp = db.Column(db.Integer, nullable=False)
    notification_cleared = db.Column(db.Boolean, nullable=False, default=False)


class MarketHistory(db.Model):
    __tablename__ = "market_history"

    id = Column(db.Integer, primary_key=True, autoincrement=True)
    typeID = db.Column(db.BigInteger)
    regionID = db.Column(db.Integer, nullable=False)
    average = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, nullable=False)
    highest = db.Column(db.Float, nullable=False)
    lowest = db.Column(db.Float, nullable=False)
    order_count = db.Column(db.Integer, nullable=False)
    volume = db.Column(db.Integer, nullable=False)
    updated_date = db.Column(db.DateTime, nullable=False, default=func.now())


class InvType(db.Model):
    __tablename__ = "invTypes"

    typeID = db.Column(db.BigInteger, primary_key=True)
    groupID = db.Column(db.BigInteger, index=True)
    typeName = db.Column(db.String(100))
    description = db.Column(db.Text)
    mass = db.Column(db.Float)
    volume = db.Column(db.Float)
    capacity = db.Column(db.Float)
    portionSize = db.Column(db.BigInteger)
    raceID = db.Column(db.BigInteger)
    basePrice = db.Column(db.DECIMAL(19, 4))
    published = db.Column(db.Boolean)
    marketGroupID = db.Column(db.BigInteger)
    iconID = db.Column(db.BigInteger)
    soundID = db.Column(db.BigInteger)
    graphicID = db.Column(db.BigInteger)


class Blueprints(db.Model):
    __tablename__ = "Blueprints"

    item_id = db.Column(db.BigInteger, primary_key=True)
    character_id = db.Column(db.BigInteger)
    location_flag = db.Column(db.String(64))
    location_id = db.Column(db.BigInteger)
    material_efficiency = db.Column(db.Integer)
    quantity = db.Column(db.Integer)
    runs = db.Column(db.Integer)
    time_efficiency = db.Column(db.Integer)
    type_id = db.Column(db.BigInteger)


class Transactions(db.Model):
    __tablename__ = "Transactions"

    character_id = db.Column(db.BigInteger, primary_key=True)
    amount = db.Column(db.Float, nullable=True)
    balance = db.Column(db.Float, nullable=True)
    context_id = db.Column(db.BigInteger, nullable=True)
    context_id_type = db.Column(db.Text, nullable=True)
    date = db.Column(db.DateTime(), nullable=True)
    description = db.Column(db.Text, nullable=True)
    first_party_id = db.Column(db.BigInteger, nullable=True)
    reason = db.Column(db.Text, nullable=True)
    ref_type = db.Column(db.Text, nullable=True)
    second_party_id = db.Column(db.BigInteger, nullable=True)
    tax = db.Column(db.Float, nullable=True)
    tax_receiver_id = db.Column(db.BigInteger, nullable=True)


class MiningLedger(db.Model):
    __tablename__ = "MiningLedger"
    id = db.Column(db.BigInteger, primary_key=True)
    character_id = db.Column(db.BigInteger)
    date = db.Column(db.Date())
    quantity = db.Column(db.BigInteger)
    solar_system_id = db.Column(db.BigInteger)
    type_id = db.Column(db.BigInteger)


class ActivityProduct(db.Model):
    __tablename__ = "activity_products"

    # Primary key - you might want to add an auto-incrementing ID
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Data columns based on your CSV
    type_id = db.Column(db.Integer, nullable=False)
    activity_id = db.Column(db.Integer, nullable=False)
    product_type_id = db.Column(db.Integer, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)


class Characters(db.Model):
    __tablename__ = "Characters"
    character_id = db.Column(db.BigInteger, primary_key=True)
    master_character_id = db.Column(db.BigInteger)
    character_owner_hash = db.Column(db.Text, nullable=True)
    character_name = db.Column(db.String(200), nullable=True)

    # SSO Token stuff
    access_token = db.Column(db.Text, nullable=True)
    access_token_expires = db.Column(db.DateTime(), nullable=True)
    refresh_token = db.Column(db.Text, nullable=True)

    sso_is_valid = db.Column(db.Boolean, nullable=True)

    def get_id(self):
        """Required for flask-login"""
        return self.character_id

    def get_parent(self):
        """Required for flask-login"""
        return self.master_character_id

    def get_sso_data(self):
        """Little "helper" function to get formated data for esipy security"""
        return {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "expires_in": (
                self.access_token_expires - datetime.utcnow()
            ).total_seconds(),
        }

    def update_token(self, token_response):
        """helper function to update token data from SSO response"""
        self.access_token = token_response["access_token"]
        self.access_token_expires = datetime.fromtimestamp(
            time.time() + token_response["expires_in"]
        )
        if "refresh_token" in token_response:
            self.refresh_token = token_response["refresh_token"]


class StaStation(db.Model):
    __tablename__ = "staStations"

    # Primary key
    stationID = db.Column(db.BigInteger, primary_key=True, nullable=False)

    # Security and operational data
    security = db.Column(db.Float, nullable=True)
    dockingCostPerVolume = db.Column(db.Float, nullable=True)
    maxShipVolumeDockable = db.Column(db.Float, nullable=True)
    officeRentalCost = db.Column(db.Integer, nullable=True)
    operationID = db.Column(db.Integer, nullable=True)

    # Station classification
    stationTypeID = db.Column(db.Integer, nullable=True)
    corporationID = db.Column(db.Integer, nullable=True)

    # Location hierarchy
    solarSystemID = db.Column(db.Integer, nullable=True)
    constellationID = db.Column(db.Integer, nullable=True)
    regionID = db.Column(db.Integer, nullable=True)

    # Station information
    stationName = db.Column(db.String(100), nullable=True)

    # Coordinate information
    x = db.Column(db.Float, nullable=True)
    y = db.Column(db.Float, nullable=True)
    z = db.Column(db.Float, nullable=True)

    # Reprocessing information
    reprocessingEfficiency = db.Column(db.Float, nullable=True)
    reprocessingStationsTake = db.Column(db.Float, nullable=True)
    reprocessingHangarFlag = db.Column(db.Integer, nullable=True)


class Users(db.Model, UserMixin):
    __tablename__ = "Users"

    # our ID is the character ID from EVE API
    character_id = db.Column(db.BigInteger, primary_key=True)
    character_owner_hash = db.Column(db.Text, nullable=True)
    character_name = db.Column(db.String(200), nullable=True)

    # SSO Token stuff
    access_token = db.Column(db.Text, nullable=True)
    access_token_expires = db.Column(db.DateTime(), nullable=True)
    refresh_token = db.Column(db.Text, nullable=True)

    # Discord
    discord_user_id = db.Column(db.String(64), nullable=True)

    def __init__(self, **kwargs):
        for property, value in kwargs.items():
            # depending on whether value is an iterable or not, we must
            # unpack it's value (when **kwargs is request.form, some values
            # will be a 1-element list)
            if hasattr(value, "__iter__") and not isinstance(value, str):
                # the ,= unpack of a singleton fails PEP8 (travis flake8 test)
                value = value[0]

            if property == "password":
                value = hash_pass(value)  # we need bytes here (not plain str)

            setattr(self, property, value)

    def __repr__(self):
        return str(self.character_id)

    def get_id(self):
        """Required for flask-login"""
        return self.character_id

    def get_sso_data(self):
        """Little "helper" function to get formated data for esipy security"""
        return {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "expires_in": (
                self.access_token_expires - datetime.utcnow()
            ).total_seconds(),
        }

    def update_token(self, token_response):
        """helper function to update token data from SSO response"""
        self.access_token = token_response["access_token"]
        self.access_token_expires = datetime.fromtimestamp(
            time.time() + token_response["expires_in"],
        )
        if "refresh_token" in token_response:
            self.refresh_token = token_response["refresh_token"]


class MapSolarSystems(db.Model):
    __tablename__ = "mapSolarSystems"

    regionID = db.Column(db.Integer, nullable=True, index=True)
    constellationID = db.Column(db.Integer, nullable=True, index=True)
    solarSystemID = db.Column(db.Integer, primary_key=True)
    solarSystemName = db.Column(db.String(100), nullable=True)
    x = db.Column(db.Float, nullable=True)
    y = db.Column(db.Float, nullable=True)
    z = db.Column(db.Float, nullable=True)
    xMin = db.Column(db.Float, nullable=True)
    xMax = db.Column(db.Float, nullable=True)
    yMin = db.Column(db.Float, nullable=True)
    yMax = db.Column(db.Float, nullable=True)
    zMin = db.Column(db.Float, nullable=True)
    zMax = db.Column(db.Float, nullable=True)
    luminosity = db.Column(db.Float, nullable=True)
    border = db.Column(db.Boolean, nullable=True)
    fringe = db.Column(db.Boolean, nullable=True)
    corridor = db.Column(db.Boolean, nullable=True)
    hub = db.Column(db.Boolean, nullable=True)
    international = db.Column(db.Boolean, nullable=True)
    regional = db.Column(db.Boolean, nullable=True)
    constellation = db.Column(db.Boolean, nullable=True)
    security = db.Column(db.Float, nullable=True, index=True)
    factionID = db.Column(db.Integer, nullable=True)
    radius = db.Column(db.Float, nullable=True)
    sunTypeID = db.Column(db.Integer, nullable=True)
    securityClass = db.Column(db.String(2), nullable=True)


class MapRegion(db.Model):
    __tablename__ = "mapRegions"

    regionID = db.Column(db.Integer, primary_key=True, nullable=False)
    regionName = db.Column(db.String(100), nullable=True)
    x = db.Column(db.Float, nullable=True)
    y = db.Column(db.Float, nullable=True)
    z = db.Column(db.Float, nullable=True)
    xMin = db.Column(db.Float, nullable=True)
    xMax = db.Column(db.Float, nullable=True)
    yMin = db.Column(db.Float, nullable=True)
    yMax = db.Column(db.Float, nullable=True)
    zMin = db.Column(db.Float, nullable=True)
    zMax = db.Column(db.Float, nullable=True)
    factionID = db.Column(db.Integer, nullable=True)
    nebula = db.Column(db.Integer, nullable=True)
    radius = db.Column(db.Float, nullable=True)


@login_manager.user_loader
def user_loader(character_id):
    return Users.query.filter_by(character_id=character_id).first()


@login_manager.request_loader
def request_loader(request):
    character_name = request.form.get("character_name")
    user = Users.query.filter_by(character_name=character_name).first()
    return user if user else None
