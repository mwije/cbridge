from .user import *
from .clinic import *
from sqlalchemy.orm import Mapped
from typing import List
import json

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
    log = db.Column(db.String(100), nullable=True, default='{}')
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
        # Deserialize the current log into a dictionary
        if self.log == None or self.log == '':
            log_dict = {}
        else:
            log_dict = json.loads(self.log)
            
        # Update the dictionary with the new uid and timestamp
        current_datetime = datetime.now() # Get the current datetime in ISO 8601 format
        log_dict[str(uid)] = current_datetime
        
        # Serialize the updated dictionary back into a JSON string
        self.log = json.dumps(log_dict)
        db.session.commit()
        
    def patients_last_seen_get(self):
        # Deserialize the log into a dictionary and return it
        return json.loads(self.log)

class Appointment(db.Model):
    __tablename__ = 'appointments'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'))
    schedule_id = db.Column(db.Integer, db.ForeignKey('schedules.id'))
    status = db.Column(db.String(20), nullable=True)
    notes = db.Column(db.String(50), nullable=True)
    datetime = db.Column(db.DateTime, nullable=False, default=datetime.now())
    active = db.Column(db.Boolean, default=True)

    patient: Mapped['Patient'] = db.relationship(back_populates='appointments')
    schedule: Mapped['Schedule'] = db.relationship(back_populates='appointments')
    conference: Mapped['Conference'] = db.relationship(back_populates='appointment')
    encounter: Mapped['Encounter'] = db.relationship(back_populates='appointment')

    def complete(self):
        if self:
            self.status = 'completed'

    def cancel(self):
        if self:
            self.status = 'cancelled'

    def start(self):
        if self:
            self.status = 'ongoing'
            
    def queue(self):
        if self:
            self.status = 'queued'

class Conference(db.Model):
    __tablename__ = 'conferences'

    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'))
    url = db.Column(db.String(50), nullable=True)
    datetime = db.Column(db.DateTime, nullable=False, default=datetime.now())
    active = db.Column(db.Boolean, default=False)

    appointment: Mapped['Appointment'] = db.relationship(back_populates='conference')

    def mark_open(self):
        self.active = True
        self.datetime = datetime.now()
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