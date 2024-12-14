import bcrypt
import logging
import os
from models import User, Role, Permission

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE_FOLDER = os.path.join(BASE_DIR, "database")
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

    Returns:
        dict: A dictionary with username and role name if authenticated, None otherwise.
    """
    try:
        user = User.get_by_username(username)
        if user:
            if user.verify_password(password):
                logging.info("User %s authenticated successfully.", username)
                # user.role_id is actually the role name now
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

    Args:
        username (str): The username of the user.

    Returns:
        str: The name of the role if found, None otherwise.
    """
    try:
        user = User.get_by_username(username)
        if user:
            # role_id is actually the role's name
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

    Args:
        username (str): The username for the new user.
        password (str): The plain-text password for the new user.
        role_id (str): The role name for the new user (e.g., 'Management').
        email (str): The email address for the new user.

    Returns:
        User: The created User object if successful, None otherwise.
    """
    try:
        user = User.create(
            username=username, password=password, role_id=role_id, email=email
        )
        if isinstance(user, User):
            logging.info(
                "User %s created successfully with role %s.", username, role_id
            )
            return user
        else:
            logging.error("Failed to create user %s: %s", username, user)
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
        str: The hashed password.
    """
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")


def has_permission(role_name, entity, action):
    """
    Checks if a role has a specific permission.

    Args:
        role_name (str): The name of the role.
        entity (str): The entity to check permission for.
        action (str): The action to check permission for.

    Returns:
        bool: True if the permission exists, False otherwise.
    """
    try:
        # role_name is the role identifier now
        return Permission.has_permission(role_name, entity, action)
    except Exception as e:
        logging.error(f"Error checking permission for role {role_name}: {e}")
        return False
