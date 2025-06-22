from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField,PasswordField
from wtforms.validators import DataRequired, URL
from flask_ckeditor import CKEditorField


# WTForm for creating a blog post
class CreatePostForm(FlaskForm):
    title = StringField("Blog Post Title", validators=[DataRequired()])
    subtitle = StringField("Subtitle", validators=[DataRequired()])
    img_url = StringField("Blog Image URL", validators=[DataRequired(), URL()])
    body = CKEditorField("Blog Content", validators=[DataRequired()])
    submit = SubmitField("Submit Post")


# TODO: Create a RegisterForm to register new users
class RegisterForm(FlaskForm):
    name=StringField("Username:",validators=[DataRequired(message="John Doe")])
    email=StringField("Email:", validators=[DataRequired(message="example@example.com")])
    password=PasswordField("Password:",validators=[DataRequired(message="Enter Your password")])
    submit=SubmitField("Register")

# TODO: Create a LoginForm to login existing users
class LogInForm(FlaskForm):
    email=StringField("Email:", validators=[DataRequired(message="example@example.com")])
    password=PasswordField("Password:",validators=[DataRequired(message="Enter Your password")])
    submit=SubmitField("Log In")

# TODO: Create a CommentForm so users can leave comments below posts
class CommentForm(FlaskForm):
    body=CKEditorField("Add Comment",validators=[DataRequired(message="Loved your Blog")])
    submit=SubmitField("Post Comment")