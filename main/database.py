import bcrypt
import sqlite3
import logging
import os
import getpass
import sys
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_FOLDER = os.path.join(BASE_DIR, "db_folder")
DATABASE_URL = os.path.join(DATABASE_FOLDER, "app.db")

if not os.path.exists(DATABASE_FOLDER):
    os.makedirs(DATABASE_FOLDER)

DEBUG = os.getenv("DEBUG", "False") == "True"

logging.basicConfig(
    filename="app.log",
    level=logging.DEBUG if DEBUG else logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)



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

def create_connection():
    """Create a database connection."""
    try:
        conn = sqlite3.connect(DATABASE_URL)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn
    except sqlite3.Error as e:
        logging.error(f"Database connection error: {e}")
        print(f"Database connection error: {e}")
        return None

def create_tables_and_triggers(conn):
    try:
        cursor = conn.cursor()
        schema_sql = """
        /*
            This database schema sets up a foundation for Epic Events CRM, similar to the previous design, but simplified to avoid any SQLite-specific pitfalls. The logic and constraints remain effectively the same, but we’ll use standard SQLite-compatible syntax.

            Changes from previous attempts:
            - No "IF NOT EXISTS" for triggers.
            - No "SET" keyword in triggers.
            - Using standard SQLite-compatible data types and syntax.
            - Decimals will be stored as REAL because SQLite doesn’t have a DECIMAL type; checks remain to ensure valid values.
            - Ensuring all columns and constraints are compatible with SQLite.

            This schema uses:
            - Roles, Users, Clients, Contracts, Events, Permissions tables.
            - Triggers to auto-update updated_at on update.
            - Indexes on foreign key columns.

            We will rely on REAL for amounts since SQLite stores numeric values as REAL; checks still enforce numeric constraints.
            */

            -- Roles Table
            CREATE TABLE IF NOT EXISTS roles   (
            name TEXT PRIMARY KEY
            );

            INSERT INTO roles (name) VALUES 
                ('Management'),
                ('Commercial'),
                ('Support');

            -- Users Table
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password_hash TEXT NOT NULL,
                role_id TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (role_id) REFERENCES roles(name)
            );

            -- Profiles Table
            CREATE TABLE IF NOT EXISTS profiles  (
                user_id TEXT PRIMARY KEY,
                bio TEXT,
                FOREIGN KEY (user_id) REFERENCES users(username)
            );

            -- Clients Table
            CREATE TABLE IF NOT EXISTS clients  (
                email TEXT PRIMARY KEY,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                phone TEXT,
                company_name TEXT,
                last_contact TEXT, -- SQLite date
                sales_contact_id TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (sales_contact_id) REFERENCES users(username),
                UNIQUE (first_name, last_name, company_name)
            );

            -- Contracts Table
            CREATE TABLE IF NOT EXISTS contracts  (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id TEXT NOT NULL,
                sales_contact_id TEXT,
                total_amount REAL NOT NULL CHECK (total_amount >= 0),
                amount_remaining REAL NOT NULL CHECK (amount_remaining >= 0),
                status TEXT NOT NULL CHECK (status IN ('Signed', 'Not Signed')),
                date_created TEXT DEFAULT (date('now')),
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now')),
                CHECK (amount_remaining <= total_amount),
                FOREIGN KEY (client_id) REFERENCES clients(email),
                FOREIGN KEY (sales_contact_id) REFERENCES users(username)
            );

            -- Events Table
            CREATE TABLE IF NOT EXISTS events  (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contract_id INTEGER NOT NULL,
                support_contact_id TEXT,
                event_date_start TEXT NOT NULL,
                event_date_end TEXT NOT NULL,
                location TEXT,
                attendees INTEGER,
                notes TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (contract_id) REFERENCES contracts(id),
                FOREIGN KEY (support_contact_id) REFERENCES users(username)
            );

            -- Permissions Table
            CREATE TABLE IF NOT EXISTS permissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role_id TEXT NOT NULL,
                entity TEXT NOT NULL,
                action TEXT NOT NULL,
                FOREIGN KEY (role_id) REFERENCES roles(name),
                CHECK (entity IN ('client', 'contract', 'event', 'user')),
                CHECK (action IN ('create', 'read', 'update', 'delete'))
            );

            -- Insert Management Permissions
            INSERT INTO permissions (role_id, entity, action) VALUES
                ('Management', 'client', 'create'),
                ('Management', 'client', 'read'),
                ('Management', 'client', 'update'),
                ('Management', 'client', 'delete'),
                ('Management', 'contract', 'create'),
                ('Management', 'contract', 'read'),
                ('Management', 'contract', 'update'),
                ('Management', 'contract', 'delete'),
                ('Management', 'event', 'create'),
                ('Management', 'event', 'read'),
                ('Management', 'event', 'update'),
                ('Management', 'event', 'delete'),
                ('Management', 'user', 'create'),
                ('Management', 'user', 'read'),
                ('Management', 'user', 'update'),
                ('Management', 'user', 'delete');

            -- Insert Commercial Permissions
            INSERT INTO permissions (role_id, entity, action) VALUES
                ('Commercial', 'client', 'create'),
                ('Commercial', 'client', 'read'),
                ('Commercial', 'client', 'update'),
                ('Commercial', 'contract', 'create'),
                ('Commercial', 'contract', 'read'),
                ('Commercial', 'contract', 'update'),
                ('Commercial', 'event', 'create'),
                ('Commercial', 'event', 'read');

            -- Insert Support Permissions
            INSERT INTO permissions (role_id, entity, action) VALUES
                ('Support', 'event', 'read'),
                ('Support', 'event', 'update'),
                ('Support', 'client', 'read'),
                ('Support', 'contract', 'read');

            -- Create indexes for better performance
            CREATE INDEX idx_users_role ON users(role_id);
            CREATE INDEX idx_clients_sales_contact ON clients(sales_contact_id);
            CREATE INDEX idx_contracts_client ON contracts(client_id);
            CREATE INDEX idx_contracts_sales_contact ON contracts(sales_contact_id);
            CREATE INDEX idx_events_contract ON events(contract_id);
            CREATE INDEX idx_events_support_contact ON events(support_contact_id);

            -- Create triggers for updated_at timestamps
            CREATE TRIGGER users_updated_at_trigger 
                AFTER UPDATE ON users
            BEGIN
                UPDATE users SET updated_at = datetime('now')
                WHERE username = NEW.username;
            END;

            CREATE TRIGGER clients_updated_at_trigger
                AFTER UPDATE ON clients
            BEGIN
                UPDATE clients SET updated_at = datetime('now')
                WHERE email = NEW.email;
            END;

            CREATE TRIGGER contracts_updated_at_trigger
                AFTER UPDATE ON contracts
            BEGIN
                UPDATE contracts SET updated_at = datetime('now')
                WHERE id = NEW.id;
            END;

            CREATE TRIGGER events_updated_at_trigger
                AFTER UPDATE ON events
            BEGIN
                UPDATE events SET updated_at = datetime('now')
                WHERE id = NEW.id;
            END;
            """
        cursor.executescript(schema_sql)
        conn.commit()
        logging.info("Tables, triggers, and indexes created successfully.")
        print("Tables, triggers, and indexes created successfully.")
    except sqlite3.Error as e:
        logging.error(f"Error during table and trigger creation: {e}")
        print(f"Error during table and trigger creation: {e}")
        conn.rollback()
        conn.close()
        if os.path.exists(DATABASE_URL):
            os.remove(DATABASE_URL)
        sys.exit(1)

