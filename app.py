import os
from functools import wraps
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
import random

# If running for the first time
if not os.path.exists("chess.db"):
    from setup import setup
    setup()

app = Flask(__name__)

# Configure Flask application
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# connect to database
db = SQL("sqlite:///chess.db")

def login_required(view):
    """Redirect visitors who are not logged in to the login page."""
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return view(*args, **kwargs)
    return wrapped_view


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route("/")
@login_required
def index():
    # Homepage
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    # Handle user login
    session.clear()
    
    if request.method == "POST":
        # if no username or password
        if not request.form.get("username") or not request.form.get("password"):
            flash("Must fill all fields", "error")
            return render_template("login.html")
        
        # Get username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )
        
        # Check username and password
        if len(rows) != 1 or not check_password_hash(rows[0]["password_hash"], request.form.get("password")):
            flash("Incorrect password and/or username", "error")
            return render_template("login.html")
        
        # Set user cookie and redirect to main page
        session["user_id"] = rows[0]["id"]
        return redirect("/")
    
    else:
        # Display login form
        return render_template("login.html")

@app.route("/logout")
def logout():
    # Clear session and log user out
    session.clear()
    return redirect("/")

@app.route("/register", methods=["GET", "POST"])
def register():
    # Handle user registration
    if request.method == "POST":

        # Get user input
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        
        # If no username, email, password or confirmation
        if not all([username, email, password, confirmation]):
            flash("Must fill all fields", "error")
            return render_template("register.html")
        
        # Check password confirmation
        if password != confirmation:
            flash("Your passwords didn't match", "error")
            return render_template("register.html")
        
        # Password at least 8 chars
        if len(password) < 8:
            flash("Password must be at least 8 characters", "error")
            return render_template("register.html")
        
        # Hash password for security
        password_hash = generate_password_hash(password)
        
        # Check if username or email already exists
        existing_user = db.execute(
            "SELECT id FROM users WHERE username = ? OR email = ?", 
            username, email
        )
        
        if existing_user:
            flash("Username or email already exists", "error")
            return render_template("register.html")
        
        # Insert new user into database
        try:
            db.execute(
                "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)", 
                username, email, password_hash
            )
        except Exception as e:
            flash("Registration failed. Please try again.", "error")
            return render_template("register.html")
        
        # Log user in automatically after registration
        rows = db.execute("SELECT id FROM users WHERE username = ?", username)
        session["user_id"] = rows[0]["id"]
        
        flash("Registration successful!", "success")
        return redirect("/")
    
    # If method is get
    return render_template("register.html")

@app.route("/play")
@login_required
def play():
    # Display game selection page
    return render_template("play.html")

@app.route("/new_game", methods=["POST"])
@login_required
def new_game():
    # Create a new chess game
    opponent_type = request.form.get("opponent")
    
    if opponent_type == "ai":
        # Create game against AI
        game_id = db.execute(
            "INSERT INTO games (white_player_id, black_player_id, status) VALUES (?, ?, ?)",
            session["user_id"], 1, "active"
        )
        flash("Game started against AI!", "success")
        return redirect(f"/game/{game_id}")
    
    elif opponent_type == "friend":
        # Create game against friend
        friend_id = request.form.get("friend_id")
        if friend_id:
            game_id = db.execute(
                "INSERT INTO games (white_player_id, black_player_id, status) VALUES (?, ?, ?)",
                session["user_id"], friend_id, "pending"
            )
            flash("Game invitation sent!", "success")
            return redirect(f"/game/{game_id}")
    
    # If no valid selection redirect to play page
    return redirect("/play")

@app.route("/game/<int:game_id>")
@login_required
def game(game_id):
    # Display specific game with given ID
    game = db.execute("SELECT * FROM games WHERE id = ?", game_id)
    
    if not game:
        flash("Game not found", "error")
        return redirect("/")
    
    # Get usernames of white and black players
    white = db.execute("SELECT username FROM users WHERE id = ?", game[0]["white_player_id"])
    black = db.execute("SELECT username FROM users WHERE id = ?", game[0]["black_player_id"])
    
    return render_template("game.html", game=game[0], white=white[0], black=black[0])

@app.route("/move", methods=["POST"])
@login_required
def move():
    # Record a move in a game
    game_id = request.form.get("game_id")
    move_text = request.form.get("move")
    
    # Next move number
    current_move = db.execute(
        "SELECT MAX(move_number) as max_move FROM moves WHERE game_id = ?", game_id
    )
    move_number = (current_move[0]["max_move"] or 0) + 1
    
    # Insert move into database
    db.execute(
        "INSERT INTO moves (game_id, user_id, move_number, move) VALUES (?, ?, ?, ?)",
        game_id, session["user_id"], move_number, move_text
    )
    
    # Update game's moves field
    game = db.execute("SELECT moves FROM games WHERE id = ?", game_id)
    current_moves = game[0]["moves"] or ""
    db.execute(
        "UPDATE games SET moves = ? WHERE id = ?",
        f"{current_moves} {move_text}".strip(), game_id
    )
    
    flash("Move recorded!", "success")
    return redirect(f"/game/{game_id}")

@app.route("/history")
@login_required
def history():
    # Display user's game history
    page = request.args.get("page", 1, type=int)
    per_page = 10
    offset = (page - 1) * per_page
    
    # Get games
    games = db.execute("""
        SELECT g.*, 
               u1.username as white_username,
               u2.username as black_username
        FROM games g
        JOIN users u1 ON g.white_player_id = u1.id
        JOIN users u2 ON g.black_player_id = u2.id
        WHERE g.white_player_id = ? OR g.black_player_id = ?
        ORDER BY g.created_at DESC
        LIMIT ? OFFSET ?
    """, session["user_id"], session["user_id"], per_page, offset)
    
    # Count total games
    total = db.execute(
        "SELECT COUNT(*) as count FROM games WHERE white_player_id = ? OR black_player_id = ?",
        session["user_id"], session["user_id"]
    )[0]["count"]
    
    pages = (total + per_page - 1) // per_page
    
    return render_template("history.html", games=games, page=page, pages=pages)

