from flask_wtf import FlaskForm
from wtforms import StringField, TimeField, SubmitField, DateField, IntegerField, RadioField
from sqlalchemy import String
from wtforms.validators import Length, DataRequired
from cbridge.models import label_mapping, _validators, _valuesets
from cbridge.models.schedule import Appointment

class QueueControlForm(FlaskForm):
    class Meta:
        model = Appointment
    
    table = 'Appointment'

    patient = RadioField('Select patient', coerce=int)
    submit = SubmitField('Start Consultation')