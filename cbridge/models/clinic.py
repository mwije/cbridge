from .schedule import *

class Clinic(db.Model):
    __tablename__ = 'clinics'
    id = db.Column(db.Integer, primary_key=True)
    address = db.Column(db.String(50), unique=True, nullable=False)
    telephone = db.Column(db.String(16), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    note = db.Column(db.String(120), nullable=True)

    schedules = db.relationship('Schedule', back_populates='clinic')