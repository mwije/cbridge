from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from cbridge.decorators import role_required, login_required
from cbridge.models.user import *
from cbridge.models.encounter import *
from cbridge.extensions import db, bcrypt

from .forms import *
from .jwt import generate_jwt
import random, string
from datetime import datetime, date

consult_bp = Blueprint('consult', __name__)

@consult_bp.route('/staging', methods=['GET', 'POST'])
@consult_bp.route('/staging/', methods=['GET', 'POST'])
@consult_bp.route('/staging/<int:schedule_id>', methods=['GET', 'POST'])
@role_required('clinician')
def staging(schedule_id=None):
    thedate = datetime.today().date()

    # All schedules of clinician
    schedules = Schedule.query.filter(
        Schedule.clinician_id==current_user.clinician.id,
        Schedule.date >= thedate
    ).order_by(Schedule.date).all()
    
    if schedule_id == None:
        # Set view for current date/closest schedule date
        if schedules:
            nearest_schedule = min(schedules, key=lambda x: abs(x.date - thedate))
            schedule_id = nearest_schedule.id
        else:
            flash('You have no schedules. Create some')
            return redirect(url_for('book.clinicianschedule'))
    # All appointments for selected schedule
    appointments = db.session.query(Appointment).filter(
        Appointment.schedule_id==schedule_id
    ).order_by(Appointment.id.asc()).all()

    if request.method == 'POST':
        # Find the selected appointment
        
        appointment_id = request.form.get('selected_appointment')
        
        selected_appointment = Appointment.query.filter(Appointment.id==appointment_id).first()
   
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
    
    return render_template('lobby_clinician.html', schedules=schedules, appointments=appointments, thedate=thedate, schedule_id=schedule_id)

@consult_bp.route('/lobby', methods=['GET', 'POST'])
@role_required('client')
def lobby():
    thedate = datetime.today().date()
    appointments = db.session.query(Appointment).join(Schedule).filter(
        Appointment.patient_id == current_user.patient.id,
        Appointment.active == True
    ).order_by(Appointment.id.desc()).all()

    if not appointments:
        flash("No appointments for user. Make a booking")
        return redirect(url_for('book.booking'))
    appointment = appointments[0]
    # TODO: what if multiple appointments are pending

    clinician = db.session.query(Clinician).join(User).filter(
        Clinician.id == appointment.schedule.clinician_id
    )

    return render_template('lobby_patient.html', thedate=thedate, appointment=appointment, clinician=clinician)

@consult_bp.route('/appointment/<int:appointment_id>/status', methods=['GET'])
@login_required
def get_appointment_status(appointment_id):
    # Retrieve the appointment record
    appointment = db.session.query(Appointment).filter(
        Appointment.id == appointment_id,
        Appointment.active == True
    ).first()

    if not appointment:
        return jsonify({'error': 'Appointment not found or inactive'}), 404

    # Update last seen
    appointment.schedule.patients_last_seen_update(current_user.uid)
    # Get the status and conference URL
    status = appointment.status
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
    scheduled_appointments = [a for a in appointments if a.status in ['', None]]
    queued_appointments = [a for a in appointments if a.status in ['queued']]
    completed_appointments = [a for a in appointments if a.status in ['completed']]
    queue_position = next((index + 1 for index, a in enumerate(queued_appointments) if a.id == appointment.id), None)

    # Return status as JSON, including the dynamic queue position
    return jsonify({
        'appointment_status': status,
        'total_appointments': total_appointments,
        'scheduled_appointments': len(scheduled_appointments),
        'queued_appointments': len(queued_appointments),
        'completed_appointments': len(completed_appointments),
        'appointment_number': appointment_number,
        'queue_position': queue_position,
        'conference': conference,
        'live': live
    })

