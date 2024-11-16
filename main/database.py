"""Database initialization and user creation module for Epic Events CRM.

This module handles the setup of the SQLite database, including table creation,
inserting default roles and permissions, and creating the initial admin user.
It also includes utility functions for password validation and user creation.
"""

import bcrypt
import sqlite3
import logging
import base64
import os
import getpass


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATABASE_FOLDER = os.path.join(BASE_DIR, 'database')
DATABASE_URL = os.path.join(DATABASE_FOLDER, "app.db")

if not os.path.exists(DATABASE_FOLDER):
    os.makedirs(DATABASE_FOLDER)  # Create the 'database' folder if it doesn't exist
    
DEBUG = os.getenv("DEBUG") == "True"
SECRET_KEY = os.getenv("SECRET_KEY")

# Configure logging to output to a file
logging.basicConfig(
    filename="app.log",  # Log file
    level=logging.DEBUG if DEBUG else logging.INFO,  # Log level
    format="%(asctime)s - %(levelname)s - %(message)s",  # Log format
)

def with_connection(func):
    """Decorator to manage database connections for functions that interact with the database.

    Args:
        func (callable): The function to be decorated.

    Returns:
        callable: The wrapped function with managed database connection.
    """
    def wrapper(*args, **kwargs):
        try:
            with sqlite3.connect(DATABASE_URL) as conn:
                conn.row_factory = sqlite3.Row  # Enable access to columns by name
                return func(conn, *args, **kwargs)
        except sqlite3.Error as e:
            logging.error(f"Database connection error: {e}")
            print(f"Database connection error: {e}")
    return wrapper

def is_password_strong(password):
    """Check if the provided password meets strength requirements.

    A strong password must be at least 8 characters long, contain both uppercase
    and lowercase letters, and include at least one number.

    Args:
        password (str): The password to validate.

    Returns:
        bool: True if the password is strong, False otherwise.
    """
    if len(password) < 8:
        return False
    if not any(char.isdigit() for char in password):
        return False
    if not any(char.isupper() for char in password):
        return False
    if not any(char.islower() for char in password):
        return False
    return True

@with_connection
def create_user(conn, username, password, role_id, email):
    """Create a new user in the database.

    Args:
        conn (sqlite3.Connection): The database connection object.
        username (str): The username for the new user.
        password (str): The plaintext password for the new user.
        role_id (int): The role ID to assign to the user.
        email (str): The email address of the new user.

    Returns:
        None
    """
    # Check if the password is strong enough
    if not is_password_strong(password):
        logging.warning(f"Password for user '{username}' is not strong enough.")
        print(
            "Password is not strong enough. It must be at least 8 characters long, contain upper and lower case letters, and include at least one number."
        )
        return

    # Hash the password using bcrypt
    password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

    # Encode the hash to a base64 string for storage
    password_hash_str = base64.b64encode(password_hash).decode("utf-8")

    try:
        cursor = conn.cursor()
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

@with_connection
def create_role(conn, name):
    """Create a new role in the database.

    Args:
        conn (sqlite3.Connection): The database connection object.
        name (str): The name of the role to create.

    Returns:
        None
    """
    try:
        cursor = conn.cursor()
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

@with_connection
def insert_default_permissions(conn):
    """Insert default permissions into the database.

    Adds predefined permissions for 'Management', 'Commercial', and 'Support' roles.

    Args:
        conn (sqlite3.Connection): The database connection object.

    Returns:
        None
    """
    try:
        cursor = conn.cursor()

        # Permissions for Management
        management_permissions = [
            ("client", "create"),
            ("client", "update"),
            ("client", "read"),
            ("client", "delete"),
            ("contract", "create"),
            ("contract", "update"),
            ("contract", "read"),
            ("contract", "delete"),
            ("event", "create"),
            ("event", "update"),
            ("event", "read"),
            ("event", "delete"),
            ("user", "create"),
            ("user", "update"),
            ("user", "delete"),
            ("user", "read"),
        ]

        # Permissions for Commercial
        commercial_permissions = [
            ("client", "create"),
            ("client", "update"),
            ("client", "read"),
            ("contract", "create"),
            ("contract", "update"),
            ("contract", "read"),
            ("event", "create"),
            ("event", "read"),
        ]

        # Permissions for Support
        support_permissions = [
            ("event", "read"),
            ("event", "update"),
            ("client", "read"),
            ("contract", "read"),
        ]

        # Insert Management Permissions
        for entity, action in management_permissions:
            cursor.execute(
                """
                INSERT INTO permissions (role_id, entity, action)
                SELECT roles.id, ?, ?
                FROM roles
                WHERE roles.name = 'Management'""",
                (entity, action),
            )

        # Insert Commercial Permissions
        for entity, action in commercial_permissions:
            cursor.execute(
                """
                INSERT INTO permissions (role_id, entity, action)
                SELECT roles.id, ?, ?
                FROM roles
                WHERE roles.name = 'Commercial'""",
                (entity, action),
            )

        # Insert Support Permissions
        for entity, action in support_permissions:
            cursor.execute(
                """
                INSERT INTO permissions (role_id, entity, action)
                SELECT roles.id, ?, ?
                FROM roles
                WHERE roles.name = 'Support'""",
                (entity, action),
            )

        conn.commit()
        logging.info("Default permissions inserted.")
        print("Default permissions inserted.")
    except sqlite3.Error as e:
        logging.error(f"Database error during inserting default permissions: {e}")
        print(f"Database error during inserting default permissions: {e}")

