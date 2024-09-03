from flask import Blueprint, render_template
from cbridge.models.encounter import *

public_bp = Blueprint('public', __name__)

@public_bp.route('/prescription/verify/<url>', methods=['GET'])
def verifyprescription(url=''):
    plan = Plan.query.filter_by(url=url).first()
    file= plan.file
    if not file.startswith('/'):
        file = '/' + file
    return render_template('file_preview.html', title='Verify prescription', file=file)