def get_role_id(conn, role_name):
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM roles WHERE name = ?", (role_name,))
    role = cursor.fetchone()
    return role['name'] if role else None

def create_user(conn, username, password, role_id, email):
    password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    password_hash_str = password_hash.decode("utf-8")

    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (username, email, password_hash, role_id) VALUES (?, ?, ?, ?)",
            (username, email, password_hash_str, role_id),
        )
        conn.commit()
        logging.info(f"User '{username}' created successfully with role '{role_id}'.")
        print(f"User '{username}' created with role '{role_id}'.")
    except sqlite3.IntegrityError as e:
        logging.warning(f"User '{username}' or email '{email}' already exists. Error: {e}")
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
    if os.path.exists(DATABASE_URL):
        print("Database already exists. Initialization skipped.")
        return

    email_pattern = r"^[^@]+@[^@]+\.[^@]+$"
    print("Please enter admin user details to initialize the database.")
    admin_username = input("Enter admin username: ").strip()

    while True:
        admin_email = input("Enter admin email: ").strip()
        if re.match(email_pattern, admin_email):
            break
        else:
            print("Invalid email format. Please enter a valid email (e.g., user@example.com).")

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

    conn = create_connection()
    try:
        create_tables_and_triggers(conn)
        role_id = get_role_id(conn, "Management")
        if role_id:
            create_user(conn, admin_username, admin_password, role_id, admin_email)
            print(f"Admin user '{admin_username}' created successfully.")
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
