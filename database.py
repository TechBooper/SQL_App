import bcrypt
import sqlite3
import logging

# Configure logging to output to a file
logging.basicConfig(
    filename='app.log',  # Log file
    level=logging.INFO,  # Log level
    format='%(asctime)s - %(levelname)s - %(message)s'  # Log format
)

# Password strength validation
def is_password_strong(password):
    if len(password) < 8:
        return False
    if not any(char.isdigit() for char in password):
        return False
    if not any(char.isupper() for char in password):
        return False
    if not any(char.islower() for char in password):
        return False
    return True

# Function to create a new user
def create_user(username, password, role_name):
    # Check if the password is strong enough
    if not is_password_strong(password):
        logging.warning(f"Password for user '{username}' is not strong enough.")
        print("Password is not strong enough. It must be at least 8 characters long, contain upper and lower case letters, and include at least one number.")
        return

    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    try:
        with sqlite3.connect('app.db') as conn:
            cursor = conn.cursor()

            # Get role_id based on role_name
            cursor.execute("SELECT id FROM roles WHERE name = ?", (role_name,))
            role = cursor.fetchone()

            if not role:
                logging.error(f"Role '{role_name}' does not exist for user '{username}'.")
                print(f"Role '{role_name}' does not exist.")
                return

            role_id = role[0]

            try:
                # Insert the new user into the database
                cursor.execute(
                    "INSERT INTO users (username, password_hash, role_id) VALUES (?, ?, ?)",
                    (username, password_hash, role_id)
                )
                conn.commit()
                logging.info(f"User '{username}' created successfully with role '{role_name}'.")
                print(f"User '{username}' created with role '{role_name}'.")
            except sqlite3.IntegrityError:
                logging.warning(f"User '{username}' already exists.")
                print(f"User '{username}' already exists.")
            except sqlite3.Error as e:
                logging.error(f"Error while creating user '{username}': {e}")
                print(f"An error occurred while creating user '{username}': {e}")
    except sqlite3.Error as e:
        logging.error(f"Database connection error while creating user '{username}': {e}")
        print(f"Database connection error: {e}")

# Function to create a new role
def create_role(name):
    try:
        with sqlite3.connect('app.db') as conn:
            cursor = conn.cursor()
            try:
                # Insert the new role into the database
                cursor.execute("INSERT INTO roles (name) VALUES (?)", (name,))
                conn.commit()
                logging.info(f"Role '{name}' created successfully.")
                print(f"Role '{name}' created.")
            except sqlite3.IntegrityError:
                logging.warning(f"Role '{name}' already exists.")
                print(f"Role '{name}' already exists.")
            except sqlite3.Error as e:
                logging.error(f"Error while creating role '{name}': {e}")
                print(f"An error occurred while creating role '{name}': {e}")
    except sqlite3.Error as e:
        logging.error(f"Database connection error while creating role '{name}': {e}")
        print(f"Database connection error: {e}")

# Function to retrieve the role for a specific user (based on user_id)
def get_user_role(user_id):
    try:
        with sqlite3.connect('app.db') as conn:
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
                logging.info(f"Role '{role['name']}' retrieved for user ID {user_id}.")
                return role['name']
            else:
                logging.warning(f"No role found for user ID {user_id}.")
                return None
    except sqlite3.Error as e:
        logging.error(f"Database connection error while retrieving role for user ID {user_id}: {e}")
        print(f"Database connection error: {e}")
        return None

# Function to authenticate a user (username and password)
def authenticate(username, password):
    try:
        with sqlite3.connect('app.db') as conn:
            conn.row_factory = sqlite3.Row  # Enable access to columns by name
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, password_hash, role_id FROM users WHERE username = ?",
                (username,)
            )
            user = cursor.fetchone()
            if user and bcrypt.checkpw(password.encode('utf-8'), user['password_hash']):
                logging.info(f"User '{username}' authenticated successfully.")
                return {'user_id': user['id'], 'role_id': user['role_id']}
            else:
                logging.warning(f"Failed authentication attempt for username: {username}.")
                return None
    except sqlite3.Error as e:
        logging.error(f"Database error during authentication for '{username}': {e}")
        print(f"Database error: {e}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error during authentication for '{username}': {e}")
        print(f"An unexpected error occurred: {e}")
        return None
