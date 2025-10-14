from flask import Flask, request, jsonify, redirect, url_for, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from dotenv import load_dotenv
load_dotenv()
import logging
import os


db = SQLAlchemy()
login_manager = LoginManager()

def create_app(test_config=None):
    """Create and configure the Flask app.

    test_config: optional dict used to override configuration (useful in tests and local dev).
    """
    app = Flask(__name__)
    # Base secret
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

    # Default MySQL configuration (used when no override is provided)
    app.config.setdefault('MYSQL_HOST', '127.0.0.1')
    app.config.setdefault('MYSQL_USER', 'root')
    app.config.setdefault('MYSQL_PASSWORD', os.getenv('MYSQL_PASSWORD'))
    app.config.setdefault('MYSQL_DB', 'registration_db')

    # Allow overriding the SQLALCHEMY_DATABASE_URI from environment or test_config
    env_db_uri = os.getenv('SQLALCHEMY_DATABASE_URI')
    if test_config and 'SQLALCHEMY_DATABASE_URI' in test_config:
        app.config['SQLALCHEMY_DATABASE_URI'] = test_config['SQLALCHEMY_DATABASE_URI']
    elif env_db_uri:
        app.config['SQLALCHEMY_DATABASE_URI'] = env_db_uri
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = (
            f"mysql+pymysql://{app.config['MYSQL_USER']}:{app.config['MYSQL_PASSWORD']}@"
            f"{app.config['MYSQL_HOST']}/{app.config['MYSQL_DB']}"
        )

    db.init_app(app)

    # Initialize and configure login manager
    login_manager.init_app(app)
    login_manager.login_view = 'login'

    with app.app_context():
        from models import User

        # Flask-Login user loader
        @login_manager.user_loader
        def load_user(user_id):
            return User.query.get(int(user_id))

        # Try to create tables but do not crash the app if DB is unavailable.
        try:
            db.create_all()
        except Exception as e:
            # Log a warning and continue; this allows local testing without a MySQL server.
            app.logger.warning('Database unavailable at startup, continuing without creating tables: %s', e)

        return app

