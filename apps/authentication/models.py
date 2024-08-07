# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from flask_login import UserMixin
from sqlalchemy import BigInteger, Column, Integer, ForeignKey
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.ext.declarative import declared_attr

from apps import db, login_manager

from datetime import datetime
import time

from apps.authentication.util import hash_pass

# class Skill(db.Model):
#     __tablename__ = 'skills'

#     id = db.Column(db.Integer, primary_key=True)
#     active_skill_level = db.Column(db.Integer, nullable=False)
#     skill_id = db.Column(db.Integer, nullable=False, unique=True)
#     skillpoints_in_skill = db.Column(db.Integer, nullable=False)
#     trained_skill_level = db.Column(db.Integer, nullable=False)
#     skillset_id = db.Column(db.Integer, ForeignKey('skillsets.id'), nullable=False)


class SkillSet(db.Model):
    __tablename__ = "skillsets"

    id = db.Column(db.Integer, primary_key=True)
    character_id = db.Column(db.Integer, nullable=False)
    total_sp = db.Column(db.Integer, nullable=False)
    unallocated_sp = db.Column(db.Integer, nullable=False)


#    skills = relationship('Skill', backref='skillset', cascade='all, delete-orphan')


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


@login_manager.user_loader
def user_loader(character_id):
    return Users.query.filter_by(character_id=character_id).first()


@login_manager.request_loader
def request_loader(request):
    character_name = request.form.get("character_name")
    user = Users.query.filter_by(character_name=character_name).first()
    return user if user else None
