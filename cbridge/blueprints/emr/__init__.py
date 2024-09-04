from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from cbridge.decorators import role_required
from cbridge.models.user import *
from cbridge.models.library import *

from .frontend import *
from cbridge.extensions import db, bcrypt

emr_bp = Blueprint('emr', __name__)

@emr_bp.route('/patient/<int:patient_id>/demographics')
def emr_demographics(patient_id):
    # Render demographics view
    patient = Patient.query.filter_by(id=patient_id)
    return render_template('emr/patient_demographics.html', patient=patient)

@emr_bp.route('/emr/<int:appointment_id>/presentation', methods=['GET'])
@login_required
def emr_presentation(appointment_id):
    # Render presentation view
    appointment = Appointment.query.filter_by(id=appointment_id)
    encounter = appointment.encounter
    return render_template('emr/presentation.html', encounter=encounter)

@emr_bp.route('/emr/<int:appointment_id>/presentation', methods=['POST'])
@login_required
def emr_presentation_update(appointment_id):
    # Commits presentation data
    data = request.get_json()
    appointment = Appointment.query.filter_by(id=appointment_id)
    encounter = appointment.encounter or Encounter(appointment_id=appointment.id)
    encounter.reason = data.get('reason')
    encounter.history = data.get('history')
    encounter.findings = data.get('findings')
    db.session.add(encounter)
    db.session.commit()
    return jsonify({'status': 'success', 'message': 'Presentation details updated.'}), 200

@emr_bp.route('/emr/<int:appointment_id>/management', methods=['GET'])
@login_required
def emr_management(appointment_id):
    # Render management view
    appointment = Appointment.query.filter_by(id=appointment_id)
    patient = appointment.patient
    encounter = appointment.encounter
    today = datetime.now()
    ongoing_prescriptions = [
        prescription for encounter in patient.encounter_list()
        for prescription in encounter.prescriptions
        if prescription.is_ongoing(today)
    ]
    return render_template('emr/management.html', appointment=appointment, encounter=encounter, ongoing_prescriptions=ongoing_prescriptions)

@emr_bp.route('/emr/drugs/search', methods=['GET'])
@login_required
def search_drugs():
    # Get matching drugs for autocompletion
    query = request.args.get('q', '')
    drugs = Drug.query.filter(Drug.name.ilike(f'%{query}%')).all()
    results = [{'id': drug.id, 'name': drug.name} for drug in drugs]
    
    return jsonify(results)

@emr_bp.route('/emr/drugs/create', methods=['POST'])
@login_required
def create_or_get_drug():
    drug_name = request.json.get('name')

    if not drug_name:
        return jsonify({"error": "Drug name is required"}), 400

    # Check if a drug with the same name already exists
    existing_drug = Drug.query.filter_by(name=drug_name).first()
    if existing_drug:
        return jsonify({"id": existing_drug.id, "name": existing_drug.name}), 200

    # Create a new drug
    new_drug = Drug(name=drug_name)

    try:
        db.session.add(new_drug)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to create new drug"}), 500

    return jsonify({"id": new_drug.id, "name": new_drug.name}), 201

@emr_bp.route('/emr/drugs/<int:drug_id>/instructions', methods=['GET'])
@login_required
def get_drug_instructions(drug_id):
    # Get drug instructions
    drug = Drug.query.filter_by(id=drug_id).first()
    instructions = drug.instructions_get()
    print(instructions)
    return jsonify(instructions)

@emr_bp.route('/emr/<int:appointment_id>/management', methods=['POST'])
@login_required
def emr_management_update(appointment_id):
    data = request.get_json()
    appointment = Appointment.query.filter_by(id=appointment_id)
    encounter = appointment.encounter or Encounter(appointment_id=appointment.id)
    
    # Update or discontinue existing prescriptions
    for presc in data.get('existing_prescriptions', []):
        prescription = Prescription.query.get(presc['id'])
        if not presc['continue']:
            db.session.delete(prescription)
    
    # Add new prescriptions
    for presc in data.get('new_prescriptions', []):
        prescription = Prescription(
            encounter_id=encounter.id,
            drug_id=presc['drug_id'],
            instruction=presc['instruction'],
            duration=presc['duration']
        )
        db.session.add(prescription)
    
    # Update management notes
    encounter.plan_note = data.get('management_notes')
    db.session.add(encounter)
    db.session.commit()
    
    return jsonify({'status': 'success', 'message': 'Management details saved successfully.'})

@emr_bp.route('/patient/<int:patient_id>/allergies', methods=['GET', 'POST'])
def allergies(patient_id):
    if request.method == 'POST':
        allergy = Allergy(description=request.form['description'], patient_id=patient_id)
        db.session.add(allergy)
        db.session.commit()
        return redirect(url_for('emr.allergies', patient_id=patient_id))
    allergies = Allergy.query.filter_by(patient_id=patient_id).all()
    return render_template('allergies.html', allergies=allergies)

@emr_bp.route('/patient/<int:patient_id>/drugs', methods=['GET', 'POST'])
def drugs(patient_id):
    if request.method == 'POST':
        # Update or adjust the drug regimen logic here
        drug = Drug.query.filter_by(id=request.form['drug_id']).first()
        drug.regimen = request.form['regimen']
        db.session.commit()
        return redirect(url_for('emr.drugs', patient_id=patient_id))
    drugs = Drug.query.filter_by(patient_id=patient_id).all()
    return render_template('drugs.html', drugs=drugs)


@emr_bp.route('/patient/<int:patient_id>/management-plan', methods=['GET', 'POST'])
def management_plan(patient_id):
    if request.method == 'POST':
        plan = ManagementPlan.query.filter_by(patient_id=patient_id).first()
        plan.description = request.form['description']
        db.session.commit()
        # Handle the authorization checkbox
        if 'authorize' in request.form:
            plan.authorized = True
            db.session.commit()
            # Generate prescription logic here
        return redirect(url_for('emr.management_plan', patient_id=patient_id))
    plan = ManagementPlan.query.filter_by(patient_id=patient_id).first()
    return render_template('management_plan.html', plan=plan)

@emr_bp.route('/patient/<int:patient_id>/summary/json')
@role_required('clinician')
def patient_summary_json(patient_id):
    patient = Patient.query.filter_by(id=patient_id).first()
    
    # Constructing the patient summary as a dictionary
    patient_summary = {
        'name': patient.user.name,
        'age': patient.user.age(),
        'sex': patient.user.sex,
        #'medical_history': patient.medical_history,
        #'allergies': patient.allergies,
        #'current_medications': patient.current_medications,
        #'last_visit': patient.last_visit.strftime('%Y-%m-%d') if patient.last_visit else 'N/A'
    }
    
    return jsonify(patient_summary)