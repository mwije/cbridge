from flask import Blueprint, render_template
import logging

from .auth import auth_bp
from .profile import profile_bp
from .home import home_bp
from .book import book_bp
from .consult import consult_bp
from .emr import emr_bp, emr_fe
from .public import public_bp

def register_blueprints(app):
    app.register_blueprint(auth_bp)
    logging.info('blueprint auth registered')
    app.register_blueprint(home_bp)
    logging.info('blueprint home registered')
    app.register_blueprint(profile_bp, url_prefix='/profile')
    logging.info('blueprint profile registered')
    app.register_blueprint(book_bp)
    logging.info('blueprint book registered')
    app.register_blueprint(consult_bp)
    logging.info('blueprint consult registered')
    app.register_blueprint(emr_bp)
    app.register_blueprint(emr_fe)
    logging.info('blueprint emr registered')
    app.register_blueprint(public_bp)
    logging.info('blueprint public registered')
    
    @app.errorhandler(404)
    def error404(error):
        return render_template('error.html', error=error.name, code=error.code, message=error.description), error.code
