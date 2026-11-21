import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "users.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            full_name TEXT NOT NULL,
            role TEXT DEFAULT 'Student',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()

    # Pre-seed default test users if table is empty
    cursor.execute("SELECT COUNT(*) as count FROM users")
    row = cursor.fetchone()
    if row["count"] == 0:
        seed_users = [
            ("admin", "admin123", "System Administrator", "Administrator"),
            ("john_doe", "password123", "John Doe", "Student"),
            ("alice", "securePass2024", "Alice Smith", "Instructor")
        ]
        cursor.executemany(
            "INSERT INTO users (username, password, full_name, role) VALUES (?, ?, ?, ?)",
            seed_users
        )
        conn.commit()
        print("Database initialized and pre-seeded with sample users.")
    conn.close()

def validate_user(username, password):
    """
    Checks if the username and password match records in the database.
    Returns user dict if valid, else None.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, username, password, full_name, role FROM users WHERE username = ? AND password = ?",
        (username.strip(), password.strip())
    )
    user = cursor.fetchone()
    conn.close()
    if user:
        return dict(user)
    return None

def create_user(username, password, full_name, role="Student"):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (username, password, full_name, role) VALUES (?, ?, ?, ?)",
            (username.strip(), password.strip(), full_name.strip(), role.strip() or "Student")
        )
        conn.commit()
        new_id = cursor.lastrowid
        conn.close()
        return True, new_id
    except sqlite3.IntegrityError:
        conn.close()
        return False, "Username already exists in the database."
    except Exception as e:
        conn.close()
        return False, str(e)

def get_all_users():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, password, full_name, role, created_at FROM users ORDER BY id ASC")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

if __name__ == "__main__":
    init_db()
    print("All users currently in DB:")
    for u in get_all_users():
        print(f" - [{u['id']}] {u['username']} | {u['full_name']} | Role: {u['role']}")
