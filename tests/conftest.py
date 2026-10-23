import pytest
from app import create_app
from extensions import db
from models import User, Word
from services.auth_service import create_user

@pytest.fixture()
def app():
    app = create_app({
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
        "SQLALCHEMY_DATABASE_URI": "sqlite://",
        "SECRET_KEY": "test-secret",
        "APP_TIMEZONE": "Asia/Kolkata",
    })
    with app.app_context():
        db.create_all()
        for word in app.config["INITIAL_WORDS"]:
            db.session.add(Word(word=word))
        create_user("playerone", "Testpass1$", "player")
        create_user("adminuser", "Testpass1$", "admin")
        db.session.commit()
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()

@pytest.fixture()
def client(app):
    return app.test_client()
