from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_session import Session
from flask_cors import CORS

db = SQLAlchemy()
login_manager = LoginManager()
session_manager = Session()
cors = CORS()

