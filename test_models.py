import unittest
import sqlite3
from models import User, Client, Contract, Event, Role, Database

class TestModels(unittest.TestCase):
    def setUp(self):
        # Setup test database connection
        self.conn = Database.connect()
        self.cursor = self.conn.cursor()

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

    def test_create_user_success(self):
        result = User.create(
            username="testuser",
            password="password123",
            role_id=1,
            email="test@example.com"
        )
        self.assertIsInstance(result, User)
        self.assertEqual(result.username, "testuser")
        self.assertEqual(result.email, "test@example.com")

    def test_create_user_duplicate_username(self):
        User.create(
            username="testuser",
            password="password123",
            role_id=1,
            email="test@example.com"
        )
        result = User.create(
            username="testuser",
            password="password456",
            role_id=1,
            email="test2@example.com"
        )
        self.assertEqual(result, "A user with this username already exists.")

    def test_get_user_by_username(self):
        User.create(
            username="testuser",
            password="password123",
            role_id=1,
            email="test@example.com"
        )
        user = User.get_by_username("testuser")
        self.assertIsNotNone(user)
        self.assertIsInstance(user, User)
        self.assertEqual(user.username, "testuser")

    def test_update_user(self):
        user = User.create(
            username="testuser",
            password="password123",
            role_id=1,
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
            role_id=1,
            email="test@example.com"
        )
        result = user.delete()
        self.assertTrue(result)
        deleted_user = User.get_by_username("testuser")
        self.assertIsNone(deleted_user)

    def test_create_client_success(self):
        result = Client.create(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            phone="1234567890",
            company_name="Test Company",
            sales_contact_id=1
        )
        self.assertIsInstance(result, Client)
        self.assertEqual(result.email, "john@example.com")

    def test_create_duplicate_client(self):
        Client.create(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            phone="1234567890",
            company_name="Test Company",
            sales_contact_id=1
        )
        result = Client.create(
            first_name="John",
            last_name="Doe",
            email="john2@example.com",
            phone="0987654321",
            company_name="Test Company",
            sales_contact_id=1
        )
        self.assertEqual(result, "A client with this first name, last name, and company already exists.")

    def test_update_client(self):
        client = Client.create(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            phone="1234567890",
            company_name="Test Company",
            sales_contact_id=1
        )
        client.phone = "987654321"
        result = client.update()
        self.assertTrue(result)
        updated_client = Client.get_by_email("john@example.com")
        self.assertEqual(updated_client.phone, "987654321")

    def test_delete_client(self):
        client = Client.create(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            phone="1234567890",
            company_name="Test Company",
            sales_contact_id=1
        )
        result = client.delete()
        self.assertTrue(result)
        deleted_client = Client.get_by_email("john@example.com")
        self.assertIsNone(deleted_client)

    def test_create_contract_success(self):
        result = Contract.create(
            client_id="john@example.com",
            sales_contact_id="sales_user",
            total_amount=1000.0,
            amount_remaining=500.0,
            status="Signed"
        )
        self.assertIsInstance(result, Contract)
        self.assertEqual(result.total_amount, 1000.0)
        self.assertEqual(result.status, "Signed")

    def test_update_contract(self):
        contract = Contract.create(
            client_id="john@example.com",
            sales_contact_id="sales_user",
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
            sales_contact_id="sales_user",
            total_amount=1000.0,
            amount_remaining=500.0,
            status="Signed"
        )
        result = contract.delete()
        self.assertTrue(result)
        deleted_contract = Contract.get_by_id(contract.id)
        self.assertIsNone(deleted_contract)

    def test_create_event_success(self):
        result = Event.create(
            contract_id=1,
            support_contact_id="support_user",
            event_date_start="2024-01-01",
            event_date_end="2024-01-02",
            location="Test Location",
            attendees=100,
            notes="Event Notes"
        )
        self.assertIsInstance(result, Event)
        self.assertEqual(result.location, "Test Location")

    def test_update_event(self):
        event = Event.create(
            contract_id=1,
            support_contact_id="support_user",
            event_date_start="2024-01-01",
            event_date_end="2024-01-02",
            location="Test Location",
            attendees=100,
            notes="Event Notes"
        )
        event.notes = "Updated Notes"
        result = event.update()
        self.assertTrue(result)
        updated_event = Event.get_by_id(event.id)
        self.assertEqual(updated_event.notes, "Updated Notes")

    def test_delete_event(self):
        event = Event.create(
            contract_id=1,
            support_contact_id="support_user",
            event_date_start="2024-01-01",
            event_date_end="2024-01-02",
            location="Test Location",
            attendees=100,
            notes="Event Notes"
        )
        result = event.delete()
        self.assertTrue(result)
        deleted_event = Event.get_by_id(event.id)
        self.assertIsNone(deleted_event)

if __name__ == '__main__':
    unittest.main()
