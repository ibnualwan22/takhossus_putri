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

def create_app(config_name='default'):
    # --- PERUBAHAN KUNCI DI SINI ---
    # Jika aplikasi dijalankan di server (production), muat file .env.prod
    if os.getenv('FLASK_ENV') == 'production':
        dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env.prod')
        if os.path.exists(dotenv_path):
            load_dotenv(dotenv_path)
    # --- AKHIR PERUBAHAN ---

    app = Flask(__name__)
    # Sekarang, app.config akan dimuat dari environment variable yang baru saja di-load
    app.config.from_object(config[config_name])
    # Ambil database URI dari environment variable yang sudah di-load
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('PROD_DATABASE_URL')
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')


    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    from .routes import admin_bp
    app.register_blueprint(admin_bp)

    from .auth_routes import auth_bp
    app.register_blueprint(auth_bp)

    return app