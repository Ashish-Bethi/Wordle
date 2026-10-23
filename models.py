from datetime import datetime, timezone
from flask_login import UserMixin
from extensions import db

def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(10), nullable=False, default="player")
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    games = db.relationship("Game", back_populates="user", cascade="all, delete-orphan")

class Word(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(5), unique=True, nullable=False)

class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    word_id = db.Column(db.Integer, db.ForeignKey("word.id"), nullable=False)
    started_at = db.Column(db.DateTime, nullable=False, default=utcnow, index=True)
    status = db.Column(db.String(20), nullable=False, default="in_progress")
    attempts_used = db.Column(db.Integer, nullable=False, default=0)
    completed_at = db.Column(db.DateTime, nullable=True)
    user = db.relationship("User", back_populates="games")
    secret = db.relationship("Word")
    guesses = db.relationship("Guess", back_populates="game", cascade="all, delete-orphan",
                              order_by="Guess.guess_number")

class Guess(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey("game.id"), nullable=False, index=True)
    guessed_word = db.Column(db.String(5), nullable=False)
    guess_number = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    game = db.relationship("Game", back_populates="guesses")
    __table_args__ = (db.UniqueConstraint("game_id", "guess_number", name="uq_game_guess_number"),)
