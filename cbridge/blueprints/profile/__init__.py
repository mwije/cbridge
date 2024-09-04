from flask import Blueprint, render_template, session
from flask_login import login_required, current_user
from cbridge.models import User, Patient, Clinician

profile_bp = Blueprint('profile', __name__)

@profile_bp.route('/', defaults={'selected_uid': None})
@profile_bp.route('/<selected_uid>')
@login_required
def index(selected_uid):
    if not selected_uid:
        selected_uid = current_user.uid

    user = User.query.get(selected_uid)
    roleinfo = get_role_info(selected_uid)

    return render_template('profile.html', userinfo=user, roleinfo=roleinfo)



def get_role_info(uid):
    roleinfo = {}
    current_role = session.get('current_role', '')

    if current_role == 'client':
        patient = Patient.query.filter_by(uid=uid).first()
        if patient:
            roleinfo = {
                'Note': patient.note,
                'Appointments': len(patient.appointment_list()),  # Example
                # Add more patient-specific fields as needed
            }
    elif current_role == 'clinician':
        clinician = Clinician.query.filter_by(uid=uid).first()
        if clinician:
            roleinfo = {
                'Professional Name': clinician.professional_name,
                'Specialty': clinician.specialty,
                'Qualifications': clinician.qualifications,
                'Registration': clinician.registration,
                'Contact': clinician.contact,
                'Schedules': len(clinician.schedules),  # Example
                # Add more clinician-specific fields as needed
            }
    # Add other roles as needed

    return roleinfo
