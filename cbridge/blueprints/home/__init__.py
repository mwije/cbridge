from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from cbridge.decorators import role_required
from cbridge.models.user import User
from cbridge.extensions import db, bcrypt

home_bp = Blueprint('home', __name__)

@home_bp.route('/')
def index():
    return render_template('index.html')

    