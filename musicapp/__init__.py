# __init__.py
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_migrate import Migrate

# Initialize extensions
db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = '5791628bb0b13ce0c676dfde280ba245'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///new.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Define upload folder
    UPLOAD_FOLDER = os.path.join(app.root_path, 'static/music')
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

    # Ensure the upload directory exists
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    # Initialize extensions with the app
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'
    login_manager.login_message_category = 'info'
    migrate.init_app(app, db)

    # Import and register routes
    from musicapp import routes
    app.register_blueprint(routes.bp)  # Assuming routes are defined in a Blueprint

    return app