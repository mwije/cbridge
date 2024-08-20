from functools import wraps
from flask import redirect, url_for, abort
from flask_login import current_user, login_required

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        @login_required  # Ensures the user is logged in
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))  # Redirect to login if not authenticated
            user_roles = current_user.get_roles()
            print(user_roles, roles)
            if not any(role in user_roles for role in roles):
                return redirect(url_for('profile.index'))  # Redirect to unauthorized page
            return f(*args, **kwargs)
        return decorated_function
    return decorator
