import unittest
from main.models import User, Client, Contract, Event, Role, Permission, Database

class TestModels(unittest.TestCase):
    def setUp(self):
        # Setup test database connection
        self.conn = Database.connect()
        self.cursor = self.conn.cursor()

        # Create tables if they do not exist
        self.cursor.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password_hash TEXT NOT NULL,
                role_id TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS clients (
                email TEXT PRIMARY KEY,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                phone TEXT NOT NULL,
                company_name TEXT NOT NULL,
                sales_contact_id TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS contracts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id TEXT NOT NULL,
                sales_contact_id TEXT NOT NULL,
                total_amount REAL NOT NULL,
                amount_remaining REAL NOT NULL,
                status TEXT CHECK(status IN ('Signed', 'Not Signed')) NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contract_id INTEGER NOT NULL,
                support_contact_id TEXT,
                event_date_start TEXT NOT NULL,
                event_date_end TEXT NOT NULL,
                location TEXT NOT NULL,
                attendees INTEGER NOT NULL,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS permissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role_id TEXT NOT NULL,
                entity TEXT NOT NULL,
                action TEXT NOT NULL
            );
        """)

        # Clear all tables before each test
        self.cursor.executescript("""
            DELETE FROM events;
            DELETE FROM contracts;
            DELETE FROM clients;
            DELETE FROM users;
            DELETE FROM permissions;
        """)
        self.conn.commit()

    def tearDown(self):
        # Clear all tables after each test
        try:
            self.cursor.executescript("""
                DELETE FROM events;
                DELETE FROM contracts;
                DELETE FROM clients;
                DELETE FROM users;
                DELETE FROM permissions;
            """)
            self.conn.commit()
        finally:
            self.cursor.close()
            self.conn.close()

    # User Tests
    def test_create_user_success(self):
        result = User.create(
            username="testuser",
            password="password123",
            role_id="Management",
            email="test@example.com"
        )
        self.assertIsInstance(result, User)
        self.assertEqual(result.username, "testuser")

    def test_create_user_duplicate_email(self):
        User.create(
            username="testuser1",
            password="password123",
            role_id="Management",
            email="duplicate@example.com"
        )
        result = User.create(
            username="testuser2",
            password="password456",
            role_id="Support",
            email="duplicate@example.com"
        )
        self.assertEqual(result, "A user with this email already exists.")

    def test_update_user(self):
        user = User.create(
            username="testuser",
            password="password123",
            role_id="Management",
            email="test@example.com"
        )
        user.email = "updated@example.com"
        result = user.update()
        self.assertTrue(result)
        updated_user = User.get_by_username("testuser")
        self.assertEqual(updated_user.email, "updated@example.com")

    def test_delete_user(self):
        user = User.create(
            username="testuser",
            password="password123",
            role_id="Management",
            email="test@example.com"
        )
        result = user.delete()
        self.assertTrue(result)
        deleted_user = User.get_by_username("testuser")
        self.assertIsNone(deleted_user)

    # Client Tests
    def test_create_client_success(self):
        result = Client.create(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            phone="1234567890",
            company_name="TestCorp",
            sales_contact_id="testuser"
        )
        self.assertIsInstance(result, Client)
        self.assertEqual(result.email, "john@example.com")



    def test_delete_client(self):
        client = Client.create(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            phone="1234567890",
            company_name="TestCorp",
            sales_contact_id="testuser"
        )
        result = client.delete()
        self.assertTrue(result)
        deleted_client = Client.get_by_email("john@example.com")
        self.assertIsNone(deleted_client)

    # Contract Tests
    def test_create_contract_success(self):
        result = Contract.create(
            client_id="john@example.com",
            sales_contact_id="salesuser",
            total_amount=1000.0,
            amount_remaining=500.0,
            status="Signed"
        )
        self.assertIsInstance(result, Contract)
        self.assertEqual(result.total_amount, 1000.0)

    def test_update_contract(self):
        contract = Contract.create(
            client_id="john@example.com",
            sales_contact_id="salesuser",
            total_amount=1000.0,
            amount_remaining=500.0,
            status="Signed"
        )
        contract.amount_remaining = 200.0
        result = contract.update()
        self.assertTrue(result)
        updated_contract = Contract.get_by_id(contract.id)
        self.assertEqual(updated_contract.amount_remaining, 200.0)

    def test_delete_contract(self):
        contract = Contract.create(
            client_id="john@example.com",
            sales_contact_id="salesuser",
            total_amount=1000.0,
            amount_remaining=500.0,
            status="Signed"
        )
        result = contract.delete()
        self.assertTrue(result)
        deleted_contract = Contract.get_by_id(contract.id)
        self.assertIsNone(deleted_contract)

    # Event Tests
    def test_create_event_success(self):
        result = Event.create(
            contract_id=1,
            support_contact_id="supportuser",
            event_date_start="2024-01-01",
            event_date_end="2024-01-02",
            location="Test Location",
            attendees=50,
            notes="Test Event"
        )
        self.assertIsInstance(result, Event)
        self.assertEqual(result.location, "Test Location")

    def test_update_event(self):
        event = Event.create(
            contract_id=1,
            support_contact_id="supportuser",
            event_date_start="2024-01-01",
            event_date_end="2024-01-02",
            location="Test Location",
            attendees=50,
            notes="Test Event"
        )
        event.notes = "Updated Notes"
        result = event.update()
        self.assertTrue(result)
        updated_event = Event.get_by_id(event.id)
        self.assertEqual(updated_event.notes, "Updated Notes")

    def test_delete_event(self):
        event = Event.create(
            contract_id=1,
            support_contact_id="supportuser",
            event_date_start="2024-01-01",
            event_date_end="2024-01-02",
            location="Test Location",
            attendees=50,
            notes="Test Event"
        )
        result = event.delete()
        self.assertTrue(result)
        deleted_event = Event.get_by_id(event.id)
        self.assertIsNone(deleted_event)

    # Permission Tests
    def test_create_permission(self):
        self.cursor.execute(
            "INSERT INTO permissions (role_id, entity, action) VALUES (?, ?, ?)",
            ("Management", "user", "create")
        )
        self.conn.commit()
        permissions = Permission.get_permissions_by_role("Management")
        self.assertEqual(len(permissions), 1)
        self.assertEqual(permissions[0].entity, "user")

    def test_has_permission(self):
        self.cursor.execute(
            "INSERT INTO permissions (role_id, entity, action) VALUES (?, ?, ?)",
            ("Management", "user", "create")
        )
        self.conn.commit()
        result = Permission.has_permission("Management", "user", "create")
        self.assertTrue(result)

if __name__ == '__main__':
    unittest.main()
