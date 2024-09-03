from ..extensions import db
from sqlalchemy.orm import Mapped
from typing import List, Dict, Any
import json

from .encounter import *

class Drug(db.Model):
    __tablename__ = 'drugs'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    substitute_id = db.Column(db.Integer, nullable=True)
    notes = db.Column(db.String(150), nullable=True)
    
    prescriptions: Mapped[List['Prescription']] = db.relationship(back_populates='drug')
    
    def instructions_get(self) -> List[Dict[str, Any]]:
        return json.loads(self.notes) if self.notes else []

    def instruction_add(self, instruction: str, clinician_id: int):
        instructions = self.instructions_get()
        instructions.append({
            'instruction': instruction,
            'clinician_id': clinician_id,
            'datetime': datetime.now()
        })
        self.notes = json.dumps(instructions)
        db.session.commit()

    def instruction_remove(self, instruction: str):
        instructions = self.instructions_get()
        instructions = [inst for inst in instructions if inst['instruction'] != instruction]
        self.notes = json.dumps(instructions)
        db.session.commit()

    def has_substitute(self) -> bool:
        return self.substitute_id is not None and self.substitute_id != 0

    def substitute_get(self):
        if self.has_substitute():
            return Drug.query.get(self.substitute_id)
        return None