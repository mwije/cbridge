from flask import Flask
from routes.user import user

APP_PORT = 8880


def create_app():
    app = Flask(__name__, template_folder='templates')

    app.register_blueprint(user, url_prefix='/user')

    return app