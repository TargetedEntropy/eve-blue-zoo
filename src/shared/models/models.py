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


@login_manager.user_loader
def user_loader(character_id):
    return Users.query.filter_by(character_id=character_id).first()


@login_manager.request_loader
def request_loader(request):
    character_name = request.form.get("character_name")
    user = Users.query.filter_by(character_name=character_name).first()
    return user if user else None
