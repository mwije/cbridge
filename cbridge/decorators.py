from functools import wraps
from flask import redirect, url_for, abort
from flask_login import current_user, login_required
from datetime import datetime, date, time as time_type

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

def day_of_week(dt, time=None):
    """
    Compute day of week from a given date or datetime. If a date is passed, combine it with the optional time.
    """
    dt = ensure_datetime(dt, time)
    return dt.strftime('%A') if dt else ''



def ensure_datetime(dt, time=None):
    """
    Ensure the input is a datetime object. If a date is passed, combine it with the optional time.
    """
    if isinstance(dt, datetime):
        return dt
    elif isinstance(dt, date):
        if time and isinstance(time, time_type):
            return datetime.combine(dt, time)
        return datetime.combine(dt, datetime.min.time())
    raise ValueError("Input must be a date or datetime object")


def remaining_time(date_or_datetime, cutoff_hours=24, time=None):
    """Calculate remaining time and format it based on the cutoff value."""
    if date_or_datetime:
        # Ensure we are working with a datetime object
        date_or_datetime = ensure_datetime(date_or_datetime, time)
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

def is_past(date_or_datetime, time=None):
    """Check if the given date has passed."""
    date_or_datetime = ensure_datetime(date_or_datetime, time)
    return date_or_datetime < datetime.now()



def init_jinjafilters(app):
    app.jinja_env.filters['day_of_week'] = day_of_week
    app.jinja_env.filters['remaining_time'] = remaining_time
    app.jinja_env.filters['is_past'] = is_past