@app.route("/stats")
@login_required
def stats():
    # Show user statistics
    user_stats = db.execute(
        "SELECT * FROM user_stats WHERE user_id = ?", session["user_id"]
    )
    
    # Create stats entry if user doesn't have one
    if not user_stats:
        db.execute("INSERT INTO user_stats (user_id) VALUES (?)", session["user_id"])
        user_stats = db.execute("SELECT * FROM user_stats WHERE user_id = ?", session["user_id"])
    
    # Get recent games for display
    recent_games = db.execute("""
        SELECT g.*, 
               u1.username as white_username,
               u2.username as black_username
        FROM games g
        JOIN users u1 ON g.white_player_id = u1.id
        JOIN users u2 ON g.black_player_id = u2.id
        WHERE g.white_player_id = ? OR g.black_player_id = ?
        ORDER BY g.created_at DESC
        LIMIT 5
    """, session["user_id"], session["user_id"])
    
    return render_template("stats.html", stats=user_stats[0], recent_games=recent_games)

@app.route("/leaderboard")
def leaderboard():
    # Show leaderboard
    top_players = db.execute("""
        SELECT u.username, us.current_rating, us.total_games, us.wins
        FROM users u
        JOIN user_stats us ON u.id = us.user_id
        WHERE u.username != 'AI'
        ORDER BY us.current_rating DESC
        LIMIT 10
    """)
    
    return render_template("leaderboard.html", players=top_players)

@app.route("/challenge")
@login_required
def challenge():
    # Show challenge page
    users = db.execute("""
        SELECT id, username, rating FROM users 
        WHERE id != ? AND username != 'AI'
        ORDER BY username
    """, session["user_id"])
    
    return render_template("challenge.html", users=users)

@app.route("/friends")
@login_required
def friends():
    # Show friends list
    friends_list = db.execute("""
        SELECT u.id, u.username, u.rating, f.status
        FROM friends f
        JOIN users u ON f.friend_id = u.id
        WHERE f.user_id = ?
    """, session["user_id"])
    
    pending = db.execute("""
        SELECT u.id, u.username
        FROM friends f
        JOIN users u ON f.user_id = u.id
        WHERE f.friend_id = ? AND f.status = 'pending'
    """, session["user_id"])
    
    return render_template("friends.html", friends=friends_list, pending=pending)

@app.route("/add_friend", methods=["POST"])
@login_required
def add_friend():
    # Add a friend by username
    username = request.form.get("username")
    
    if not username:
        flash("Please enter a username", "error")
        return redirect("/friends")
    
    # Find friend by username
    friend = db.execute("SELECT id FROM users WHERE username = ?", username)
    
    if not friend:
        flash("User not found", "error")
        return redirect("/friends")
    
    friend_id = friend[0]["id"]
    
    # Can't friend yourself
    if friend_id == session["user_id"]:
        flash("You cannot add yourself as a friend", "error")
        return redirect("/friends")
    
    # Check if already friend
    existing = db.execute(
        "SELECT * FROM friends WHERE user_id = ? AND friend_id = ?",
        session["user_id"], friend_id
    )
    
    if existing:
        flash("Already friends with this user", "error")
        return redirect("/friends")
    
    # Add friend with pending status
    db.execute(
        "INSERT INTO friends (user_id, friend_id, status) VALUES (?, ?, 'pending')",
        session["user_id"], friend_id
    )
    
    flash("Friend request sent!", "success")
    return redirect("/friends")

@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    # Show user profile
    user = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])[0]
    
    if request.method == "POST":
        # Update email if provided
        email = request.form.get("email")
        
        if email:
            db.execute("UPDATE users SET email = ? WHERE id = ?", email, session["user_id"])
            flash("Profile updated!", "success")
        
        return redirect("/profile")
    
    return render_template("profile.html", user=user)

@app.route("/change_password", methods=["GET", "POST"])
@login_required
def change_password():
    # Handle password change requests
    if request.method == "POST":
        # Get input
        current = request.form.get("current_password")
        new = request.form.get("new_password")
        confirmation = request.form.get("confirmation")
        
        # If no input
        if not current or not new or not confirmation:
            flash("Please fill all fields", "error")
            return render_template("change_password.html")
        
        # Check new password confirmation
        if new != confirmation:
            flash("New passwords don't match", "error")
            return render_template("change_password.html")
        
        # # Password at least 8 chars
        if len(new) < 8:
            flash("Password must be at least 8 characters", "error")
            return render_template("change_password.html")
        
        # Verify current password
        user = db.execute("SELECT password_hash FROM users WHERE id = ?", session["user_id"])[0]
        
        if not check_password_hash(user["password_hash"], current):
            flash("Current password is incorrect", "error")
            return render_template("change_password.html")
        
        # Update password with new hash
        new_hash = generate_password_hash(new)
        db.execute("UPDATE users SET password_hash = ? WHERE id = ?", new_hash, session["user_id"])
        
        flash("Password changed successfully!", "success")
        return redirect("/profile")
    
    return render_template("change_password.html")

@app.route("/tournaments")
@login_required
def tournaments():
    # Show tournaments page
    return render_template("tournament.html")

if __name__ == "__main__":
    # Debug mode only when FLASK_DEBUG=1 is set
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")