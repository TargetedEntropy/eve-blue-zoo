"""User Related Classes, data for users"""

import os
import hashlib
import binascii
import time
from datetime import datetime
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import (
    BigInteger,
    Column,
    Integer,
    Date,
    Boolean,
    Text,
    String,
    DateTime,
)

from flask_app.apps import db
from sqlalchemy.ext.declarative import declarative_base

class MiningLedger(db.Model):
    __tablename__ = "MiningLedger"
    id = Column(BigInteger, primary_key=True)
    character_id = Column(BigInteger)
    date = Column(Date())
    quantity = Column(BigInteger)
    solar_system_id = Column(BigInteger)
    type_id = Column(BigInteger)


class Characters(db.Model):
    __tablename__ = "Characters"
    character_id = Column(BigInteger, primary_key=True)
    master_character_id = Column(BigInteger)
    character_owner_hash = Column(Text, nullable=True)
    character_name = Column(String(200), nullable=True)

    # SSO Token stuff
    access_token = Column(Text, nullable=True)
    access_token_expires = Column(DateTime(), nullable=True)
    refresh_token = Column(Text, nullable=True)

    sso_is_valid = Column(Boolean, nullable=True)

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
    character_id = Column(BigInteger, primary_key=True)
    character_owner_hash = Column(Text, nullable=True)
    character_name = Column(String(200), nullable=True)

    # SSO Token stuff
    access_token = Column(Text, nullable=True)
    access_token_expires = Column(DateTime(), nullable=True)
    refresh_token = Column(Text, nullable=True)

    # Discord
    discord_user_id = Column(String(64), nullable=True)

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


class SkillSet(db.Model):
    __tablename__ = "skillsets"

    id = Column(Integer, primary_key=True)
    character_id = Column(Integer, nullable=False)
    total_sp = Column(Integer, nullable=False)
    unallocated_sp = Column(Integer, nullable=False)


def hash_pass(password):
    """Hash a password for storing."""

    salt = hashlib.sha256(os.urandom(60)).hexdigest().encode("ascii")
    pwdhash = hashlib.pbkdf2_hmac(
        "sha512", password.encode("utf-8"), salt, 100000)
    pwdhash = binascii.hexlify(pwdhash)
    return salt + pwdhash  # return bytes
