import re
from werkzeug.security import generate_password_hash
from extensions import db
from models import User

SPECIALS = set("$%*&")

def validate_registration(username, password):
    if not isinstance(username, str) or len(username) < 5:
        return "Username must be at least 5 characters long."
    if not username.isalpha() or not username.isascii():
        return "Username must contain only English letters (A-Z or a-z)."
    if not isinstance(password, str) or len(password) < 5:
        return "Password must be at least 5 characters long."
    if not any(c.isalpha() for c in password):
        return "Password must contain at least one letter."
    if not any(c.isdigit() for c in password):
        return "Password must contain at least one number."
    if not any(c in SPECIALS for c in password):
        return "Password must contain at least one of these special characters: $, %, *, &."
    return None

def create_user(username, password, role="player"):
    user = User(username=username, password_hash=generate_password_hash(password), role=role)
    db.session.add(user)
    db.session.flush()
    return user
