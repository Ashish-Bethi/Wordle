"""Initialize the database and create an admin from environment variables."""
import os
from app import create_app
from extensions import db
from models import Word, User
from services.auth_service import validate_registration, create_user

app = create_app()

def main():
    username = os.environ.get("ADMIN_USERNAME", "")
    password = os.environ.get("ADMIN_PASSWORD", "")
    if not username or not password:
        raise SystemExit("Set ADMIN_USERNAME and ADMIN_PASSWORD before running seed.py.")
    error = validate_registration(username, password)
    if error:
        raise SystemExit("Invalid admin credentials: " + error)
    with app.app_context():
        db.create_all()
        for word in app.config["INITIAL_WORDS"]:
            if not Word.query.filter_by(word=word).first():
                db.session.add(Word(word=word))
        existing = User.query.filter_by(username=username).first()
        if existing:
            if existing.role != "admin":
                raise SystemExit("That username already belongs to a non-admin user.")
            print("Configured admin already exists; no password changes made.")
        else:
            create_user(username, password, role="admin")
        db.session.commit()
        print("Database ready; answer words seeded and admin account verified.")

if __name__ == "__main__":
    main()
