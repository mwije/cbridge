from flask import Blueprint, render_template, request, session, current_app, url_for
from flask_login import current_user
from cbridge.decorators import role_required
from cbridge.models.schedule import *

from ..consult.jwt import generate_jwt

emr_fe = Blueprint('emr_fe', __name__)

@emr_fe.route('/consultation/emr.js')
@role_required('clinician')
def emrjs():
    appointment_id = request.args.get('id')
    appointment = Appointment.query.filter_by(id=appointment_id).first();

    if session['current_role'] == 'clinician':
        lobby_url = url_for('consult.staging')
    else:
        lobby_url = url_for('consult.lobby')

    jwt = generate_jwt(user=current_user, conference=appointment.conference)

    return render_template('emr/emr.js',
        appointment=appointment,
        conference=appointment.conference,
        patient=appointment.patient,
        jwt=jwt,
        lobby_url=lobby_url,
        VIDEO_HOST_DOMAIN=current_app.config['VIDEO_HOST_DOMAIN'],
        VIDEO_HOST_URL=current_app.config['VIDEO_HOST_URL']
        )