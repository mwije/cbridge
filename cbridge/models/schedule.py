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
    
    def appointments_by_status_count(self, status):
        return sum(1 for appointment in self.appointments if appointment.status == status)
    
    def appointments_total_count(self):
        return len(self.appointments)

    def session_start(self):
        for appointment in self.appointments:
            if appointment.status in ['', 'ongoing', None]:
                appointment.status = 'queued'
                

    def session_stop(self):
        for appointment in self.appointments:
            if appointment.status in ['queued', 'ongoing']:
                appointment.status = ''
    
    def patients_last_seen_update(self, uid):
        current_datetime = datetime.now().isoformat()  # Get the current datetime in ISO 8601 format
        self.notes[uid] = current_datetime
    
    def patients_last_seen_get(self):
        return json.dumps(self.notes)

class Appointment(db.Model):
    __tablename__ = 'appointments'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'))
    schedule_id = db.Column(db.Integer, db.ForeignKey('schedules.id'))
    status = db.Column(db.String(20), nullable=True)
    notes = db.Column(db.String(50), nullable=True)
    datetime = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    active = db.Column(db.Boolean, default=True)

    patient: Mapped['Patient'] = db.relationship(back_populates='appointments')
    schedule: Mapped['Schedule'] = db.relationship(back_populates='appointments')
    conference: Mapped['Conference'] = db.relationship(back_populates='appointment')



class Conference(db.Model):
    __tablename__ = 'conferences'

    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'))
    url = db.Column(db.String(50), nullable=True)
    datetime = db.Column(db.DateTime, nullable=False, default=datetime.utcnow())
    active = db.Column(db.Boolean, default=False)

    appointment: Mapped['Appointment'] = db.relationship(back_populates='conference')

    def mark_open(self):
        self.active = True
        self.datetime = datetime.utcnow()
        db.session.commit()
    
    def mark_close(self):
        self.active = False
        db.session.commit()


    def exclusive_open(self):
        # Ensure only this conference is open for schedule
        
        current_appointment = db.session.query(Appointment).get(self.appointment_id)
        schedule_id = current_appointment.schedule_id

        # Query all conferences related to the same schedule_id except the current one
        other_conferences = db.session.query(Conference).join(Appointment).filter(
            Appointment.schedule_id == schedule_id,
            Conference.id != self.id
        ).all()

        # Deactivate all the other conferences
        for conference in other_conferences:
            conference.active = False

        # Ensure the current conference is active
        self.active = True

        # Commit the transaction
        db.session.commit()