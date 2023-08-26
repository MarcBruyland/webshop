from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField, PasswordField, DateField, FloatField
from wtforms.validators import DataRequired, Email


class LoginForm(FlaskForm):
    email = StringField("User name", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField('Submit')


class SignupForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    email = StringField("User name", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    address = StringField("Address", validators=[DataRequired()])
    submit = SubmitField('Submit')


class ShippingForm(FlaskForm):
    shipping_address = StringField("Shipping address", validators=[DataRequired()])
    submit = SubmitField('Submit')


class ProductForm(FlaskForm):
    id = IntegerField("Product id")
    name = StringField("Name", validators=[DataRequired()])
    description = StringField("Description")
    price = FloatField("Price", validators=[DataRequired()])
    picture = StringField("Picture", validators=[DataRequired()])
    quantity = IntegerField("Quantity")
    submit = SubmitField('Submit')


