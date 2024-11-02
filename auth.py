import bcrypt
import logging
from models import User, Role
import sqlite3

# Configure logging settings
logging.basicConfig(
    filename="auth.log",  # Logs will be saved to auth.log file
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def authenticate(username, password):
    """
    Authenticates a user by username and password.

    Args:
        username (str): The username of the user.
        password (str): The password provided by the user.

    Returns:
        dict: A dictionary with user ID and role ID if authenticated, None otherwise.
    """
    try:
        user = User.get_by_username(username)
        if user and bcrypt.checkpw(password.encode("utf-8"), user.password_hash):
            logging.info("User %s authenticated successfully.", username)
            return {"user_id": int(user.id), "role_id": int(user.role_id)}
        logging.warning("Failed authentication attempt for username: %s.", username)
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
        user = User.create(
            username=username, password=password, role_id=role_id, email=email
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
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())


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
