from flask import Flask

from .extensions import init_extensions, db, login_manager, bcrypt, migrate
from .blueprints import register_blueprints


#from flask_migrate import Migrate
#from flask_bcrypt import Bcrypt

def create_app():
    app = Flask(__name__, template_folder='templates')
    app.config.from_object('cbridge.config.Config')
    
    init_extensions(app)
    register_blueprints(app)

    #create_session(app)

    #migrate = Migrate(app, db)
    return app


def create_session(app):
    login_manager = LoginManager()
    login_manager.init_app(app)

    from models import User

    @login_manager.user_loader
    def load_user(uid):
        return User.query.get(uid)
    
    bcrypt = Bcrypt(app)