def initialize_database():
    """Initialize the SQLite database.

    Creates the database file if it doesn't exist, sets up tables, triggers,
    default roles, permissions, and prompts for the creation of an admin user.

    Returns:
        None
    """
    if not os.path.exists(DATABASE_URL):
        @with_connection
        def create_tables(conn):
            cursor = conn.cursor()

            # Create roles table
            cursor.execute(
                """
                CREATE TABLE roles (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE
                )
                """
            )

            # Create users table
            cursor.execute(
                """
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY,
                    username TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    role_id INTEGER NOT NULL,
                    email TEXT NOT NULL UNIQUE,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE
                )
                """
            )

            # Create profiles table
            cursor.execute(
                """
                CREATE TABLE profiles (
                    user_id INTEGER PRIMARY KEY,
                    bio TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
                """
            )

            # Create clients table with UNIQUE constraint
            cursor.execute(
                """
                CREATE TABLE clients (
                    id INTEGER PRIMARY KEY,
                    first_name TEXT NOT NULL,
                    last_name TEXT NOT NULL,
                    email TEXT NOT NULL UNIQUE,
                    phone TEXT,
                    company_name TEXT,
                    last_contact DATE,
                    sales_contact_id INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (sales_contact_id) REFERENCES users(id) ON DELETE SET NULL,
                    UNIQUE (first_name, last_name, company_name)
                )
                """
            )

            # Create contracts table with UNIQUE constraint
            cursor.execute(
                """
                CREATE TABLE contracts (
                    id INTEGER PRIMARY KEY,
                    client_id INTEGER NOT NULL,
                    sales_contact_id INTEGER,
                    total_amount REAL NOT NULL,
                    amount_remaining REAL NOT NULL,
                    status TEXT NOT NULL CHECK (status IN ('Signed', 'Not Signed')),
                    date_created DATE DEFAULT CURRENT_DATE,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE,
                    FOREIGN KEY (sales_contact_id) REFERENCES users(id) ON DELETE SET NULL,
                    UNIQUE (client_id, total_amount, status, date_created)
                )
                """
            )

            # Create events table
            cursor.execute(
                """
                CREATE TABLE events (
                    id INTEGER PRIMARY KEY,
                    contract_id INTEGER NOT NULL,
                    support_contact_id INTEGER,
                    event_date_start DATETIME NOT NULL,
                    event_date_end DATETIME NOT NULL,
                    location TEXT,
                    attendees INTEGER,
                    notes TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (contract_id) REFERENCES contracts(id) ON DELETE CASCADE,
                    FOREIGN KEY (support_contact_id) REFERENCES users(id) ON DELETE SET NULL,
                    UNIQUE (contract_id, event_date_start, event_date_end, location)
                )
                """
            )

            # Create permissions table
            cursor.execute(
                """
                CREATE TABLE permissions (
                    id INTEGER PRIMARY KEY,
                    role_id INTEGER NOT NULL,
                    entity TEXT NOT NULL,
                    action TEXT NOT NULL,
                    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE
                )
                """
            )

            # Create triggers to auto-update updated_at fields
            # For users table
            cursor.execute(
                """
                CREATE TRIGGER update_users_updated_at
                BEFORE UPDATE ON users
                FOR EACH ROW
                BEGIN
                    NEW.updated_at = CURRENT_TIMESTAMP;
                END;
                """
            )

            # For clients table
            cursor.execute(
                """
                CREATE TRIGGER update_clients_updated_at
                BEFORE UPDATE ON clients
                FOR EACH ROW
                BEGIN
                    NEW.updated_at = CURRENT_TIMESTAMP;
                END;
                """
            )

            # For contracts table
            cursor.execute(
                """
                CREATE TRIGGER update_contracts_updated_at
                BEFORE UPDATE ON contracts
                FOR EACH ROW
                BEGIN
                    NEW.updated_at = CURRENT_TIMESTAMP;
                END;
                """
            )

            # For events table
            cursor.execute(
                """
                CREATE TRIGGER update_events_updated_at
                BEFORE UPDATE ON events
                FOR EACH ROW
                BEGIN
                    NEW.updated_at = CURRENT_TIMESTAMP;
                END;
                """
            )

            conn.commit()
            logging.info("Database initialized with all tables and triggers.")
            print("Database initialized successfully.")

        # Create tables and triggers
        create_tables()

        # Create default roles
        create_role('Management')
        create_role('Commercial')
        create_role('Support')

        # Insert default permissions
        insert_default_permissions()

        # Create admin user interactively
        admin_username = input("Enter admin username: ")
        admin_email = input("Enter admin email: ")
        admin_password = getpass.getpass("Enter admin password: ")

        # Get role_id for 'Management'
        @with_connection
        def get_role_id(conn, role_name):
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM roles WHERE name = ?", (role_name,))
            role = cursor.fetchone()
            return role[0] if role else None

        role_id = get_role_id('Management')
        if role_id:
            create_user(admin_username, admin_password, role_id, admin_email)
            print(f"Admin user '{admin_username}' created.")
        else:
            print("Error: 'Management' role not found.")

    else:
        print("Database already exists. Initialization skipped.")

if __name__ == "__main__":
    initialize_database()
