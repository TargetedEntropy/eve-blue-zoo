# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from importlib import import_module
from apps.authentication.esi import EsiAuth
from apscheduler.schedulers.background import BackgroundScheduler
import atexit

db = SQLAlchemy()
login_manager = LoginManager()

esi = EsiAuth()


def register_extensions(app):
    db.init_app(app)
    login_manager.init_app(app)
    esi.init_app(app)
    

def register_blueprints(app):
    for module_name in ('authentication', 'home'):
        module = import_module('apps.{}.routes'.format(module_name))
        app.register_blueprint(module.blueprint)


def configure_database(app):

    @app.before_first_request
    def initialize_database():
        db.create_all()

    @app.teardown_request
    def shutdown_session(exception=None):
        db.session.remove()

def configure_scheduler(app):
    # Setup the scheduler to refresh coures, assignments and submissions
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=update_all_children, trigger="interval", seconds=3600)
    scheduler.start()

    # Shut down the scheduler when exiting the app
    atexit.register(lambda: scheduler.shutdown())



    # Goodbye
    

def create_app(config):
    app = Flask(__name__)
    app.config.from_object(config)
    register_extensions(app)
    register_blueprints(app)
    configure_database(app)
    return app
