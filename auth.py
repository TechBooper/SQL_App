# auth.py

import bcrypt
import logging
from models import User, Role

logging.basicConfig(
    filename='auth.log',  # Logs will be saved to auth.log file
    level=logging.INFO,   
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def authenticate(username, password):
    try:
        user = User.get_by_username(username)
        if user and bcrypt.checkpw(password.encode('utf-8'), user.password_hash):
            logging.info(f"User {username} authenticated successfully.")
            return {'user_id': user.id, 'role_id': user.role_id}
        else:
            logging.warning(f"Failed authentication attempt for username: {username}.")
            return None
    except Exception as e:
        logging.error(f"Error during authentication for {username}: {e}")
        return None

def get_user_role(user_id):
    try:
        user = User.get_by_id(user_id)
        if user:
            role = Role.get_by_id(user.role_id)
            if role:
                logging.info(f"Role {role.name} retrieved for user ID {user_id}.")
                return role.name
            else:
                logging.warning(f"No role found for user ID {user_id}.")
                return None
        else:
            logging.warning(f"User ID {user_id} not found.")
            return None
    except Exception as e:
        logging.error(f"Error retrieving role for user ID {user_id}: {e}")
        return None

def create_user(username, password, role_id, email):
    try:
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        user = User.create(username=username, password_hash=password_hash, role_id=role_id, email=email)
        if user:
            logging.info(f"User {username} created successfully with role ID {role_id}.")
            return user
        else:
            logging.error(f"Failed to create user {username}.")
            return None
    except Exception as e:
        logging.error(f"Error while creating user {username}: {e}")
        return None
