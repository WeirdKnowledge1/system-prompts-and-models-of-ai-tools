import sqlite3
import os

DATABASE_DIR = "data"
DATABASE_NAME = "user_credentials.db"
DATABASE_PATH = os.path.join(DATABASE_DIR, DATABASE_NAME)

def initialize_database():
    """
    Initializes the SQLite database and creates the users table if it doesn't exist.
    """
    os.makedirs(DATABASE_DIR, exist_ok=True) # Ensure data directory exists

    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        # Create users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Future tables could be added here (e.g., user_preferences, document_ownership)

        conn.commit()
        print(f"Database initialized successfully at {DATABASE_PATH}")

    except sqlite3.Error as e:
        print(f"Error initializing database: {e}")
        # Depending on the app's needs, might want to raise this or handle more gracefully
        raise
    finally:
        if conn:
            conn.close()

def get_db_connection():
    """
    Establishes and returns a database connection.
    The caller is responsible for closing the connection.
    Returns None if connection fails.
    """
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row # Access columns by name
        return conn
    except sqlite3.Error as e:
        print(f"Error connecting to database: {e}")
        return None

def get_user_by_username(username: str) -> sqlite3.Row | None:
    """
    Fetches a user by their username.
    Returns a sqlite3.Row object if found, else None.
    """
    conn = get_db_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user_row = cursor.fetchone()
        return user_row
    except sqlite3.Error as e:
        print(f"Error fetching user by username '{username}': {e}")
        return None
    finally:
        if conn:
            conn.close()

def add_user(username: str, password_hash: str, salt: str) -> int | None:
    """
    Adds a new user to the database.
    Returns the ID of the newly created user, or None on failure.
    """
    conn = get_db_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (username, password_hash, salt)
            VALUES (?, ?, ?)
        """, (username, password_hash, salt))
        conn.commit()
        return cursor.lastrowid # Get the ID of the inserted row
    except sqlite3.IntegrityError: # Handles UNIQUE constraint violation for username
        print(f"Error adding user: Username '{username}' already exists.")
        return None # Or raise a specific custom exception
    except sqlite3.Error as e:
        print(f"Error adding user '{username}': {e}")
        return None
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    print("Initializing database directly (for setup or testing)...")
    initialize_database()

    # Example: Test connection and try to fetch a non-existent user (should not error if table exists)
    print("\nTesting database connection...")
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM users WHERE username = ?", ("test_user_should_not_exist",))
            user_row = cursor.fetchone()
            if user_row is None:
                print("Test query executed successfully: test_user_should_not_exist not found (as expected).")
            else:
                print(f"Test query found unexpected user: {user_row['username']}")
        except sqlite3.Error as e_query:
            print(f"Error during test query: {e_query}")
        finally:
            connection.close()
            print("Database connection closed.")
    else:
        print("Failed to establish database connection for testing.")

    print("\nDatabase module self-test finished.")