@consult_bp.route('/appointment/<int:appointment_id>/plan', methods=['GET', 'POST'])
@role_required('clinician')
def generate_plan(appointment_id):
    # Authorized clinician?
    appointment = db.session.query(Appointment).filter(
        Appointment.id == appointment_id,
    ).order_by(Appointment.id).first()

    if not appointment:
        return jsonify({'success': False, 'message': 'Appointment not found'}), 404

    # Ensure valid json
    if request.method == 'POST':
        data = request.get_json()
        # Ensure valid JSON and required fields
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        required_fields = ['reason', 'history', 'findings', 'plan_note']
        missing_fields = [field for field in required_fields if field not in data or not data[field]]
        
        if missing_fields:
            return jsonify({'success': False, 'message': f'Missing fields: {", ".join(missing_fields)}'}), 400
        
        #try:
        # Start a transaction
        
        # Clean up existing Encounter and related records for this appointment
        existing_encounter = Encounter.query.filter_by(appointment_id=appointment_id).first()
        if existing_encounter:
            # Delete all prescriptions related to the encounter
            Prescription.query.filter_by(encounter_id=existing_encounter.id).delete()
            # Delete the existing encounter
            db.session.delete(existing_encounter)
            

        # Create a new encounter
        encounter = Encounter(
            appointment_id=appointment_id,
            datetime_start=datetime.utcnow(),
            datetime_end=datetime.utcnow(),
            reason=data['reason'],
            history=data['history'],
            findings=data['findings'],
            plan_note=data['plan_note']
        )
        
        db.session.add(encounter)
        db.session.commit()

        # Add new prescriptions
        prescriptions = data.get('prescriptions', [])
        for pres in prescriptions:
            encounter.prescription_add(
                drug_id=pres['drug_id'],
                instruction=pres['instruction'],
                duration=pres['duration'],
            )

        db.session.commit()

        # Generate the plan and create a document TODOS
        existing_encounter = Encounter.query.filter_by(appointment_id=appointment_id).first()
        plan_url = encounter.plan_generate_document()

        # If all operations succeed, commit the transaction
        

        return jsonify({'success': True, 'document_url': plan_url})
        '''
        except Exception as e:
            # If there is an error, rollback the transaction
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)}), 500
'''
@consult_bp.route('/appointment/<int:appointment_id>/sign', methods=['GET'])
@role_required('clinician')
def sign_prescription(appointment_id):
    # Authorized clinician?
    appointment = db.session.query(Appointment).filter(
        Appointment.id == appointment_id,
    ).order_by(Appointment.id).first()
    
    ## add datetime_end for encounter
    ## generate document and forward it
    return jsonify({}), 200

@consult_bp.route('/appointment/<int:appointment_id>/close', methods=['GET'])
@role_required('clinician')
def conclude_appointment(appointment_id):
    # Authorized clinician?
    appointment = db.session.query(Appointment).filter(
        Appointment.id == appointment_id,
    ).order_by(Appointment.id).first()
    
    appointment.conference.mark_close()
    return jsonify({}), 200



@consult_bp.route('/consultation/<int:conference_id>', methods=['GET', 'POST'])
@role_required('clinician', 'client')
def consultation(conference_id):
    conference = Conference.query.get(conference_id)
    conference.exclusive_open()
    jwt = generate_jwt(user=current_user, conference=conference)
    
    if session['current_role'] == 'clinician':
        lobby_url = url_for('consult.staging')
    else:
        lobby_url = url_for('consult.lobby')

    if not conference:
        flash("Conference not found.", "error")
        return redirect(url_for('consult.staging'))

    return render_template('teleconsult.html',
        conference=conference,
        appointment=conference.appointment,
        patient=conference.appointment.patient,
        jwt=jwt,
        lobby_url=lobby_url,
        VIDEO_HOST_DOMAIN=current_app.config['VIDEO_HOST_DOMAIN'],
        VIDEO_HOST_URL=current_app.config['VIDEO_HOST_URL']
        )

@consult_bp.route('/schedule/<int:schedule_id>/session', methods=['POST'])
@role_required('clinician')
def set_current_schedule(schedule_id):
    data = request.json
    active = data.get('active', False)
    schedule = Schedule.query.filter(Schedule.id==schedule_id).first()

    schedule_old = None
    if session.get('current_schedule'):
        schedule_old = Schedule.query.filter(Schedule.id==session['current_schedule']).first()

    if active:
        if schedule.appointments:
            session['current_schedule'] = schedule.id
            schedule.session_start()
            if schedule_old: schedule_old.session_stop()
            
            db.session.commit()
            
            return jsonify(success=True)
            
        else:
            
            return jsonify(success=False), 400
    else:
        session['current_schedule'] = None
        schedule.session_stop()
        db.session.commit()
        return jsonify(success=True)

@consult_bp.route('/schedule/<int:schedule_id>/status', methods=['GET'])
@role_required('clinician')
def get_schedule_status(schedule_id):
    # Retrieve the appointment record
    schedule = db.session.query(Schedule).filter(
        Schedule.id == schedule_id,
        Schedule.active == True
    ).first()

    if not schedule:
        return jsonify({'error': 'Schedule not found or inactive'}), 404

    # Get last seen users
    last_seen = schedule.patients_last_seen_get()
    
    # Get all active appointments for the same schedule, ordered by ID
    appointments = db.session.query(Appointment).filter(
        Appointment.schedule_id == schedule_id,
        Appointment.active == True
    ).order_by(Appointment.id).all()

    # Calculate the total number of active appointments
    total_appointments = len(appointments)

    # Determine the current queue position based on status and ID
    scheduled_appointments = [a for a in appointments if a.status in ['', None]]
    queued_appointments = [a for a in appointments if a.status in ['queued']]
    completed_appointments = [a for a in appointments if a.status in ['completed']]

    # Return status as JSON, including the dynamic queue position
    return jsonify({
        'last_seen_users': last_seen,
        'total_appointments': total_appointments,
        'scheduled_appointments': len(scheduled_appointments),
        'queued_appointments': len(queued_appointments),
        'completed_appointments': len(completed_appointments),
    })