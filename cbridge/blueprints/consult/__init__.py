from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from cbridge.decorators import role_required
from cbridge.models.user import *
from cbridge.extensions import db, bcrypt

from .forms import *
import random, string
from datetime import datetime, date

consult_bp = Blueprint('consult', __name__)

@consult_bp.route('/staging', methods=['GET', 'POST'])
@role_required('clinician')
def staging():
    form = QueueControlForm()
    thedate = datetime.today().date()
    thedate = date(2024,8,29)
    appointments = db.session.query(Appointment).join(Schedule).filter(
        Schedule.date == thedate, Schedule.clinician_id == current_user.clinician.id
    ).order_by(Appointment.id.asc()).all()

    # Populate the RadioField with patient names and appointment IDs
    form.patient.choices = [(appt.id, f"{appt.patient.user.name} - {appt.datetime.strftime('%H:%M')}") for appt in appointments]

    if form.validate_on_submit():
        # Find the selected appointment
        selected_appointment = Appointment.query.get(form.patient.data)
   
        # Check if a Conference already exists for this appointment
        existing_conference = db.session.query(Conference).filter_by(appointment_id=selected_appointment.id).first()

        if existing_conference:
            # Use the existing conference
            conference = existing_conference
        else:
            # Generate a unique URL for the conference room
            random_url = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
            conference_url = f"{random_url}"

            # Create a new Conference entry
            conference = Conference(appointment_id=selected_appointment.id, url=conference_url)
            db.session.add(conference)
            db.session.commit()


        # Redirect clinician to the /tele page
        return redirect(url_for('consult.consultation', conference_id=conference.id))

    return render_template('lobby_clinician.html', thedate=thedate, queue_form=form)

@consult_bp.route('/lobby', methods=['GET', 'POST'])
@role_required('client')
def lobby():
    thedate = datetime.today().date()
    appointments = db.session.query(Appointment).join(Schedule).filter(
        Appointment.patient_id == current_user.patient.id,
        Appointment.active == True
    ).order_by(Appointment.id.desc()).all()
    appointment = appointments[0]
    # TODO: what if multiple appointments are pending

    clinician = db.session.query(Clinician).join(User).filter(
        Clinician.id == appointment.schedule.clinician_id
    )

    return render_template('lobby_patient.html', thedate=thedate, appointment=appointment, clinician=clinician)

@consult_bp.route('/appointment/<int:appointment_id>/status', methods=['GET'])
def get_appointment_status(appointment_id):
    # Retrieve the appointment record
    appointment = db.session.query(Appointment).filter(
        Appointment.id == appointment_id,
        Appointment.active == True
    ).first()

    if not appointment:
        return jsonify({'error': 'Appointment not found or inactive'}), 404

    # Get the status and conference URL
    status = appointment.status  # Assuming 'status' is a column in your Appointment model
    #conference = ( current_app.config['VIDEO_HOST_URL'] + appointment.conference.url) if appointment.conference else None
    conference = url_for('consult.consultation', conference_id=appointment.conference.id) if appointment.conference else None
    live = appointment.conference.active if appointment.conference else None

    # Get all active appointments for the same schedule, ordered by ID
    appointments = db.session.query(Appointment).filter(
        Appointment.schedule_id == appointment.schedule_id,
        Appointment.active == True
    ).order_by(Appointment.id).all()

    # Calculate the total number of active appointments
    total_appointments = len(appointments)

    # Determine the appointment's number in the order of scheduling (sorted by ID)
    appointment_number = next((index + 1 for index, a in enumerate(appointments) if a.id == appointment.id), None)

    # Determine the current queue position based on status and ID
    queued_appointments = [a for a in appointments if a.status in ['', 'queued', None]]
    queue_position = next((index + 1 for index, a in enumerate(queued_appointments) if a.id == appointment.id), None)

    # Return status as JSON, including the dynamic queue position
    return jsonify({
        'status': status,
        'total': total_appointments,
        'appointment_number': appointment_number,
        'queue_position': queue_position,
        'conference': conference,
        'live': live
    })

@consult_bp.route('/appointment/<int:appointment_id>/close', methods=['GET'])
def conclude_appointment(appointment_id):
    # Authorized clinician?
    appointment = db.session.query(Appointment).filter(
        Appointment.id == appointment_id,
    ).order_by(Appointment.id).first()
    
    appointment.conference.mark_close()
    return jsonify({}), 200

@consult_bp.route('/consultation/<int:conference_id>', methods=['GET', 'POST'])
@role_required('clinician')
def consultation(conference_id):
    conference = Conference.query.get(conference_id)
    conference.exclusive_open()
    if not conference:
        flash("Conference not found.", "error")
        return redirect(url_for('consult.staging'))

    return render_template('teleconsult.html', conference=conference, VIDEO_HOST_DOMAIN=current_app.config['VIDEO_HOST_DOMAIN'], VIDEO_HOST_URL=current_app.config['VIDEO_HOST_URL'])
