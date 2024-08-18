from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms_alchemy import model_form_factory
from sqlalchemy import String
from wtforms.validators import Length
from cbridge.models import label_mapping
from cbridge.models.user import User

ModelForm = model_form_factory(FlaskForm)

class LoginForm(FlaskForm):
    username = StringField()
    password = PasswordField()
    submit = SubmitField('Login')

class RegisterForm(ModelForm):
    class Meta:
        model = User
        exclude = ['date_joined']  # Exclude fields as necessary
        # Include submit field definition if needed
        submit = SubmitField('Register')

    def __init__(self, *args, **kwargs):
        super(RegisterForm, self).__init__(*args, **kwargs)
        self.customize_fields()

    def customize_fields(self):
        """Customize fields after the form is initialized"""
        for field_name, field in self._fields.items():
            if field_name in label_mapping:
                field.label.text = label_mapping.get(field_name) + "\t:"
            
            column = getattr(self.Meta.model, field_name, None)
            if column and isinstance(column.type, String):
                # Generate new field attributes
                max_length = column.type.length
                field.validators = [Length(max=max_length)]
                field.render_kw = {"maxlength": max_length}

def generate_field_with_length(column):
    max_length = None
    if isinstance(column.type, String):
        max_length = column.type.length
    
    # Generate field
    field = StringField(column.name.capitalize(),
                        validators=[Length(max=max_length)] if max_length else [],
                        render_kw={"maxlength": max_length} if max_length else {})
    return field
