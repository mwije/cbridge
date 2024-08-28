from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from cbridge.decorators import role_required
from cbridge.models.user import *
from cbridge.extensions import db, bcrypt

from .forms import *

book_bp = Blueprint('book', __name__)

@book_bp.route('/schedule', methods=['GET', 'POST'])
@role_required('clinician')
def clinicianschedule():
    form = NewScheduleForm()
    if form.validate_on_submit():
        flash('Received')
        # Add schedule entry
        new_schedule = Schedule(
                clinician_id = current_user.clinician.id,
                date = form.date.data,
                max_bookings = form.max_bookings.data,
                time_start = form.time_start.data,
                time_end = form.time_end.data,
                active = True
                )
            
        db.session.add(new_schedule)
        db.session.commit()


    title = "Clinician's Schedule"

    bookings = Schedule.query.filter_by(clinician_id=current_user.clinician.id).order_by(Schedule.date).all()
    return render_template('schedule.html', title = title, bookings=bookings, new_schedule_form=form)

@book_bp.route('/schedule/remove/<int:schedule_id>', methods=['POST'])
@role_required('clinician')
def remove_schedule(schedule_id):
    schedule = Schedule.query.get(schedule_id)
    if schedule and schedule.clinician_id == current_user.clinician.id:
        db.session.delete(schedule)
        db.session.commit()
    return redirect(url_for('book.clinicianschedule'))

@book_bp.route('/schedule/toggle/<int:schedule_id>', methods=['POST'])
@role_required('clinician')
def toggle_schedule(schedule_id):
    schedule = Schedule.query.get(schedule_id)
    if schedule and schedule.clinician_id == current_user.clinician.id:
        schedule.active = not schedule.active
        db.session.commit()
    return redirect(url_for('book.clinicianschedule'))

@book_bp.route('/book')
@role_required('client', 'helper')
def booking():
    title = "My Booking"
    bookings = {}
    return render_template('schedule.html', title = title, bookings=bookings)


def get_bookings(clinician):
    return current_user.clinicians.id