from .user import *
from .clinic import *

class Schedule(db.Model):
    __tablename__ = 'schedules'

    id = db.Column(db.Integer, primary_key=True)
    clinician_id = db.Column(db.Integer, db.ForeignKey('clinicians.id'))
    clinic_id = db.Column(db.Integer, db.ForeignKey('clinics.id'))
    day_week = db.Column(db.String(10), nullable=False)
    max_bookings = db.Column(db.Integer, nullable=False)
    time_start = db.Column(db.Time, nullable=False)
    time_end = db.Column(db.Time, nullable=False)
    active = db.Column(db.Boolean, default=True)

    clinician = db.relationship('Clinician', back_populates='schedules')
    clinic = db.relationship('Clinic', back_populates='schedules')
    appointments = db.relationship('Appointment', back_populates='schedule')

class Appointment(db.Model):
    __tablename__ = 'appointments'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'))
    schedule_id = db.Column(db.Integer, db.ForeignKey('schedules.id'))
    status = db.Column(db.String(20), nullable=True)
    notes = db.Column(db.String(50), nullable=True)
    datetime = db.Column(db.DateTime, nullable=False)
    active = db.Column(db.Boolean, default=True)

    patient = db.relationship('Patient', back_populates='appointments')
    schedule = db.relationship('Schedule', back_populates='appointments')