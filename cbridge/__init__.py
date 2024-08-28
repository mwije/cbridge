from flask import Flask
import logging
from .extensions import init_extensions, db, login_manager, bcrypt, migrate
from .blueprints import register_blueprints


#from flask_migrate import Migrate
#from flask_bcrypt import Bcrypt

def create_app():
    app = Flask(__name__, template_folder='templates')
    app.config.from_object('cbridge.config.Config')
    
    init_extensions(app)
    logging.info('extensions initialized')
    register_blueprints(app)
    logging.info('blueprints registered')

    #migrate = Migrate(app, db)
    return app