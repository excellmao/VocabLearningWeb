from flask_wtf import FlaskForm
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError, equal_to
from wtforms import PasswordField, SubmitField, StringField, TextAreaField, SelectField
from app.models import User

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=20)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    # Check username
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is taken, Please choose a different one.')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class WordForm(FlaskForm):
    term = StringField('Word/Term', validators=[DataRequired(), Length(max=100)])
    definition = TextAreaField('Definition', validators=[DataRequired()])
    ipa = StringField('IPA Pronunciation (Optional)')
    example_sentence = TextAreaField('Example Sentence (Optional)')
    synonyms = StringField('Synonyms (Comma separated, Optional)')
    topic_id = SelectField('Topic', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Save Word')

class TopicForm(FlaskForm):
    name = StringField('Deck Name', validators=[DataRequired(), Length(min=2, max=100)])
    submit = SubmitField('Create Deck')

class WordForm(FlaskForm):
    term = StringField('Word/Term', validators=[DataRequired(), Length(max=100)])
    definition = TextAreaField('Definition', validators=[DataRequired()])
    example_sentence = TextAreaField('Example Sentence (Optional)')
    submit = SubmitField('Add Word')