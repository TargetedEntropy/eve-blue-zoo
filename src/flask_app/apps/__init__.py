# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

import os
from importlib import import_module
from flask import Flask, g
from flask_login import LoginManager
from flask_discord import DiscordOAuth2Session
from apps.authentication.esi import EsiAuth

from models.database import SessionLocal, engine, Base


# Initialize extensions
login_manager = LoginManager()
esi = EsiAuth()
discord_client = DiscordOAuth2Session()


def create_app(config):
    """Application factory pattern for creating Flask app instances."""
    print("Starting App")
    
    # Create Flask app instance
    app = Flask(__name__)
    app.config.from_object(config)
    
    # Initialize all extensions and components
    _init_extensions(app)
    _register_blueprints(app)
    _configure_database(app)
    # _configure_tasks(app)  # Uncomment when ready to use
    
    return app


def _init_extensions(app):
    """Initialize Flask extensions with the app instance."""
    # Authentication
    login_manager.init_app(app)
    login_manager.login_view = 'authentication_blueprint.login'  # Configure login endpoint
    login_manager.login_message = 'Please log in to access this page.'
    
    # ESI Authentication
    esi.init_app(app)
    
    # Discord OAuth
    discord_client.init_app(app)


def _register_blueprints(app):
    """Register all application blueprints."""
    blueprint_modules = ("authentication", "home")
    
    for module_name in blueprint_modules:
        try:
            module = import_module(f"apps.{module_name}.routes")
            app.register_blueprint(module.blueprint)
            app.logger.debug(f"Registered blueprint: {module_name}")
        except ImportError as e:
            app.logger.error(f"Failed to import blueprint {module_name}: {e}")
            raise


def _configure_database(app):
    """Configure database settings and session handling."""
    
    def create_tables():
        """Create database tables if they don't exist."""
        try:
            Base.metadata.create_all(bind=engine)
            app.logger.info("Database tables created/verified")
        except Exception as e:
            app.logger.error(f"Error creating database tables: {e}")
            raise
    
    @app.before_request
    def before_request():
        """Create a database session for each request."""
        g.db = SessionLocal()
    
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        """Clean up database session after each request."""
        db = g.pop('db', None)
        if db is not None:
            if exception:
                db.rollback()
            db.close()
    
    # Log database configuration
    if app.debug:
        app.logger.debug("Database configured with SQLAlchemy Core/ORM")


def _configure_tasks(app):
    """Configure background tasks (currently disabled)."""
    # Uncomment and modify when ready to use background tasks
    # from apps.tasks.task_main import MainTasks
    # task_master = MainTasks(app)
    # return task_master
    pass


# Get current database session
# def get_db():
#     """Get the current database session from Flask g object."""
#     if 'db' not in g:
#         g.db = SessionLocal()
#     return g.db