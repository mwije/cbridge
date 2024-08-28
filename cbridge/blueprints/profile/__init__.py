from flask import Blueprint, render_template, session
from flask_login import login_required, current_user

from cbridge.models import *

profile_bp = Blueprint('profile', __name__)

@profile_bp.route('/', defaults={'selected_uid': None})
@profile_bp.route('/<selected_uid>')
@login_required
def index(selected_uid):
    if not selected_uid: current_user.uid
    userinfo = render_userview(selected_uid)
    roleinfo = render_roleview(selected_uid)

    return render_template('profile.html', userinfo=userinfo, roleinfo=roleinfo)
    


def render_userview(uid):
    fields = get_fieldvalues(User, current_user)
    return render_template('userinfo.html', fields=fields, title='')


def render_roleview(uid):
    roledata= {}
    match session.get('current_role'):
        case 'client':
            print('USER ROLE:', current_user.patient)
            if current_user.patient:
                  roledata = get_fieldvalues(Patient, current_user.patient)
        case 'clinician':
            print('USER ROLE:', current_user.clinician)
            if current_user.clinician:
                roledata = get_fieldvalues(Clinician, current_user.clinician)
        case default:
            error = f'invalid role { session.get('current_role') }'
            print(error)
            return error

    if roledata:
        
        return render_template('userinfo.html', fields=roledata, title=session.get('current_role') )
    else:
        return f'{ session.get('current_role') } role is not authorized for user: {current_user.username}'

def get_fieldvalues(table, instance):
    fielddata = {}
    print('x')
    for column in table.__table__.columns:
        print(column)
        fielddata[column.name] = getattr(instance, column.name)
        
    return fielddata