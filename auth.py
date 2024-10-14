import sqlite3
import bcrypt
import logging

logging.basicConfig(
    filename='auth.log',  # Logs will be saved to auth.log file
    level=logging.INFO,   
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def authenticate(username, password):
    try:
        with sqlite3.connect('app.db') as conn:
            conn.row_factory = sqlite3.Row  
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, password_hash, role_id FROM users WHERE username = ?",
                (username,)
            )
            user = cursor.fetchone()
            if user and bcrypt.checkpw(password.encode('utf-8'), user['password_hash']):
                logging.info(f"User {username} authenticated successfully.")
                return {'user_id': user['id'], 'role_id': user['role_id']}
            else:
                logging.warning(f"Failed authentication attempt for username: {username}.")
                return None
    except sqlite3.Error as e:
        logging.error(f"Database error during authentication for {username}: {e}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error during authentication for {username}: {e}")
        return None

def get_user_role(user_id):
    try:
        with sqlite3.connect('app.db') as conn:
            conn.row_factory = sqlite3.Row  
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT roles.name
                FROM roles
                JOIN users ON users.role_id = roles.id
                WHERE users.id = ?
                """,
                (user_id,)
            )
            role = cursor.fetchone()
            if role:
                logging.info(f"Role {role['name']} retrieved for user ID {user_id}.")
                return role['name']
            else:
                logging.warning(f"No role found for user ID {user_id}.")
                return None
    except sqlite3.Error as e:
        logging.error(f"Database error retrieving role for user ID {user_id}: {e}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error retrieving role for user ID {user_id}: {e}")
        return None

def create_user(username, password, role_id):
    try:
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        with sqlite3.connect('app.db') as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (username, password_hash, role_id) VALUES (?, ?, ?)",
                (username, password_hash, role_id)
            )
            conn.commit()
            logging.info(f"User {username} created successfully with role ID {role_id}.")
    except sqlite3.IntegrityError as e:
        logging.error(f"Failed to create user {username}: {e}")
    except sqlite3.Error as e:
        logging.error(f"Database error while creating user {username}: {e}")
    except Exception as e:
        logging.error(f"Unexpected error while creating user {username}: {e}")
