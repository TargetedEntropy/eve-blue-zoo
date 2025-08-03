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

from .database import Base

class MiningLedger(Base):
    __tablename__ = "MiningLedger"
    id = Column(BigInteger, primary_key=True)
    character_id = Column(BigInteger)
    date = Column(Date())
    quantity = Column(BigInteger)
    solar_system_id = Column(BigInteger)
    type_id = Column(BigInteger)


class Characters(Base):
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


class SkillSet(Base):
    __tablename__ = "skillsets"

    id = Column(Integer, primary_key=True)
    character_id = Column(Integer, nullable=False)
    total_sp = Column(Integer, nullable=False)
    unallocated_sp = Column(Integer, nullable=False)


