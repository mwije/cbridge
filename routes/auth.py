from flask import Blueprint

auth = Blueprint('auth', __name__)

@auth.route('/login')
def login():
    return 'login'

@auth.route('/register')
def register():
    return 'register'

@auth.route('logout')
def logout():
    return 'logout'

