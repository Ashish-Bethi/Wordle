import os
from pathlib import Path

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-me")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///" + str(Path(__file__).resolve().parent / "instance" / "wordle.db")
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    APP_TIMEZONE = os.environ.get("APP_TIMEZONE", "Asia/Kolkata")
    WTF_CSRF_ENABLED = True
    INITIAL_WORDS = [
        "APPLE", "GRAPE", "MANGO", "BREAD", "CHAIR",
        "PLANT", "HOUSE", "WATER", "LIGHT", "SMILE",
        "BRAVE", "CLOUD", "STONE", "TRAIN", "SHEEP",
        "TIGER", "LEMON", "PEACH", "NURSE", "DREAM",
    ]
