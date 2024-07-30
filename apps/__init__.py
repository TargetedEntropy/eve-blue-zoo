# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from importlib import import_module
from apps.authentication.esi import EsiAuth

db = SQLAlchemy()
login_manager = LoginManager()

esi = EsiAuth()
login_manager = LoginManager()

discord_client = None


def register_extensions(app):
    db.init_app(app)
    login_manager.init_app(app)
    esi.init_app(app)


def register_blueprints(app):
    for module_name in ("authentication", "home"):
        module = import_module("apps.{}.routes".format(module_name))
        app.register_blueprint(module.blueprint)


def configure_database(app):

    with app.app_context():
        db.create_all()

    @app.teardown_request
    def shutdown_session(exception=None):
        db.session.remove()


def configure_tasks(app):
    task_master = import_module("apps.tasks.task_main")
    task_master.MainTasks(app)


from flask_discord import DiscordOAuth2Session


def configure_discord(app):
    global discord_client
    discord_client = DiscordOAuth2Session(app)


def create_app(config):
    app = Flask(__name__)
    app.config.from_object(config)
    configure_discord(app)
    register_extensions(app)
    register_blueprints(app)
    configure_database(app)
    configure_tasks(app)
    return app
