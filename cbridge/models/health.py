from sqlalchemy.orm import Mapped
from typing import List

from .user import *

class Allergy(db.Model):
    __tablename__ = 'allegies'
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'))
    allergen = db.Column(db.String(50), nullable=False)
    datetime = db.Column(db.DateTime, nullable=False, default=datetime.utcnow())
    notes = db.Column(db.String(150), nullable=True)
    
    patient: Mapped['Patient'] = db.relationship(back_populates='allergies')

    def summary(self) -> Dict[str, Any]:
        return {
            'allergy_id': self.id,
            'allergen': self.allergen,
            'datetime': self.datetime,
            'notes': self.notes
        }

    def register(self, allergen: str, notes: str = None):
        allergy = Allergy(patient_id=self.patient_id, allergen=allergen, notes=notes)
        db.session.add(allergy)
        db.session.commit()

    def resolve(self, allergy_id: int):
        Allergy.query.filter_by(id=allergy_id, patient_id=self.patient_id).delete()
        db.session.commit()

class Problem(db.Model):
    __tablename__ = 'problems'
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'))
    problem = db.Column(db.String(50), nullable=False)
    datetime_set = db.Column(db.DateTime, nullable=False, default=datetime.utcnow())
    datetime_resolved = db.Column(db.DateTime, nullable=False, default=datetime.utcnow())

    notes = db.Column(db.String(150), nullable=True)
    
    patient: Mapped['Patient'] = db.relationship(back_populates='problems')

    def is_valid(self) -> bool:
        return self.datetime_removed is None or self.datetime_removed > datetime.utcnow()

    def register(self, problem: str, notes: str = None):
        problem = Problem(patient_id=self.patient_id, problem=problem, notes=notes)
        db.session.add(problem)
        db.session.commit()

    def summary(self, past_records: bool = False) -> List[Dict[str, Any]]:
        if past_records:
            problems = Problem.query.filter_by(patient_id=self.patient_id).all()
        else:
            problems = Problem.query.filter_by(patient_id=self.patient_id).filter(Problem.datetime_removed.is_(None) | (Problem.datetime_removed > datetime.utcnow())).all()

        return [{
            'problem_id': problem.id,
            'problem': problem.problem,
            'datetime_set': problem.datetime,
            'datetime_resolved': problem.datetime_removed,
            'notes': problem.notes
        } for problem in problems]

    def resolve(self):
        self.datetime_removed = datetime.utcnow()
        db.session.commit()

    def unresolve(self):
        self.datetime_removed = None
        db.session.commit()
        