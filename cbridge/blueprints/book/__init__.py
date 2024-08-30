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
        flash('New session registered')
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

@book_bp.route('/booking')
@role_required('client', 'helper')
def booking():
    patient = current_user.patient  # Assuming current_user is the logged-in patient
    title = "My Booking"

    # Check if the patient has an active appointment
    active_appointment = Appointment.query.filter_by(patient_id=patient.id, active=True).first()
    
    if active_appointment:
        
        return redirect(url_for('consult.lobby'))
    
    # If no active appointment, show available schedules
    available_schedules = Schedule.query.filter(
        Schedule.date >= datetime.now().date(),
        Schedule.active == True
    ).all()
    
    return render_template('schedule.html', title = title, bookings=available_schedules)

@book_bp.route('/booking/make/<int:schedule_id>', methods=['POST'])
@role_required('client', 'helper')
def make_booking(schedule_id):
    patient = current_user.patient  # Assuming current_user is the logged-in patient
    
    # Retrieve the selected schedule
    selected_schedule = Schedule.query.get(schedule_id)
    
    if selected_schedule and selected_schedule.active:
        if len(selected_schedule.appointments) < selected_schedule.max_bookings:
            # Create a new appointment
            new_appointment = Appointment(
                patient_id=patient.id,
                schedule_id=schedule_id,
                datetime = datetime.today()
                )
            db.session.add(new_appointment)
            db.session.commit()
            flash("Your appointment has been booked.")
        else:
            flash("This schedule is fully booked.")
    
    return redirect(url_for('book.booking'))

@book_bp.route('/booking/cancel/<int:appointment_id>', methods=['POST'])
@role_required('client', 'helper')
def cancel_appointment(appointment_id):
    patient = current_user.patient  # Assuming current_user is the logged-in patient
    appointment = Appointment.query.get(appointment_id)
    
    if appointment and appointment.patient_id == patient.id:
        db.session.delete(appointment)
        db.session.commit()
        flash("Your appointment has been canceled.")
    
    return redirect(url_for('book.booking'))
