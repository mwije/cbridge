from ..extensions import db
from flask_login import UserMixin
from datetime import datetime

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    uid = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)
    role = db.Column(db.String(10), nullable=False)

    name = db.Column(db.String(120), nullable=False)
    date_birth = db.Column(db.Date, nullable=False)
    identification = db.Column(db.String(15), nullable=True)

    telephone = db.Column(db.String(16), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    address = db.Column(db.String(120), nullable=False)

    date_joined = db.Column(db.Date, default=datetime.utcnow)

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