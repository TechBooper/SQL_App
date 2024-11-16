import bcrypt
import logging
from models import User, Role
import sqlite3

import os
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATABASE_URL = os.path.join(BASE_DIR, 'database', 'app.db')

conn = sqlite3.connect(DATABASE_URL)

# Configure logging settings
logging.basicConfig(
    filename="auth.log",  # Logs will be saved to auth.log file
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def authenticate(username, password):
    """
    Authenticates a user by username and password.

    Returns:
        dict: A dictionary with user ID and role ID if authenticated, None otherwise.
    """
    # Check if the database exists
    if not os.path.exists(DATABASE_URL):
        print("Database not found. Please initialize the database before proceeding.")
        return None

    try:
        conn = sqlite3.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute("SELECT id, password_hash, role_id FROM users WHERE username = ?", (username,))
        result = cursor.fetchone()
        conn.close()

        if result:
            user_id, stored_hash_str, role_id = result
            stored_hash = stored_hash_str.encode("utf-8")  # Encode to bytes
            if bcrypt.checkpw(password.encode("utf-8"), stored_hash):
                logging.info("User %s authenticated successfully.", username)
                return {"user_id": user_id, "role_id": role_id}
            else:
                logging.warning("Failed authentication attempt for username: %s.", username)
                return None
        else:
            logging.warning("User %s not found.", username)
            return None
    except Exception as error:
        logging.error("Error during authentication for %s: %s", username, str(error))
        return None



def get_user_role(user_id):
    """
    Retrieves the role of a user by user ID.

    Args:
        user_id (int): The ID of the user.

    Returns:
        str: The name of the role if found, None otherwise.
    """
    try:
        user = User.get_by_id(user_id)
        if user:
            role = Role.get_by_id(user.role_id)
            if role:
                logging.info("Role %s retrieved for user ID %s.", role.name, user_id)
                return role.name
            logging.warning("No role found for user ID %s.", user_id)
            return None
        logging.warning("User with ID %s not found.", user_id)
        return None
    except Exception as error:
        logging.error("Error retrieving role for user ID %s: %s", user_id, str(error))
        return None


def create_user(username, password, role_id, email):
    """
    Creates a new user with the given details.

    Args:
        username (str): The username for the new user.
        password (str): The plain-text password for the new user.
        role_id (int): The role ID for the new user.
        email (str): The email address for the new user.

    Returns:
        User: The created User object if successful, None otherwise.
    """
    try:
        password_hash = hash_password(password)
        user = User.create(
            username=username, password_hash=password_hash, role_id=role_id, email=email
        )
        if user:
            logging.info(
                "User %s created successfully with role ID %d.", username, role_id
            )
            return user
        logging.error("Failed to create user %s.", username)
        return None
    except Exception as error:
        logging.error("Error while creating user %s: %s", username, str(error))
        return None


def hash_password(password):
    """
    Hashes a password using bcrypt.

    Args:
        password (str): The plain-text password to hash.

    Returns:
        bytes: The hashed password.
    """
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")


def has_permission(role_id, entity, action):
    conn = sqlite3.connect("app.db")
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT 1 FROM permissions
        WHERE role_id = ? AND entity = ? AND action = ?
    """,
        (role_id, entity, action),
    )
    result = cursor.fetchone()
    conn.close()
    return result is not None
