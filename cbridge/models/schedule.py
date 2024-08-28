from .user import *
from .clinic import *
from sqlalchemy.orm import Mapped
from typing import List

from wtforms.validators import DataRequired, Length, Email, Optional, NumberRange

class Schedule(db.Model):
    __tablename__ = 'schedules'

    id = db.Column(db.Integer, primary_key=True)
    clinician_id = db.Column(db.Integer, db.ForeignKey('clinicians.id'))
    clinic_id = db.Column(db.Integer, db.ForeignKey('clinics.id'))
    date = db.Column(db.Date, nullable=False)
    max_bookings = db.Column(db.Integer, nullable=False)
    time_start = db.Column(db.Time, nullable=False)
    time_end = db.Column(db.Time, nullable=False)
    active = db.Column(db.Boolean, default=True)

    clinician: Mapped['Clinician'] = db.relationship(back_populates='schedules')
    clinic: Mapped['Clinic'] = db.relationship(back_populates='schedules')
    appointments: Mapped[List['Appointment']] = db.relationship(back_populates='schedule')

    @classmethod
    def custom_constraints(cls):
        return {
            'max_bookings': [NumberRange(min=1, max=50)],
            'password': [Length(min=3, max=30)],
            'email': [Optional(), Email()]
        }

class Appointment(db.Model):
    __tablename__ = 'appointments'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'))
    schedule_id = db.Column(db.Integer, db.ForeignKey('schedules.id'))
    status = db.Column(db.String(20), nullable=True)
    notes = db.Column(db.String(50), nullable=True)
    datetime = db.Column(db.DateTime, nullable=False)
    active = db.Column(db.Boolean, default=True)

    patient: Mapped['Patient'] = db.relationship(back_populates='appointments')
    schedule: Mapped['Schedule'] = db.relationship(back_populates='appointments')