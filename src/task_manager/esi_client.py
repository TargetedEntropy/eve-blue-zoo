"""Shared ESI Client for Task Manager"""

import sys
import os
import logging

# Add path to access Flask app
sys.path.append(os.path.join(os.path.dirname(__file__), '../../flask_app'))

from apps.authentication.esi import EsiAuth

logger = logging.getLogger(__name__)


class TaskManagerESI:
    """Shared ESI client for task manager modules"""
    
    _instance = None
    _client = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._client is None:
            self._client = EsiAuth()
            logger.info("Initialized Preston ESI client for task manager")
    
    def get_esi(self, character, schema, **kwargs):
        """Get ESI data using Preston client"""
        return self._client.get_esi(character, schema, **kwargs)


# Global instance
esi = TaskManagerESI()