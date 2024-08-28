from flask import Flask, redirect, url_for, flash

from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
import logging
import os

db = SQLAlchemy()
login_manager = LoginManager()
bcrypt = Bcrypt()
migrate = Migrate()

def init_extensions(app):
    db.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    migrate.init_app(app, db)

    init_logger(app)

    from .models.user import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @login_manager.unauthorized_handler
    def unauthorized_callback():
        flash("Request declined (Reason: Unauthorized)")
        return redirect(url_for('home.index'))

def init_logger(app):
    # Create a console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Get the base directory of your project
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # Custom formatter to display relative paths
    class RelativePathFormatter(logging.Formatter):
        def format(self, record):
            # Modify the pathname to be relative to the base directory
            record.pathname = os.path.relpath(record.pathname, base_dir)
            return super().format(record)

    # Define the log format, excluding 'asctime' and shortening the 'pathname'
    formatter = RelativePathFormatter(
        '%(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    )
    console_handler.setFormatter(formatter)

    # Add the handler to the root logger
    logging.getLogger().addHandler(console_handler)

    # Set the logging level for the root logger
    logging.getLogger().setLevel(logging.INFO)

    # Set Flask's logger to use the same configuration
    app.logger.addHandler(console_handler)
    app.logger.setLevel(logging.INFO)