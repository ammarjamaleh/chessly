# Chessly

A Flask web application prototype for a chess community: user accounts, game and move records, player statistics, a leaderboard and friend requests. Final project for Harvard's [CS50x: Introduction to Computer Science](https://cs50.harvard.edu/x/).

> **Status: prototype.** The platform around the game (accounts, data model, pages) works. The chess game itself does not yet: there is no rules engine and no computer opponent. See [Limitations](#limitations-and-roadmap).

## What works

- **Accounts:** registration, login, logout, password change (minimum 8 characters, hashed with Werkzeug) and email update.
- **Games:** start a game against the built-in "AI" user or invite another user. Each game is stored with its players, status and move list.
- **Move records:** moves entered on the game page (free text, e.g. `e2e4`) are saved per game.
- **History and statistics:** paginated game history, a personal statistics page and a top-10 leaderboard.
- **Social:** user search/challenge page and friend requests.
- **Interface:** responsive layout with Bootstrap 5, Jinja templates and custom CSS. The tournaments page is a static mock-up.

## Tech stack

Python, Flask, Flask-Session (filesystem sessions), SQLite (through the `cs50` library's `SQL` helper), Jinja2, Bootstrap 5, HTML/CSS.

## Database

`setup.py` creates five tables on first run: `users`, `games`, `moves`, `user_stats` and `friends`, with foreign keys between them. It also creates the placeholder "AI" user.

## Getting started

```bash
git clone https://github.com/ammarjamaleh/chessly.git
cd chessly
python -m venv .venv
# Windows: .venv\Scripts\activate    Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000, register an account and start a game. The database (`chess.db`) is created automatically on the first run.

## Project structure

| Path | Purpose |
| --- | --- |
| `app.py` | Routes and application logic |
| `setup.py` | Database schema and initial data |
| `templates/` | Jinja templates (13 pages and the base layout) |
| `static/styles.css` | Custom styles |

## Limitations and roadmap

This is what the project does **not** do yet, and what I plan to build next:

- **No chess rules.** The board is a static starting position and moves are stored as plain text without validation. Next step: validate moves on the server with [python-chess](https://python-chess.readthedocs.io/) and add an interactive board in the browser.
- **The "AI" opponent is a placeholder.** I plan to connect the Stockfish engine, reusing my [chess-bot](https://github.com/ammarjamaleh/chess-bot) project.
- **Statistics and ratings are not updated automatically.** A proper Elo calculation after each finished game is planned.
- **Friend requests can be sent but not yet accepted.**
- **Security hardening is needed before any deployment:** access checks so that only a game's players can add moves, CSRF protection, and a configured secret key.
- **No automated tests yet.**

## Notes

- `login_required` follows the decorator pattern from the [Flask documentation](https://flask.palletsprojects.com/en/stable/patterns/viewdecorators/).
- Debug mode is off by default; set `FLASK_DEBUG=1` to enable it during development.

## License

MIT, see [LICENSE](LICENSE).
