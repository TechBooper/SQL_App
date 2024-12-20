import bcrypt
import logging
import os
import sqlite3
from .models import User, Role, Permission

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE_FOLDER = os.path.join(BASE_DIR, "db_folder")
DATABASE_URL = os.path.join(DATABASE_FOLDER, "app.db")

if not os.path.isabs(DATABASE_URL):
    DATABASE_URL = os.path.abspath(DATABASE_URL)

print(f"DATABASE_URL: {DATABASE_URL}")

logging.basicConfig(
    filename="auth.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def authenticate(username, password):
    """
    Authenticates a user by username and password.
    """
    try:
        user = User.get_by_username(username)
        if user:
            if user.verify_password(password):
                logging.info("User %s authenticated successfully.", username)
                return {"username": user.username, "role_id": user.role_id}
            else:
                logging.warning("Failed authentication attempt for username: %s.", username)
                return None
        else:
            logging.warning("User %s not found.", username)
            return None
    except Exception as error:
        logging.error("Error during authentication for %s: %s", username, str(error))
        return None


def get_user_role(username):
    """
    Retrieves the role of a user by username.
    """
    try:
        user = User.get_by_username(username)
        if user:
            role_name = user.role_id
            if role_name:
                logging.info("Role %s retrieved for user %s.", role_name, username)
                return role_name
            logging.warning("No role found for user %s.", username)
            return None
        logging.warning("User %s not found.", username)
        return None
    except Exception as error:
        logging.error("Error retrieving role for user %s: %s", username, str(error))
        return None


def create_user(username, password, role_id, email):
    """
    Creates a new user with the given details.
    """
    try:
        # Validate role exists
        role = Role.get_by_name(role_id)  # Ensure the role exists in the database
        if not role:
            logging.error("Role %s does not exist.", role_id)
            return None

        # Hash the password
        hashed_password = hash_password(password)

        # Create the user
        user = User.create(
            username=username,
            password_hash=hashed_password,
            role_id=role_id,
            email=email
        )
        logging.info("User %s created successfully.", username)
        return user
    except sqlite3.IntegrityError as e:
        logging.error("Integrity error while creating user %s: %s", username, str(e))
        return None
    except Exception as error:
        logging.error("Error while creating user %s: %s", username, str(error))
        return None


def hash_password(password):
    """
    Hashes a password using bcrypt.
    """
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")


def has_permission(role_name, entity, action):
    """
    Checks if a role has a specific permission.
    """
    try:
        return Permission.has_permission(role_name, entity, action)
    except Exception as e:
        logging.error(f"Error checking permission for role {role_name}: {e}")
        return False
