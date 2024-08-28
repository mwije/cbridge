from .field_labels import label_mapping
from .user import *
from .schedule import *

# Add more models as needed

models = [User, Schedule]  # Add all relevant models


from sqlalchemy import inspect, String
from wtforms.validators import DataRequired, Length

def gather_valusets():
    valuesets = {}

    for model in models:
        model_name = model.__name__
        valuesets[model_name] = {}
        
        if hasattr(model, 'valueset'):
            valuesets.update({model_name : model.valueset()})
    return valuesets

def map_orm_validators(orm_column):
    validators = []

    if orm_column.nullable is False:
        validators.append(DataRequired())

    if isinstance(orm_column.type, String):
        max_length = orm_column.type.length
        if max_length:
            validators.append(Length(max=max_length))

    return validators

def gather_validators():
    validation_rules = {}

    for model in models:
        model_name = model.__name__
        validation_rules[model_name] = {}

        for column in inspect(model).columns:
            orm_validators = map_orm_validators(column)
            orm_validator_dict = {type(v).__name__: v for v in orm_validators}

            if hasattr(model, 'custom_constraints'):
                custom_validators = model.custom_constraints()
                if column.name in custom_validators:
                    
                    for custom_validator in custom_validators[column.name]:
                        validator_type = type(custom_validator).__name__
                        orm_validator_dict.update({validator_type : custom_validator})


            validators = list(orm_validator_dict.values())
            validation_rules[model_name][column.name] = validators
    return validation_rules

_validators = gather_validators()
_valuesets = gather_valusets()
print(_valuesets)