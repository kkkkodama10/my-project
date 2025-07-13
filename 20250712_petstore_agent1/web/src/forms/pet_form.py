from flask_wtf import FlaskForm
from wtforms import StringField, SelectField
from wtforms.validators import DataRequired, Length

class PetForm(FlaskForm):
    name = StringField('名前', validators=[DataRequired(), Length(max=50)])
    species = StringField('種別', validators=[DataRequired(), Length(max=30)])
    sex = SelectField('性別', choices=[('male', 'オス'), ('female', 'メス'), ('unknown', '不明')], validators=[DataRequired()])
