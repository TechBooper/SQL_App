import bcrypt
import sqlite3
import logging
import base64  # Import base64 for encoding and decoding
import os

# Configure logging to output to a file
logging.basicConfig(
    filename="app.log",  # Log file
    level=logging.INFO,  # Log level
    format="%(asctime)s - %(levelname)s - %(message)s",  # Log format
)


# Ensure the database file exists or create tables if necessary
def initialize_database():
    if not os.path.exists("app.db"):
        with sqlite3.connect("app.db") as conn:
            cursor = conn.cursor()
            # Create roles table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS roles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL
                )
            """
            )
            # Create users table with an email field
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role_id INTEGER NOT NULL,
                    FOREIGN KEY (role_id) REFERENCES roles(id)
                )
            """
            )
            # Create permissions table (if not already created)
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS permissions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    role_id INTEGER NOT NULL,
                    entity TEXT NOT NULL,
                    action TEXT NOT NULL,
                    FOREIGN KEY (role_id) REFERENCES roles(id)
                )
            """
            )
            conn.commit()
            logging.info(
                "Database initialized with tables 'roles', 'users', and 'permissions'."
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
def create_user(username, password, role_id, email):
    # Check if the password is strong enough
    if not is_password_strong(password):
        logging.warning(f"Password for user '{username}' is not strong enough.")
        print(
            "Password is not strong enough. It must be at least 8 characters long, contain upper and lower case letters, and include at least one number."
        )
        return  # Ensure this return statement is correctly indented within the if block

    # Hash the password using bcrypt
    password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

    # Encode the hash to a base64 string for storage
    password_hash_str = base64.b64encode(password_hash).decode("utf-8")

    try:
        with sqlite3.connect("app.db") as conn:
            conn.row_factory = sqlite3.Row  # Enable access to columns by name
            cursor = conn.cursor()

            try:
                # Insert the new user into the database
                cursor.execute(
                    "INSERT INTO users (username, email, password_hash, role_id) VALUES (?, ?, ?, ?)",
                    (username, email, password_hash_str, role_id),
                )
                conn.commit()
                logging.info(
                    f"User '{username}' created successfully with role ID '{role_id}'."
                )
                print(f"User '{username}' created with role ID '{role_id}'.")
            except sqlite3.IntegrityError as e:
                logging.warning(
                    f"User '{username}' or email '{email}' already exists. Error: {e}"
                )
                print(f"User '{username}' or email '{email}' already exists.")
            except sqlite3.Error as e:
                logging.error(f"Error while creating user '{username}': {e}")
                print(f"An error occurred while creating user '{username}': {e}")
    except sqlite3.Error as e:
        logging.error(
            f"Database connection error while creating user '{username}': {e}"
        )
        print(f"Database connection error: {e}")


# Function to create a new role
def create_role(name):
    try:
        with sqlite3.connect("app.db") as conn:
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
        with sqlite3.connect("app.db") as conn:
            conn.row_factory = sqlite3.Row  # Enable access to columns by name
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT roles.name
                FROM roles
                JOIN users ON users.role_id = roles.id
                WHERE users.id = ?
                """,
                (user_id,),
            )
            role = cursor.fetchone()
            if role:
                logging.info(f"Role '{role['name']}' retrieved for user ID {user_id}.")
                return role["name"]
            else:
                logging.warning(f"No role found for user ID {user_id}.")
                return None
    except sqlite3.Error as e:
        logging.error(
            f"Database connection error while retrieving role for user ID {user_id}: {e}"
        )
        print(f"Database connection error: {e}")
        return None


# Function to authenticate a user (username and password)
def authenticate(username, password):
    try:
        with sqlite3.connect("app.db") as conn:
            conn.row_factory = sqlite3.Row  # Enable access to columns by name
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, password_hash, role_id FROM users WHERE username = ?",
                (username,),
            )
            user = cursor.fetchone()
            if user:
                # Decode the stored hash from base64 string to bytes
                stored_password_hash = base64.b64decode(
                    user["password_hash"].encode("utf-8")
                )
                # Encode the entered password to bytes
                password_bytes = password.encode("utf-8")
                # Check the password
                if bcrypt.checkpw(password_bytes, stored_password_hash):
                    logging.info(f"User '{username}' authenticated successfully.")
                    return {"user_id": user["id"], "role_id": user["role_id"]}
                else:
                    logging.warning(
                        f"Failed authentication attempt for username: {username}. Incorrect password."
                    )
                    return None
            else:
                logging.warning(
                    f"Failed authentication attempt for username: {username}. User not found."
                )
                return None
    except sqlite3.Error as e:
        logging.error(f"Database error during authentication for '{username}': {e}")
        print(f"Database error: {e}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error during authentication for '{username}': {e}")
        print(f"An unexpected error occurred: {e}")
        return None


# Function to insert default permissions (if needed)
def insert_default_permissions():
    try:
        with sqlite3.connect("app.db") as conn:
            cursor = conn.cursor()

            # Permissions for Management
            management_permissions = [
                ("Management", "client", "create"),
                ("Management", "client", "update"),
                ("Management", "contract", "create"),
                ("Management", "contract", "update"),
                ("Management", "event", "create"),
                ("Management", "event", "update"),
            ]

            # Permissions for Sales
            sales_permissions = [
                ("Sales", "client", "create"),
                ("Sales", "client", "update"),
                ("Sales", "contract", "create"),
                ("Sales", "contract", "update"),
                ("Sales", "event", "create"),
            ]

            # Permissions for Support
            support_permissions = [
                ("Support", "event", "read"),
                ("Support", "event", "update"),
            ]

            # Insert Management Permissions
            for role, entity, action in management_permissions:
                cursor.execute(
                    """
                    INSERT INTO permissions (role_id, entity, action)
                    SELECT roles.id, ?, ?
                    FROM roles
                    WHERE roles.name = ?""",
                    (entity, action, role),
                )

            # Insert Sales Permissions
            for role, entity, action in sales_permissions:
                cursor.execute(
                    """
                    INSERT INTO permissions (role_id, entity, action)
                    SELECT roles.id, ?, ?
                    FROM roles
                    WHERE roles.name = ?""",
                    (entity, action, role),
                )

            # Insert Support Permissions
            for role, entity, action in support_permissions:
                cursor.execute(
                    """
                    INSERT INTO permissions (role_id, entity, action)
                    SELECT roles.id, ?, ?
                    FROM roles
                    WHERE roles.name = ?""",
                    (entity, action, role),
                )

            conn.commit()
            logging.info("Default permissions inserted.")
            print("Default permissions inserted.")
    except sqlite3.Error as e:
        logging.error(f"Database error during inserting default permissions: {e}")
        print(f"Database error during inserting default permissions: {e}")


# Initialize the database if it doesn't exist
initialize_database()

# Note: The following code is optional and can be uncommented to set up roles, users, and permissions.
# Be cautious when running test code to avoid unintended data modifications.

# Create default roles
# create_role('Management')
# create_role('Sales')
# create_role('Support')

# Insert default permissions
# insert_default_permissions()

# Create an admin user (assuming role_id for 'Management' is 1)
# create_user('admin', 'YourStrongP@ssw0rd', 1, 'admin@example.com')
