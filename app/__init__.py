# app/__init__.py (Versi Final)

import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import config
from flask_login import LoginManager
from dotenv import load_dotenv # <-- Tambahkan import ini

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'

@login_manager.user_loader
def load_user(id):
    from .models import User
    return User.query.get(int(id))

# app/__init__.py

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # --- LOGIKA BARU YANG DIPERBAIKI ---
    # Cek environment dan pilih URL database yang sesuai
    if app.config['DEBUG']: # DEBUG=True ada di DevelopmentConfig
        app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DEV_DATABASE_URL')
    else: # Jika tidak DEBUG (mode production)
        app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('PROD_DATABASE_URL')

    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
    # Pastikan URI tidak kosong sebelum melanjutkan
    if not app.config['SQLALCHEMY_DATABASE_URI']:
        raise RuntimeError("DATABASE_URL is not set.")
    # --- AKHIR PERBAIKAN ---

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    from .routes import admin_bp
    app.register_blueprint(admin_bp)

    from .auth_routes import auth_bp
    app.register_blueprint(auth_bp)

    return app