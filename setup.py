import sqlite3
from cs50 import SQL

def setup():
    # Create the database file if it doesn't exist
    conn = sqlite3.connect('chess.db')
    conn.close()
    print("Created chess.db file")
    
    # Initialize database connection
    db = SQL("sqlite:///chess.db")
    
    # Create users table for storing user accounts
    db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            rating INTEGER DEFAULT 1200
        )
    """)
    
    # Create AI user for playing against computer
    ai_exists = db.execute("SELECT id FROM users WHERE username = 'AI'")
    if not ai_exists:
        db.execute(
            "INSERT INTO users (username, email, password_hash, rating) VALUES (?, ?, ?, ?)",
            "AI", "ai@chessly.com", "no_login", 1500
        )
        print("Created AI user")
    
    # Create games table to track chess games
    db.execute("""
        CREATE TABLE IF NOT EXISTS games (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            white_player_id INTEGER NOT NULL,
            black_player_id INTEGER NOT NULL,
            result TEXT,
            moves TEXT DEFAULT '',
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            played_at TIMESTAMP,
            FOREIGN KEY (white_player_id) REFERENCES users(id),
            FOREIGN KEY (black_player_id) REFERENCES users(id)
        )
    """)
    
    # Create moves table for detailed move history
    db.execute("""
        CREATE TABLE IF NOT EXISTS moves (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            move_number INTEGER NOT NULL,
            move TEXT NOT NULL,
            made_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (game_id) REFERENCES games(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    
    # Create user stats table for tracking player performance
    db.execute("""
        CREATE TABLE IF NOT EXISTS user_stats (
            user_id INTEGER PRIMARY KEY,
            total_games INTEGER DEFAULT 0,
            wins INTEGER DEFAULT 0,
            losses INTEGER DEFAULT 0,
            draws INTEGER DEFAULT 0,
            current_rating INTEGER DEFAULT 1200,
            highest_rating INTEGER DEFAULT 1200,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    
    # Create friends table for social features
    db.execute("""
        CREATE TABLE IF NOT EXISTS friends (
            user_id INTEGER,
            friend_id INTEGER,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, friend_id),
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (friend_id) REFERENCES users(id)
        )
    """)
    
    print("\n✅ Database setup complete!")