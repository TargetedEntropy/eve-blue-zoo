# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from flask_login import UserMixin
from sqlalchemy import BigInteger

from apps.database import db
from apps.login_manager import login_manager
from datetime import datetime
import time

from apps.authentication.util import hash_pass


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

    # id = db.Column(db.Integer, primary_key=True)
    # username = db.Column(db.String(64), unique=True)
    # email = db.Column(db.String(64), unique=True)
    # password = db.Column(db.LargeBinary)

    # our ID is the character ID from EVE API
    character_id = db.Column(db.BigInteger, primary_key=True)
    character_owner_hash = db.Column(db.Text, nullable=True)
    character_name = db.Column(db.String(200), nullable=True)

    # SSO Token stuff
    access_token = db.Column(db.Text, nullable=True)
    access_token_expires = db.Column(db.DateTime(), nullable=True)
    refresh_token = db.Column(db.Text, nullable=True)

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
        return str(self.username)

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


@login_manager.user_loader
def user_loader(character_id):
    return Users.query.filter_by(character_id=character_id).first()


@login_manager.request_loader
def request_loader(request):
    character_name = request.form.get("character_name")
    user = Users.query.filter_by(character_name=character_name).first()
    return user if user else None
