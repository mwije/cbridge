from functools import wraps
from flask import redirect, url_for, abort
from flask_login import current_user, login_required
from datetime import datetime

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

def day_of_week(date):
    """
    Compute day of week from a vien date
    """
    return date.strftime('%A') if date else ''

from datetime import datetime, date

def ensure_datetime(dt):
    """Convert a date or datetime to a datetime object, defaulting to midnight for dates."""
    if isinstance(dt, datetime):
        return dt
    elif isinstance(dt, date):
        return datetime.combine(dt, datetime.min.time())
    else:
        raise TypeError("Unsupported date type")

def remaining_time(date_or_datetime, cutoff_hours=24):
    """Calculate remaining time and format it based on the cutoff value."""
    if date_or_datetime:
        # Ensure we are working with a datetime object
        date_or_datetime = ensure_datetime(date_or_datetime)
        now = datetime.now()
        delta = date_or_datetime - now
        
        # If delta is negative (past date)
        if delta.total_seconds() < 0:
            return "Date has passed"

        # Check if remaining time is greater than or equal to cutoff_hours
        if delta.total_seconds() >= cutoff_hours * 3600:
            # Format as days
            days = delta.days
            return f"{days} days"
        else:
            # Format as hours and minutes
            hours, remainder = divmod(delta.total_seconds(), 3600)
            minutes, _ = divmod(remainder, 60)
            return f"{int(hours)} hours, {int(minutes)} minutes"
    return ''

def is_past(date_or_datetime):
    """Check if the given date has passed."""
    date_or_datetime = ensure_datetime(date_or_datetime)
    return date_or_datetime < datetime.now()



def init_jinjafilters(app):
    app.jinja_env.filters['day_of_week'] = day_of_week
    app.jinja_env.filters['remaining_time'] = remaining_time
    app.jinja_env.filters['is_past'] = is_past