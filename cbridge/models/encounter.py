from ..extensions import db
from sqlalchemy.orm import Mapped
from typing import List
from datetime import datetime

from .library import *

class Encounter(db.Model):
    __tablename__ = 'encounters'
    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'))
    datetime_start = db.Column(db.DateTime, nullable=False, default=datetime.utcnow())
    datetime_end = db.Column(db.DateTime, nullable=True)
    reason = db.Column(db.String(50), nullable=False)
    history = db.Column(db.String(250), nullable=True)
    findings = db.Column(db.String(250), nullable=True)
    plan_note = db.Column(db.String(250), nullable=True)
    plan_id = db.Column(db.Integer, db.ForeignKey('plans.id'))
    participants = db.Column(db.String(120), nullable=True) #JSON

    appointment: Mapped['Appointment'] = db.relationship(back_populates='encounter')
    plan: Mapped['Plan'] = db.relationship(back_populates='encounter')
    prescriptions: Mapped[List['Prescription']] = db.relationship(back_populates='encounter')

    def participants_get(self) -> List[Dict[str, datetime]]:
        return json.loads(self.participants) if self.participants else []

    def participants_add(self, uid: str):
        participants = self.participants_get()
        participants.append({uid: datetime.utcnow()})
        self.participants = json.dumps(participants)
        db.session.commit()

    def plan_generate(self) -> 'Plan':
        plan = Plan(file=self.plan_note, encounter=self)
        db.session.add(plan)
        db.session.commit()
        return plan

    def prescriptions_summary(self) -> List[Dict[str, Any]]:
        return [
            {
                'drug_id': prescription.drug.id,
                'drug_name': prescription.drug.name,
                'instruction': prescription.instruction,
                'duration': prescription.duration
            }
            for prescription in self.prescriptions
        ]

    def prescription_add(self, drug_id: int, instruction: str, duration: int) -> 'Prescription':
        prescription = Prescription(encounter_id=self.id, drug_id=drug_id, instruction=instruction, duration=duration)
        db.session.add(prescription)
        db.session.commit()
        return prescription

    def prescription_remove(self, prescription_id: int):
        Prescription.query.filter_by(id=prescription_id, encounter_id=self.id).delete()
        db.session.commit()

    def register(self, reason: str, history: str, findings: str, plan_note: str) -> 'Encounter':
        self.reason = reason
        self.history = history
        self.findings = findings
        self.plan_note = plan_note
        db.session.commit()
        return self

    def plan_generate_document(self) -> str:
        pdf_file = generate_pdf_from_plan(self.plan_note)  # This would be an external utility function to create a PDF.
        plan = Plan(file=pdf_file, encounter=self)
        db.session.add(plan)
        db.session.commit()
        return plan.url_generate()

    def plan_cancel(self):
        if self.plan:
            db.session.delete(self.plan)
            db.session.commit()

    def close(self):
        if self.appointment:
            self.appointment.status = 'completed'
            db.session.commit()

class Plan(db.Model):
    __tablename__ = 'plans'
    id = db.Column(db.Integer, primary_key=True)
    file = db.Column(db.String(50), nullable=False)
    url = db.Column(db.String(50), nullable=True)
    datetime_expiry = db.Column(db.DateTime, nullable=True)
    access_life = db.Column(db.Integer, default=10)

    encounter: Mapped['Encounter'] = db.relationship(back_populates='plan')

    def is_valid(self) -> bool:
        return self.datetime_expiry > datetime.utcnow() and self.access_life > 0

    def access_life_deduct(self):
        if self.access_life > 0:
            self.access_life -= 1
            db.session.commit()

    def url_generate(self) -> str:
        if not self.is_valid():
            return None
        self.url = generate_secure_url(self.file)  # This would be an external utility function to create a secure URL.
        db.session.commit()
        return self.url

class Prescription(db.Model):
    __tablename__ = 'prescriptions'
    id = db.Column(db.Integer, primary_key=True)
    encounter_id = db.Column(db.Integer, db.ForeignKey('encounters.id'))
    drug_id = db.Column(db.Integer, db.ForeignKey('drugs.id'))
    instruction = db.Column(db.String(50), nullable=False)
    duration = (db.Integer)

    encounter: Mapped['Encounter'] = db.relationship(back_populates='prescriptions')
    drug: Mapped['Drug'] = db.relationship(back_populates='prescriptions')

    def date_end(self) -> datetime:
        return self.encounter.datetime_start + timedelta(days=self.duration)

    def is_ongoing(self, datetime_past: datetime) -> bool:
        return datetime_past <= self.date_end()

    def drug_info_get(self) -> Dict[str, Any]:
        return {
            'drug_id': self.drug.id,
            'drug_name': self.drug.name,
            'instruction': self.instruction,
            'duration': self.duration
        }