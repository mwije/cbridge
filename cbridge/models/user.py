from ..extensions import db
from flask_login import UserMixin
from datetime import datetime, date
from sqlalchemy.orm import Mapped
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Dict, Any

from wtforms.validators import DataRequired, Length, Email, Optional

from .schedule import *

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    uid = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)
    
    name = db.Column(db.String(120), nullable=False)
    date_birth = db.Column(db.Date, nullable=False)
    identification = db.Column(db.String(15), nullable=True)
    sex = db.Column(db.String(6), nullable=True)

    telephone = db.Column(db.String(16), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    address = db.Column(db.String(120), nullable=False)

    date_joined = db.Column(db.Date, default=datetime.now())
    active = db.Column(db.Boolean, default=True)

    @classmethod
    def columns(self):
        return User.__table__.columns

    @classmethod
    def columnsNotNullable(self):
        return [col.name for col in User.__table__.columns if not col.nullable]

    def __repr__(self):
            return f'<User: {self.username}, Role: {self.role}>'

    def get_id(self):
        return self.uid

    def age(self):
        today = date.today()
        if self.date_birth:
            age = today.year - self.date_birth.year - ((today.month, today.day) < (self.date_birth.month, self.date_birth.day))
        else:
            age = None
        return age
    

    @classmethod
    def custom_constraints(cls):
        return {
            'username': [Length(min=3, max=50)],
            'password': [Length(min=3, max=30)],
            'email': [Optional(), Email()]
        }
    
    @classmethod
    def valueset(cls):
        return {
            'role': ['client', 'clinician', 'helper', 'admin', 'dev'],
            'active': [True, False]
        }
    
   
    roles = db.relationship('Role', secondary='user_roles', back_populates='users')
    patient: Mapped['Patient'] = db.relationship(back_populates='user', lazy='joined')
    clinician: Mapped['Clinician'] = db.relationship(back_populates='user', lazy='joined')
    helper: Mapped['Helper'] = db.relationship(back_populates='user', uselist=False)
 

    def has_role(self, role):
        return bool (
            Role.query
            .join(Role.users)
            .filter(User.uid == self.uid)
            .filter(Role.slug == role)
            .count() == 1
        )
    
    def get_roles(self):
        return [role.slug for role in self.roles]

    def role_assign(self, role_slug):
        try:
            # Find the role by slug
            role = Role.query.filter_by(slug=role_slug).first()
            if not role:
                return f"Role '{role_slug}' not found."

            # Check if the role is already assigned to the user
            user_role = UserRole.query.filter_by(uid=self.uid, role_id=role.id).first()
            if user_role:
                return f"User already has the role '{role_slug}'."

            # Assign the role to the user
            new_user_role = UserRole(uid=self.uid, role_id=role.id)
            db.session.add(new_user_role)

            # Additional logic based on role_slug
            if role_slug == 'client':
                new_patient = Patient(uid=self.uid)
                db.session.add(new_patient)
            elif role_slug == 'clinician':
                new_clinician = Clinician(uid=self.uid)
                db.session.add(new_clinician)


            db.session.commit()
            return f"Role '{role_slug}' assigned successfully."

        except SQLAlchemyError as e:
            db.session.rollback()  # Rollback in case of any error
            return f"Error assigning role: {str(e)}"

    def role_remove(self, role_slug):
        try:
            # Find the role by slug
            role = Role.query.filter_by(slug=role_slug).first()
            if not role:
                return f"Role '{role_slug}' not found."

            # Check if the user has the role
            user_role = UserRole.query.filter_by(uid=self.uid, role_id=role.id).first()
            if not user_role:
                return f"User does not have the role '{role_slug}'."

            # Remove the role from the user
            db.session.delete(user_role)
            db.session.commit()
            return f"Role '{role_slug}' removed successfully."

        except SQLAlchemyError as e:
            db.session.rollback()  # Rollback in case of any error
            return f"Error removing role: {str(e)}"

class Role(db.Model):
    __tablename__ = 'roles'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(10), nullable=False)
    slug = db.Column(db.String(10), nullable=False, unique=True)

    users = db.relationship('User', secondary='user_roles', back_populates='roles')

class UserRole(db.Model):
    __tablename__ = 'user_roles'
    uid = db.Column(db.Integer, db.ForeignKey('users.uid'), primary_key=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), primary_key=True)

class Patient(db.Model):
    __tablename__ = 'patients'
    id = db.Column(db.Integer, primary_key=True)
    note = db.Column(db.String(50), nullable=True)
    uid = db.Column(db.Integer, db.ForeignKey('users.uid'))


    user: Mapped['User'] = db.relationship(back_populates='patient')
    appointments: Mapped[List['Appointment']] = db.relationship(back_populates='patient')
    allergies: Mapped[List['Allergy']] = db.relationship(back_populates='patient')
    problems: Mapped[List['Problem']] = db.relationship(back_populates='patient')

    def problems_json(self, past_records: bool = False) -> List[Dict[str, Any]]:
        return Problem.query.filter_by(patient_id=self.id).summary(past_records=past_records)

    def allergies_json(self) -> List[Dict[str, Any]]:
        return [allergy.summary() for allergy in self.allergies]

    def appointment_list(self, status: str = None) -> List['Appointment']:
        query = Appointment.query.filter_by(patient_id=self.id)
        if status:
            query = query.filter_by(status=status)
        return query.all()

    def encounter_list(self) -> List['Encounter']:
        appointments = self.appointment_list(status='completed')
        return [appointment.encounter for appointment in appointments if appointment.encounter]

    def encounter_latest(self):
        encounters = self.encounter_list()
        return max(encounters, key=lambda e: e.id, default=None)

    def appointment_latest(self):
        appointments = self.appointment_list()
        return max(appointments, key=lambda a: a.id, default=None)

class Clinician(db.Model):
    __tablename__ = 'clinicians'
    id = db.Column(db.Integer, primary_key=True)
    note = db.Column(db.String(50), nullable=True)
    uid = db.Column(db.Integer, db.ForeignKey('users.uid'), unique=True, nullable=False)
    professional_name = db.Column(db.String(50), nullable=True)
    specialty = db.Column(db.String(50), nullable=True)
    qualifications = db.Column(db.String(50), nullable=True)
    registration = db.Column(db.String(50), nullable=True)
    contact = db.Column(db.String(25), nullable=True)

    user: Mapped['User'] = db.relationship(back_populates='clinician')
    schedules: Mapped[List['Schedule']] = db.relationship(back_populates='clinician')
    
class Helper(db.Model):
    __tablename__ = 'helpers'
    id = db.Column(db.Integer, primary_key=True)
    note = db.Column(db.String(50), nullable=False)
    uid = db.Column(db.Integer, db.ForeignKey('users.uid'))

    user: Mapped['User'] = db.relationship(back_populates='helper')