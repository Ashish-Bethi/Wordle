import os
from datetime import datetime
from zoneinfo import ZoneInfo

from flask import Flask, jsonify, redirect, render_template, request, url_for, flash
from flask_login import LoginManager, current_user, login_required, login_user, logout_user
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import check_password_hash

from config import Config
from extensions import db
from models import User, Word, Game, Guess
from services.auth_service import validate_registration, create_user
from services.game_service import evaluate_guess, is_accepted_guess, start_game, submit_guess
from services.report_service import daily_report, user_report

login_manager = LoginManager()
login_manager.login_view = "login"
csrf = CSRFProtect()


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)
    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    def local_today():
        return datetime.now(ZoneInfo(app.config["APP_TIMEZONE"])).date()

    def admin_required():
        return current_user.is_authenticated and current_user.role == "admin"

    @app.get("/")
    def index():
        if not current_user.is_authenticated:
            return redirect(url_for("login"))
        return redirect(url_for("admin_dashboard" if current_user.role == "admin" else "game_page"))

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if request.method == "POST":
            username = request.form.get("username", "")
            password = request.form.get("password", "")
            error = validate_registration(username, password)
            if error:
                flash(error, "error")
            elif User.query.filter_by(username=username).first():
                flash("That username is already taken.", "error")
            else:
                create_user(username, password, role="player")
                flash("Registration successful. Please log in.", "success")
                return redirect(url_for("login"))
        return render_template("register.html")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            username = request.form.get("username", "")
            password = request.form.get("password", "")
            user = User.query.filter_by(username=username).first()
            if user and check_password_hash(user.password_hash, password):
                login_user(user)
                return redirect(url_for("index"))
            flash("Invalid username or password.", "error")
        return render_template("login.html")

    @app.post("/logout")
    @login_required
    def logout():
        logout_user()
        return redirect(url_for("login"))

    @app.get("/game")
    @login_required
    def game_page():
        if current_user.role != "player":
            return redirect(url_for("admin_dashboard"))
        return render_template("game.html")

    @app.post("/api/games")
    @login_required
    def api_start_game():
        if current_user.role != "player":
            return jsonify(error="Only player accounts can start games."), 403
        try:
            game = start_game(current_user, local_today(), app.config["APP_TIMEZONE"])
            db.session.commit()
        except ValueError as exc:
            db.session.rollback()
            return jsonify(error=str(exc)), 429
        return jsonify(game_id=game.id, max_guesses=5, guesses=[])

    @app.post("/api/games/<int:game_id>/guesses")
    @login_required
    def api_submit_guess(game_id):
        if current_user.role != "player":
            return jsonify(error="Only player accounts can submit guesses."), 403
        payload = request.get_json(silent=True) or {}
        word = payload.get("word", "")
        game = db.session.get(Game, game_id)
        if not game or game.user_id != current_user.id:
            return jsonify(error="Game not found."), 404
        if not isinstance(word, str) or len(word) != 5 or not word.isalpha() or not word.isupper() or not word.isascii():
            return jsonify(error="Enter exactly five uppercase English letters."), 400
        if not is_accepted_guess(word):
            return jsonify(error="That word is not in the accepted five-letter English word list."), 400
        try:
            result = submit_guess(game, word)
            db.session.commit()
        except ValueError as exc:
            db.session.rollback()
            return jsonify(error=str(exc)), 400
        return jsonify(result)

    @app.get("/admin")
    @login_required
    def admin_dashboard():
        if not admin_required():
            return "Forbidden", 403
        return render_template("admin/dashboard.html")

    @app.get("/admin/api/daily")
    @login_required
    def admin_daily_api():
        if not admin_required():
            return jsonify(error="Admin access required."), 403
        raw_date = request.args.get("date", local_today().isoformat())
        try:
            day = datetime.strptime(raw_date, "%Y-%m-%d").date()
        except ValueError:
            return jsonify(error="Date must use YYYY-MM-DD."), 400
        return jsonify(daily_report(day, app.config["APP_TIMEZONE"]))

    @app.get("/admin/api/users")
    @login_required
    def admin_users_api():
        if not admin_required():
            return jsonify(error="Admin access required."), 403
        return jsonify(users=[{"id": u.id, "username": u.username}
                              for u in User.query.filter_by(role="player").order_by(User.username).all()])

    @app.get("/admin/api/user-report")
    @login_required
    def admin_user_report_api():
        if not admin_required():
            return jsonify(error="Admin access required."), 403
        try:
            user_id = int(request.args.get("user_id", ""))
        except ValueError:
            return jsonify(error="A valid user_id is required."), 400
        user = db.session.get(User, user_id)
        if not user or user.role != "player":
            return jsonify(error="Player not found."), 404
        return jsonify(username=user.username, days=user_report(user_id, app.config["APP_TIMEZONE"]))

    @app.cli.command("init-db")
    def init_db_command():
        """Create tables and seed the fixed answer pool."""
        db.create_all()
        if Word.query.count() == 0:
            for word in app.config["INITIAL_WORDS"]:
                db.session.add(Word(word=word))
            db.session.commit()
        print("Database initialized and answer words seeded.")

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG", "0") == "1")
