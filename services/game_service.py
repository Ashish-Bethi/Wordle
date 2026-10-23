import os
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo
from wordfreq import zipf_frequency
from extensions import db
from models import Game, Guess, Word

MAX_DAILY_GAMES = 3
MAX_GUESSES = 5

# A small fallback keeps core behavior testable if wordfreq is not installed,
# though requirements.txt installs it for a broad English vocabulary.
FALLBACK_WORDS = {
    "APPLE", "GRAPE", "MANGO", "BREAD", "CHAIR", "PLANT", "HOUSE", "WATER",
    "LIGHT", "SMILE", "BRAVE", "CLOUD", "STONE", "TRAIN", "SHEEP", "TIGER",
    "LEMON", "PEACH", "NURSE", "DREAM", "CRANE", "SLATE", "TRACE", "AUDIO",
    "ROAST", "SHARE", "CLOSE", "WORLD", "MUSIC", "GREEN", "BLACK", "WHITE",
    "QUICK", "ZEBRA", "CANDY", "FROST", "NIGHT", "RIVER", "MOUSE", "BERRY",
    "PLANE", "SMALL", "LARGE", "EARTH", "HEART", "CROWN", "SUGAR", "GRASS",
}

def is_accepted_guess(word):
    if word in FALLBACK_WORDS:
        return True
    try:
        return zipf_frequency(word.lower(), "en") >= 2.0
    except Exception:
        return False

def evaluate_guess(secret, guess):
    """Return per-letter status, correctly accounting for duplicate letters."""
    result = ["absent"] * 5
    remaining = {}
    for i, (target, letter) in enumerate(zip(secret, guess)):
        if target == letter:
            result[i] = "correct"
        else:
            remaining[target] = remaining.get(target, 0) + 1
    for i, letter in enumerate(guess):
        if result[i] == "correct":
            continue
        if remaining.get(letter, 0) > 0:
            result[i] = "present"
            remaining[letter] -= 1
    return result

def _day_bounds(day, timezone_name):
    tz = ZoneInfo(timezone_name)
    start_local = datetime.combine(day, time.min, tzinfo=tz)
    end_local = start_local + timedelta(days=1)
    # Store timestamps in UTC-naive form consistently with model defaults.
    return (start_local.astimezone(ZoneInfo("UTC")).replace(tzinfo=None),
            end_local.astimezone(ZoneInfo("UTC")).replace(tzinfo=None))

def start_game(user, day, timezone_name):
    start, end = _day_bounds(day, timezone_name)
    count = Game.query.filter(
        Game.user_id == user.id,
        Game.started_at >= start,
        Game.started_at < end
    ).count()
    if count >= MAX_DAILY_GAMES:
        raise ValueError("Daily limit reached: you can start at most 3 games per day.")
    words = Word.query.order_by(Word.id).all()
    if not words:
        raise ValueError("No answer words are configured. Run flask init-db first.")
    # Random selection is done by Python; the chosen answer is never sent to the client.
    import secrets
    secret = secrets.choice(words)
    game = Game(user_id=user.id, word_id=secret.id)
    db.session.add(game)
    db.session.flush()
    return game

def submit_guess(game, word):
    if game.status != "in_progress":
        raise ValueError("This game has already ended.")
    if game.attempts_used >= MAX_GUESSES:
        raise ValueError("You have used all 5 guesses.")
    number = game.attempts_used + 1
    guess = Guess(game_id=game.id, guessed_word=word, guess_number=number)
    db.session.add(guess)
    game.attempts_used = number
    won = word == game.secret.word
    if won:
        game.status = "won"
        game.completed_at = datetime.utcnow()
    elif number == MAX_GUESSES:
        game.status = "lost"
        game.completed_at = datetime.utcnow()
    db.session.flush()
    return {
        "guess": word,
        "guess_number": number,
        "feedback": evaluate_guess(game.secret.word, word),
        "status": game.status,
        "won": won,
        "message": ("Congratulations! You guessed the word." if won else
                    "Better luck next time. The word was " + game.secret.word + "." if game.status == "lost" else None)
    }
