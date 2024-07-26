# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

import os
from decouple import config

class Config(object):

    basedir = os.path.abspath(os.path.dirname(__file__))

    # Set up the App SECRET_KEY
    SECRET_KEY = config('SECRET_KEY', default='S#perS3crEt_007')

    SQLALCHEMY_DATABASE_URI = config('SQLALCHEMY_DATABASE_URI')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    ESI_SECRET_KEY = config('ESI_SECRET_KEY')
    ESI_CLIENT_ID = config('ESI_CLIENT_ID')
    ESI_CALLBACK = config('ESI_CALLBACK')
    ESI_USER_AGENT = config('ESI_USER_AGENT')
    ESI_SWAGGER_JSON = config('ESI_SWAGGER_JSON')    
    DISCORD_CLIENT_ID = config('DISCORD_CLIENT_ID')    
    DISCORD_CLIENT_SECRET = config('DISCORD_CLIENT_SECRET')    
    DISCORD_REDIRECT_URI = config('DISCORD_REDIRECT_URI')    
    DISCORD_BOT_TOKEN = config('DISCORD_BOT_TOKEN')
    OAUTHLIB_INSECURE_TRANSPORT= config('OAUTHLIB_INSECURE_TRANSPORT')


class ProductionConfig(Config):
    DEBUG = False

    # Security
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_DURATION = 3600

    # PostgreSQL database
    SQLALCHEMY_DATABASE_URI = '{}://{}:{}@{}:{}/{}'.format(
        config('DB_ENGINE', default='postgresql'),
        config('DB_USERNAME', default='appseed'),
        config('DB_PASS', default='pass'),
        config('DB_HOST', default='localhost'),
        config('DB_PORT', default=5432),
        config('DB_NAME', default='appseed-flask')
    )
    


    
    

class DebugConfig(Config):
    DEBUG = True

# Load all possible configurations
config_dict = {
    'Production': ProductionConfig,
    'Debug': DebugConfig
}
