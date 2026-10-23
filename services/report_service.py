from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo
from sqlalchemy import func, case
from extensions import db
from models import User, Game, Guess

def _bounds(day, timezone_name):
    tz = ZoneInfo(timezone_name)
    start = datetime.combine(day, time.min, tzinfo=tz).astimezone(ZoneInfo("UTC")).replace(tzinfo=None)
    end = (datetime.combine(day, time.min, tzinfo=tz) + timedelta(days=1)).astimezone(ZoneInfo("UTC")).replace(tzinfo=None)
    return start, end

def daily_report(day, timezone_name):
    start, end = _bounds(day, timezone_name)
    games = Game.query.filter(Game.started_at >= start, Game.started_at < end)
    total_games = games.count()
    unique_players = db.session.query(func.count(func.distinct(Game.user_id))).filter(
        Game.started_at >= start, Game.started_at < end).scalar() or 0
    games_won = games.filter(Game.status == "won").count()
    # Join the target Word explicitly to count exact winning submissions.
    from models import Word
    exact_correct_submissions = db.session.query(func.count(Guess.id)).join(
        Game, Guess.game_id == Game.id).join(Word, Game.word_id == Word.id).filter(
            Game.started_at >= start, Game.started_at < end,
            Guess.guessed_word == Word.word).scalar() or 0
    return {
        "date": day.isoformat(),
        "unique_players": unique_players,
        "games_started": total_games,
        "games_won": games_won,
        "exact_correct_submissions": exact_correct_submissions,
    }

def user_report(user_id, timezone_name):
    from models import Word
    rows = db.session.query(
        func.date(Game.started_at).label("utc_date"),
        func.count(Game.id).label("games_started"),
        func.sum(case((Game.status == "won", 1), else_=0)).label("games_won"),
        func.coalesce(func.sum(Game.attempts_used), 0).label("guesses_submitted"),
    ).filter(Game.user_id == user_id).group_by(func.date(Game.started_at)).order_by(
        func.date(Game.started_at).desc()).all()
    # Group in the configured local timezone in Python to ensure dates are local dates.
    games = Game.query.filter_by(user_id=user_id).order_by(Game.started_at.desc()).all()
    by_day = {}
    tz = ZoneInfo(timezone_name)
    for game in games:
        day = game.started_at.replace(tzinfo=ZoneInfo("UTC")).astimezone(tz).date().isoformat()
        record = by_day.setdefault(day, {
            "date": day, "games_started": 0, "games_won": 0,
            "exact_correct_submissions": 0, "guesses_submitted": 0
        })
        record["games_started"] += 1
        record["games_won"] += int(game.status == "won")
        record["guesses_submitted"] += game.attempts_used
        record["exact_correct_submissions"] += sum(
            1 for guess in game.guesses if guess.guessed_word == game.secret.word
        )
    return sorted(by_day.values(), key=lambda item: item["date"], reverse=True)
