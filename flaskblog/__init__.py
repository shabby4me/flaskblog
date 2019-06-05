import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_mail import Mail

app = Flask(__name__)

app.config['SECRET_KEY'] = '8db8298fa36824fba4fdf0ed0bba3dfa'
##a way to generate this(after v3.6):
##import secrets
##secrets.token_hex(length)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
##/// means relative path(./)

#database access
db = SQLAlchemy(app)
#encrypt the password to store
bcrypt = Bcrypt(app)
#the package help deal with login
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'
app.config['MAIL_SERVER'] = 'smtp.googlemail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = os.environ.get('DB_MAIL')
app.config['MAIL_PASSWORD'] = os.environ.get('DB_MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('DB_MAIL')

mail = Mail(app)

from flaskblog import routes
