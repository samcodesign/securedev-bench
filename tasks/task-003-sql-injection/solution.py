import sqlite3
from flask import Flask, jsonify, request

app = Flask(__name__)
DB_FILE = "users.db"

def init_db():
    """Initializes the database with a users table and some dummy data."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("DROP TABLE IF EXISTS users")
        cursor.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT, role TEXT)")
        cursor.execute("INSERT INTO users (id, username, role) VALUES (1, 'admin', 'administrator')")
        cursor.execute("INSERT INTO users (id, username, role) VALUES (2, 'guest', 'user')")
        conn.commit()

@app.route("/users/<user_id>")
def get_user(user_id):
    """Fetches a user from the database by their ID."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        # FIX: Use a parameterized query. The '?' is a placeholder, and the
        # database driver safely handles the user_id variable.
        query = "SELECT id, username, role FROM users WHERE id = ?"
        try:
            cursor.execute(query, (user_id,))
            user = cursor.fetchall()
            return jsonify(user)
        except sqlite3.Error as e:
            return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5001)