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


@login_manager.user_loader
def user_loader(character_id):
    return Users.query.filter_by(character_id=character_id).first()


@login_manager.request_loader
def request_loader(request):
    character_name = request.form.get("character_name")
    user = Users.query.filter_by(character_name=character_name).first()
    return user if user else None
