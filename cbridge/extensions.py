from flask import Flask, redirect, url_for, flash

from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
import logging
import os
import random
import string
from datetime import datetime
import qrcode

from .decorators import init_jinjafilters

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
    init_jinjafilters(app)

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

def generate_qr_code(data):
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')

    # Save QR code image
    qr_path = os.path.join('/path/to/save/qr_codes', 'qr_code.png')
    img.save(qr_path)
    return qr_path

def random_string(length=8):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def get_unique_filename(path, length=8, extension='', datestamp=False):
    """Generate a unique filename that does not already exist in the given path."""
    path = '.' + path.rstrip()+ '/'
    path = rel_to_abs_path(path)
#    print(path)
    if not os.path.isdir(path):
        raise ValueError("The provided path is not a valid directory")
    while True:
        filename = random_string(length) + f'-{datetime.now().strftime("%Y%m%d")}'
        if not extension == '':
            filename = filename  + '.' + extension
        full_path = os.path.join(path, filename)
        if not os.path.exists(full_path):
            return {'filename':filename, 'path':path}

def generate_qr_code(data):
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')

    # Save QR code image
    name_result = get_unique_filename(path='/static/prescriptions/', extension='jpg', datestamp=True)
    qr_filename= name_result['filename']
    qr_path = name_result['path']
    #print('QR',qr_path,qr_filename)
    img.save(qr_path+'/'+qr_filename)
    return 'static/prescriptions/' + qr_filename

def abs_to_rel_path(absolute_path):
    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.relpath(absolute_path, start=current_script_dir)

def rel_to_abs_path(relative_path):
    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.abspath(os.path.join(current_script_dir, relative_path))

def base_url():
    return os.path.dirname(os.path.realpath(__file__))