from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, DateField, SelectField
from sqlalchemy import String
from wtforms.validators import Length, DataRequired
from cbridge.models import label_mapping, _validators, _valuesets
from cbridge.models.user import User

class LoginForm(FlaskForm):
    username = StringField()
    password = PasswordField()
    submit = SubmitField('Login')

class RegisterForm(FlaskForm):
    class Meta:
        model = User
        exclude = ['date_joined']  # Exclude fields as necessary
        # Include submit field definition if needed
    
    table = 'User'
    #print(rules[table]['password'])

    username = StringField(validators = _validators[table]['username'])
    password = PasswordField(validators = _validators[table]['password'])
    confirm_password = PasswordField()
    name = StringField(validators = _validators[table]['name'])
    date_birth = DateField(validators = _validators[table]['date_birth'])
    identification = StringField(validators = _validators[table]['identification'])
    telephone = StringField(validators = _validators[table]['telephone'])
    email = StringField(validators = _validators[table]['email'])
    address = StringField(validators = _validators[table]['address'])
    submit = SubmitField('Register')

class RoleSwitchForm(FlaskForm):
    role = SelectField(choices = [], validators = [DataRequired()])
    #submit = SubmitField('Apply Role')