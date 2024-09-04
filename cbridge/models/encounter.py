from ..extensions import db, abs_to_rel_path, base_url
from sqlalchemy.orm import Mapped
from typing import List
from datetime import datetime
from cbridge.extensions import get_unique_filename, generate_qr_code
from flask import current_app, render_template, request
from weasyprint import HTML


from .library import *

class Encounter(db.Model):
    __tablename__ = 'encounters'
    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'))
    datetime_start = db.Column(db.DateTime, nullable=False, default=datetime.now())
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
        participants.append({uid: datetime.now()})
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

    def prescription_add(self, drug_id: int, instruction: str, duration: int, encounter_id: int =None) -> 'Prescription':
        if not encounter_id:
            encounter_id = self.id
        prescription = Prescription(encounter_id=encounter_id, drug_id=drug_id, instruction=instruction, duration=duration)
        db.session.add(prescription)
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
        # Assign a random url
        name_result = get_unique_filename(path='/static/prescriptions/')
        filename = name_result['filename']
        path = name_result['path']

        url='/prescription/verify/' + filename

        pdf_file = generate_pdf_from_plan(self, url=url)  # This would create PDF and return local path
        pdf_file=abs_to_rel_path(pdf_file)
        print(pdf_file)
        
        plan = Plan(file=pdf_file, encounter=self, url=filename)
        db.session.add(plan)
        db.session.commit()
        return url

    def plan_cancel(self):
        if self.plan:
            db.session.delete(self.plan)

    def complete(self):
        if self.appointment:
            self.appointment.complete()

    def cancel(self):
        if self.appointment:
            self.appointment.cancel()

    def start(self):
        if self.appointment:
            self.appointment.start()
            
    def queue(self):
        if self.appointment:
            self.appointment.queue()

class Plan(db.Model):
    __tablename__ = 'plans'
    id = db.Column(db.Integer, primary_key=True)
    file = db.Column(db.String(50), nullable=False)
    url = db.Column(db.String(50), nullable=True)
    datetime_expiry = db.Column(db.DateTime, nullable=True)
    access_life = db.Column(db.Integer, default=10)
    clinician_sign = db.Column(db.Boolean, default=False)

    encounter: Mapped['Encounter'] = db.relationship(back_populates='plan')

    def is_valid(self) -> bool:
        return self.datetime_expiry > datetime.now() and self.access_life > 0

    def access_life_deduct(self):
        if self.access_life > 0:
            self.access_life -= 1
            db.session.commit()


class Prescription(db.Model):
    __tablename__ = 'prescriptions'
    id = db.Column(db.Integer, primary_key=True)
    encounter_id = db.Column(db.Integer, db.ForeignKey('encounters.id'))
    drug_id = db.Column(db.Integer, db.ForeignKey('drugs.id'))
    instruction = db.Column(db.String(50), nullable=False)
    duration = db.Column(db.Integer)

    encounter: Mapped['Encounter'] = db.relationship(back_populates='prescriptions')
    drug: Mapped['Drug'] = db.relationship(back_populates='prescriptions', lazy='joined')

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

def generate_pdf_from_plan(encounter, url):

    # absolute url path for public access
    url = 'https://' + current_app.config['APP_DOMAIN'] + url

    # Generate the QR code for URL path
    qr_code_path = generate_qr_code(data=url)  # Return file path of generated QR code
    qr_code_path = (qr_code_path)
    # Define your HTML content

    html_content = render_template(
        'plan_template.html',
        header='Health Center, Faculty of Medicine, University of Colombo',
        encounter=encounter,
        patient=encounter.appointment.patient,
        prescriptions=encounter.prescriptions,
        clinician=encounter.appointment.schedule.clinician,
        plan_note=encounter.plan_note,
        qr_code_url=qr_code_path, # URL to access QR code
        verification_url=url
    )

    #print(html_content)

    # Generate PDF
    base=base_url()
    print(base,"||....")
    pdf = HTML(string=html_content, base_url=base).write_pdf()

    # Save PDF to file
    name_result = get_unique_filename(path='/static/prescriptions/', extension='pdf', datestamp=True)
    pdf_filename= name_result['path'] + '/' + name_result['filename']
    #print('PDF',pdf_path,pdf_filename)
    with open(pdf_filename, 'wb') as f:
        f.write(pdf)
    return pdf_filename
