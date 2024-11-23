"""
Database initialization and user creation module for Epic Events CRM.

This module handles the setup of the SQLite database, including table creation,
inserting default roles and permissions, and creating the initial admin user.
It also includes utility functions for password validation and user creation.
"""

import bcrypt
import sqlite3
import logging
import os
import getpass
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__),))
DATABASE_FOLDER = os.path.join(BASE_DIR, 'database')
DATABASE_URL = os.path.join(DATABASE_FOLDER, 'app.db')

if not os.path.exists(DATABASE_FOLDER):
    os.makedirs(DATABASE_FOLDER)  # Create the 'database' folder if it doesn't exist

DEBUG = os.getenv("DEBUG") == "True"

# Configure logging to output to a file
logging.basicConfig(
    filename="app.log",  # Log file
    level=logging.DEBUG if DEBUG else logging.INFO,  # Log level
    format="%(asctime)s - %(levelname)s - %(message)s",  # Log format
)

def is_password_strong(password):
    """Check if the provided password meets strength requirements."""
    if len(password) < 8:
        return False
    if not any(char.isdigit() for char in password):
        return False
    if not any(char.isupper() for char in password):
        return False
    if not any(char.islower() for char in password):
        return False
    return True

def create_database_connection():
    """Create a database connection to the SQLite database."""
    try:
        conn = sqlite3.connect(DATABASE_URL)
        conn.row_factory = sqlite3.Row  # Enable access to columns by name
        return conn
    except sqlite3.Error as e:
        logging.error(f"Database connection error: {e}")
        print(f"Database connection error: {e}")
        sys.exit(1)

def create_tables(conn):
    """Create the necessary tables and triggers in the database."""
    try:
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

        # Create clients table
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
                FOREIGN KEY (sales_contact_id) REFERENCES users(id) ON DELETE SET NULL
            )
            """
        )

        # Create contracts table
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
                FOREIGN KEY (sales_contact_id) REFERENCES users(id) ON DELETE SET NULL
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
                FOREIGN KEY (support_contact_id) REFERENCES users(id) ON DELETE SET NULL
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
        tables_with_updated_at = ['users', 'clients', 'contracts', 'events']
        for table in tables_with_updated_at:
            cursor.execute(
                f"""
                CREATE TRIGGER update_{table}_updated_at
                AFTER UPDATE ON {table}
                FOR EACH ROW
                BEGIN
                    UPDATE {table} SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
                END;
                """
            )

        conn.commit()
        logging.info("Database initialized with all tables and triggers.")
        print("Database initialized successfully.")
    except sqlite3.Error as e:
        logging.error(f"Error during database initialization: {e}")
        print(f"Error during database initialization: {e}")
        conn.rollback()
        conn.close()
        if os.path.exists(DATABASE_URL):
            os.remove(DATABASE_URL)
        sys.exit(1)

def create_role(conn, name):
    """Create a new role in the database."""
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
        conn.rollback()
        conn.close()
        if os.path.exists(DATABASE_URL):
            os.remove(DATABASE_URL)
        sys.exit(1)

def insert_default_permissions(conn):
    """Insert default permissions into the database."""
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
        conn.rollback()
        conn.close()
        if os.path.exists(DATABASE_URL):
            os.remove(DATABASE_URL)
        sys.exit(1)

def get_role_id(conn, role_name):
    """Retrieve the role ID for a given role name."""
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM roles WHERE name = ?", (role_name,))
    role = cursor.fetchone()
    return role[0] if role else None

def create_user(conn, username, password, role_id, email):
    """Create a new user in the database."""
    # Hash the password using bcrypt and decode it to a string for storage
    password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    password_hash_str = password_hash.decode("utf-8")

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
        conn.rollback()
        conn.close()
        if os.path.exists(DATABASE_URL):
            os.remove(DATABASE_URL)
        sys.exit(1)
    except sqlite3.Error as e:
        logging.error(f"Error while creating user '{username}': {e}")
        print(f"An error occurred while creating user '{username}': {e}")
        conn.rollback()
        conn.close()
        if os.path.exists(DATABASE_URL):
            os.remove(DATABASE_URL)
        sys.exit(1)

def initialize_database():
    """Initialize the SQLite database."""
    if os.path.exists(DATABASE_URL):
        print("Database already exists. Initialization skipped.")
        return

    # Collect admin user details before creating the database
    print("Please enter admin user details to initialize the database.")
    admin_username = input("Enter admin username: ").strip()
    admin_email = input("Enter admin email: ").strip()

    # Password input and validation
    while True:
        admin_password = getpass.getpass("Enter admin password: ")
        confirm_password = getpass.getpass("Confirm admin password: ")
        if admin_password != confirm_password:
            print("Passwords do not match. Please try again.")
            continue
        if not is_password_strong(admin_password):
            print("Password is not strong enough. It must be at least 8 characters long and include uppercase letters, lowercase letters, and numbers.")
            continue
        break

    # Proceed to create the database and insert data
    conn = create_database_connection()
    try:
        # Create tables and triggers
        create_tables(conn)

        # Create default roles
        create_role(conn, 'Management')
        create_role(conn, 'Commercial')
        create_role(conn, 'Support')

        # Insert default permissions
        insert_default_permissions(conn)

        # Get role_id for 'Management'
        role_id = get_role_id(conn, 'Management')
        if role_id:
            # Create admin user
            create_user(conn, admin_username, admin_password, role_id, admin_email)
            print(f"Admin user '{admin_username}' created.")
            logging.info(f"Admin user '{admin_username}' created successfully.")
            conn.close()
        else:
            print("Error: 'Management' role not found.")
            logging.error("Error: 'Management' role not found.")
            conn.close()
            if os.path.exists(DATABASE_URL):
                os.remove(DATABASE_URL)
            sys.exit(1)
    except Exception as e:
        logging.error(f"Unexpected error during database initialization: {e}")
        print(f"An unexpected error occurred: {e}")
        conn.rollback()
        conn.close()
        if os.path.exists(DATABASE_URL):
            os.remove(DATABASE_URL)
        sys.exit(1)

if __name__ == "__main__":
    initialize_database()
