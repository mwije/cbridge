from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from cbridge.decorators import role_required
from cbridge.models.user import *
from cbridge.extensions import db, bcrypt

emr_bp = Blueprint('emr', __name__)

@emr_bp.route('/patient/<int:patient_id>/demographics')
def demographics(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    return render_template('patient_demographics.html', patient=patient)

@emr_bp.route('/patient/<int:patient_id>/complaints', methods=['GET', 'POST'])
def complaints(patient_id):
    if request.method == 'POST':
        complaint = Complaint(reason=request.form['reason'], clinical_notes=request.form['clinical_notes'], patient_id=patient_id)
        db.session.add(complaint)
        db.session.commit()
        return redirect(url_for('emr.complaints', patient_id=patient_id))
    complaints = Complaint.query.filter_by(patient_id=patient_id).all()
    return render_template('complaints.html', complaints=complaints)

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

@emr_bp.route('/patient/<int:patient_id>/lab-reports', methods=['GET', 'POST'])
def lab_reports(patient_id):
    if request.method == 'POST':
        # Logic to upload/update lab reports
        lab_report = LabReport(description=request.form['description'], patient_id=patient_id)
        db.session.add(lab_report)
        db.session.commit()
        return redirect(url_for('emr.lab_reports', patient_id=patient_id))
    lab_reports = LabReport.query.filter_by(patient_id=patient_id).all()
    return render_template('lab_reports.html', lab_reports=lab_reports)

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