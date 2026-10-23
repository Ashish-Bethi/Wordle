# Python Flask Wordle

A Flask + SQLite Wordle application with player/admin roles, secure password hashing, a daily three-game limit, five guesses per game, Wordle feedback, and admin reports.

## Requirements

- Python 3.11 or newer recommended
- pip
- Internet access for installing Python dependencies

## 1. Create a virtual environment

### Windows PowerShell
```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### macOS / Linux
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 2. Configure secret key and admin credentials

Set these environment variables before initialization. Use a unique, long secret key and a strong admin password.

### Windows PowerShell
```powershell
$env:SECRET_KEY = "replace-this-with-a-long-random-secret"
$env:ADMIN_USERNAME = "adminuser"
$env:ADMIN_PASSWORD = "ChangeMe9$"
$env:APP_TIMEZONE = "Asia/Kolkata"
```

### macOS / Linux
```bash
export SECRET_KEY='replace-this-with-a-long-random-secret'
export ADMIN_USERNAME='adminuser'
export ADMIN_PASSWORD='ChangeMe9$'
export APP_TIMEZONE='Asia/Kolkata'
```

Do not commit real credentials or `.env` files to source control.

## 3. Initialize database and seed answer words/admin

```bash
python seed.py
```

This creates `instance/wordle.db`, inserts the initial 20 answer words if missing, and creates the configured admin. If that admin already exists, its password is not changed.

## 4. Run the application

```bash
flask --app app run
```

Open http://127.0.0.1:5000.

- Register a player account from the registration page.
- Log in with the configured admin username/password to view reports.
- The answer pool is seeded with 20 uppercase five-letter words.

## 5. Run tests

```bash
pytest -q
```

## Implementation notes

- A game counts toward the daily cap as soon as it starts, even if abandoned.
- Daily limits and reports use `APP_TIMEZONE`; the default is `Asia/Kolkata`.
- The browser receives feedback and game status but never receives the secret word before the game ends.
- The accepted-guess validator uses `wordfreq` to accept a broad English vocabulary, with a small fallback list if the library is unavailable. Dictionary coverage is not identical to every official Wordle list.
- Passwords are hashed with Werkzeug. The admin role is created only by `seed.py`, not public registration.
- SQLite timestamps are stored as UTC-naive datetimes and converted for daily reports.
- For deployment, set `FLASK_DEBUG=0`, use a strong `SECRET_KEY`, run behind a production WSGI server, and consider PostgreSQL for concurrent multi-user deployments.
