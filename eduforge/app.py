from flask import Flask
from eduforge.models import db


def create_app(config=None):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///eduforge.db"
    app.config["SECRET_KEY"] = "change-me-in-production"

    if config:
        app.config.update(config)

    db.init_app(app)

    from eduforge.views import courses, main

    app.register_blueprint(main.bp)
    app.register_blueprint(courses.bp)

    with app.app_context():
        db.create_all()

    return app
