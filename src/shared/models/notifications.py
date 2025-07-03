"""Notification classes!"""

from sqlalchemy import Column, Integer, BigInteger, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class CharacterNotifications(Base):
    __tablename__ = "character_notifications"
    id = Column(Integer, primary_key=True)
    character_id = Column(Integer, nullable=False)
    master_character_id = Column(BigInteger)
    enabled_notifications = Column(Text)


class SentNotifications(Base):
    __tablename__ = "sent_notifications"
    id = Column(Integer, primary_key=True)
    character_id = Column(Integer, nullable=False)
    master_character_id = Column(BigInteger)
    total_sp = Column(Integer, nullable=False)
    notification_cleared = Column(Boolean, nullable=False, default=False)
