# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

import sys
from flask_migrate import Migrate
from decouple import config

from apps.config import config_dict
from apps import create_app, db


# WARNING: Don't run with debug turned on in production!
DEBUG = config("DEBUG", default=True, cast=bool)

# The configuration
GET_CONFIG_MODE = "Debug" if DEBUG else "Production"

try:
    # Load the configuration using the default values
    app_config = config_dict[GET_CONFIG_MODE.capitalize()]

except KeyError:
    sys.exit("Error: Invalid <config_mode>. Expected values [Debug, Production] ")

app_config.PREFERRED_URL_SCHEME = "https"

app = create_app(app_config)
Migrate(app, db)


if DEBUG:
    app.logger.info("DEBUG       = " + str(DEBUG))
    app.logger.info("Environment = " + GET_CONFIG_MODE)
    app.logger.info("DBMS        = " + app_config.SQLALCHEMY_DATABASE_URI)
    app.logger.info("PREFERRED_URL_SCHEME = " + app_config.PREFERRED_URL_SCHEME)

if __name__ == "__main__":
    app.run()
