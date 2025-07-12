# app/__init__.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import config

db = SQLAlchemy()
migrate = Migrate()

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    db.init_app(app)
    migrate.init_app(app, db)

    # Daftarkan blueprint di sini
    from .routes import admin_bp # <-- TAMBAHKAN INI
    app.register_blueprint(admin_bp) # <-- TAMBAHKAN INI

    return app