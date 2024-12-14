import unittest
import sqlite3
from models import User, Client, Contract, Event, Role, Permission, Database

class TestModels(unittest.TestCase):
    def setUp(self):
        # Create a new in-memory database for each test
        self.connection = sqlite3.connect(":memory:")
        self.connection.row_factory = sqlite3.Row
        
        # Override the Database.connect method to use our test database
        def get_test_connection():
            return self.connection
        Database.connect = get_test_connection
        
        # Create the schema
        self.cursor = self.connection.cursor()
        self.cursor.executescript("""
        CREATE TABLE roles (
            name TEXT PRIMARY KEY
        );

        CREATE TABLE users (
            username TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL,
            role_id TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (role_id) REFERENCES roles(name)
        );

        CREATE TABLE clients (
            email TEXT PRIMARY KEY,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            phone TEXT,
            company_name TEXT,
            last_contact TEXT,
            sales_contact_id TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (sales_contact_id) REFERENCES users(username),
            UNIQUE (first_name, last_name, company_name)
        );

        CREATE TABLE contracts (
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

        CREATE TABLE events (
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

        CREATE TABLE permissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role_id TEXT NOT NULL,
            entity TEXT NOT NULL,
            action TEXT NOT NULL,
            FOREIGN KEY (role_id) REFERENCES roles(name),
            CHECK (entity IN ('client', 'contract', 'event', 'user')),
            CHECK (action IN ('create', 'read', 'update', 'delete'))
        );
        """)
        self.connection.commit()

        # Insert test role
        self.cursor.execute("INSERT INTO roles (name) VALUES ('Management')")
        self.connection.commit()

    def tearDown(self):
        # Clean up the database after each test
        self.cursor.executescript("""
            DELETE FROM events;
            DELETE FROM contracts;
            DELETE FROM clients;
            DELETE FROM users;
            DELETE FROM roles;
            DELETE FROM permissions;
        """)
        self.connection.commit()
        self.connection.close()

    def test_create_user_success(self):
        result = User.create("test_user", "password", "Management", "test@example.com")
        self.assertIsInstance(result, User)
        self.assertEqual(result.username, "test_user")
        self.assertTrue(result.verify_password("password"))

    def test_create_user_duplicate_username(self):
        User.create("test_user", "password", "Management", "test@example.com")
        result = User.create("test_user", "password123", "Management", "new@example.com")
        self.assertEqual(result, "A user with this username already exists.")

    def test_get_user_by_username(self):
        User.create("test_user", "password", "Management", "test@example.com")
        user = User.get_by_username("test_user")
        self.assertIsNotNone(user)
        self.assertEqual(user.username, "test_user")

    def test_update_user(self):
        user = User.create("test_user", "password", "Management", "test@example.com")
        user.email = "updated@example.com"
        result = user.update()
        self.assertTrue(result)
        updated_user = User.get_by_username("test_user")
        self.assertEqual(updated_user.email, "updated@example.com")

    def test_delete_user(self):
        user = User.create("test_user", "password", "Management", "test@example.com")
        self.assertTrue(user.delete())
        self.assertIsNone(User.get_by_username("test_user"))

    def test_create_client_success(self):
        User.create("sales_user", "password", "Management", "sales@example.com")
        result = Client.create(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            phone="123456789",
            company_name="CompanyX",
            sales_contact_id="sales_user"
        )
        self.assertIsInstance(result, Client)
        self.assertEqual(result.email, "john@example.com")

    def test_create_duplicate_client(self):
        User.create("sales_user", "password", "Management", "sales@example.com")
        Client.create("John", "Doe", "john@example.com", "123456789", "CompanyX", "sales_user")
        result = Client.create("John", "Doe", "another@example.com", "987654321", "CompanyX", "sales_user")
        self.assertEqual(result, "A client with this first name, last name, and company already exists.")

    def test_update_client(self):
        User.create("sales_user", "password", "Management", "sales@example.com")
        client = Client.create("John", "Doe", "john@example.com", "123456789", "CompanyX", "sales_user")
        client.phone = "987654321"
        result = client.update()
        self.assertTrue(result)
        updated_client = Client.get_by_email("john@example.com")
        self.assertEqual(updated_client.phone, "987654321")

    def test_delete_client(self):
        User.create("sales_user", "password", "Management", "sales@example.com")
        client = Client.create("John", "Doe", "john@example.com", "123456789", "CompanyX", "sales_user")
        self.assertTrue(client.delete())
        self.assertIsNone(Client.get_by_email("john@example.com"))

if __name__ == "__main__":
    unittest.main()