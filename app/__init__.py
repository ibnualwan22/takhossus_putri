# app/__init__.py

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import config
from flask_login import LoginManager

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login' # Arahkan ke rute login jika belum login

# Dekorator ini tetap di luar
@login_manager.user_loader
def load_user(id):
    # Pindahkan import ke dalam fungsi ini untuk menghindari circular import
    from .models import User
    return User.query.get(int(id))


def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # Pindahkan import blueprint ke dalam create_app
    from .routes import admin_bp
    app.register_blueprint(admin_bp)

    from .auth_routes import auth_bp
    app.register_blueprint(auth_bp)

    return app