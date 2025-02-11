from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from flask_login import current_user
from wtforms import StringField, PasswordField, DecimalField, SubmitField, RadioField, BooleanField, TextAreaField, FloatField, SelectField, widgets, SelectMultipleField, IntegerField, FileField
from wtforms.validators import DataRequired, Length, Email, NumberRange, EqualTo, ValidationError, InputRequired
from musicapp.models import User, Playlist, Music, Comment, Membership, PurchasedMembership, Genre, PlaylistMusic, MusicMetrics
from flask import current_app

# Custom MultiCheckboxField
class MultiCheckboxField(SelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')
    creator_submit = SubmitField('Sign Up as Music Creator') 

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is taken. Please choose a different one.')

class LoginForm(FlaskForm):
    tryna_user = StringField('Username', validators=[DataRequired()]) 
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class UpdateAccountForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    picture = FileField('Update Profile Picture', validators=[FileAllowed(['jpg', 'png'])])
    
    # Only for creators
    bank_details = StringField('Bank Details', validators=[Length(min=10, max=50)])
    membership_price = DecimalField('Membership Price (RM)', validators=[NumberRange(min=1, max=9999)], places=2)
    submit = SubmitField('Update')

    def validate_username(self, username):
        if username.data != current_user.username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('That username is taken. Please choose a different one.')

class GenreFilterForm(FlaskForm):
    genre_tag = MultiCheckboxField('Genres', choices=[])
    submit = SubmitField('Filter')

    def __init__(self, *args, **kwargs):
        super(GenreFilterForm, self).__init__(*args, **kwargs)
        # Dynamically set choices for genre_tag
        with current_app.app_context():
            genres = Genre.query.all()
            genre_list = [(each.tagname, each.tagname) for each in genres if each.tagname]
            self.genre_tag.choices = genre_list

class RequestResetForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')

    def validate_email(self, email):
        with current_app.app_context():
            user = User.query.filter_by(email=email.data).first()
            if user is None:
                raise ValidationError('There is no account with that email. You must register first.')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Reset Password')

class AddMusicForm(FlaskForm):
    title = StringField('Song Title', validators=[DataRequired(), Length(min=1, max=40)])
    cover_picture = FileField('Add Album Cover', validators=[FileAllowed(['jpg', 'png'])])
    genre = RadioField('Genre', choices=[], validators=[InputRequired()])
    music_file = FileField("Upload Music", validators=[DataRequired(), FileAllowed(['mp3'], 'MP3 files only!')])
    submit = SubmitField('Add Music')
    shareable = BooleanField("Shareable")  # Checkbox for shareable option
    premium = BooleanField("Premium")  # Checkbox for premium option

    def __init__(self, *args, **kwargs):
        super(AddMusicForm, self).__init__(*args, **kwargs)
        with current_app.app_context():
            genres = Genre.query.all()
            self.genre.choices = [(g.id, g.name) for g in genres]  # Store ID instead of name

    def validate_title(self, title):
        with current_app.app_context():
            music = Music.query.filter_by(title=title.data).first()
            if music:
                raise ValidationError('That song title is taken. Please choose a different title.')
    
class CommentForm(FlaskForm):
    content = TextAreaField('Leave a comment', validators=[DataRequired()])
    submit = SubmitField('Post Comment')