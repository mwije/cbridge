from flask_wtf import FlaskForm
from wtforms import StringField, TimeField, SubmitField, DateField, IntegerField, RadioField
from sqlalchemy import String
from wtforms.validators import Length, DataRequired
from cbridge.models import label_mapping, _validators, _valuesets
from cbridge.models.schedule import Schedule

class NewScheduleForm(FlaskForm):
    class Meta:
        model = Schedule
    
    table = 'Schedule'

    date = DateField(validators = _validators[table]['date'])
    max_bookings = IntegerField(validators = _validators[table]['max_bookings'])
    time_start = TimeField(validators = _validators[table]['time_start'])
    time_end = TimeField(validators = _validators[table]['time_end'])
    
    submit = SubmitField('Register')
