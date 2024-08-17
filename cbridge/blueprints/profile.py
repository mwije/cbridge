from flask import Blueprint
from flask_login import login_required, current_user

profile_bp = Blueprint('profile', __name__)

@profile_bp.route('/')
@login_required
def index():
    return "profile page"