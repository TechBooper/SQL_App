import unittest
import sqlite3
from models import User, Client, Database

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
        # First create a user
        User.create(
            username="testuser",
            password="password123",
            role_id=1,
            email="test@example.com"
        )
        
        # Try to create duplicate
        result = User.create(
            username="testuser",
            password="password456",
            role_id=1,
            email="test2@example.com"
        )
        self.assertEqual(result, "A user with this username already exists.")

    def test_get_user_by_username(self):
        # First create a user
        User.create(
            username="testuser",
            password="password123",
            role_id=1,
            email="test@example.com"
        )
        
        # Try to get the user
        user = User.get_by_username("testuser")
        self.assertIsNotNone(user)
        self.assertIsInstance(user, User)
        self.assertEqual(user.username, "testuser")

    def test_update_user(self):
        # First create a user
        user = User.create(
            username="testuser",
            password="password123",
            role_id=1,
            email="test@example.com"
        )
        
        # Update the user
        user.email = "updated@example.com"
        result = user.update()
        self.assertTrue(result)
        
        # Verify update
        updated_user = User.get_by_username("testuser")
        self.assertEqual(updated_user.email, "updated@example.com")

    def test_delete_user(self):
        # First create a user
        user = User.create(
            username="testuser",
            password="password123",
            role_id=1,
            email="test@example.com"
        )
        
        # Delete the user
        result = user.delete()
        self.assertTrue(result)
        
        # Verify deletion
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
        # First create a client
        Client.create(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            phone="1234567890",
            company_name="Test Company",
            sales_contact_id=1
        )
        
        # Try to create duplicate
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
        # First create a client
        client = Client.create(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            phone="1234567890",
            company_name="Test Company",
            sales_contact_id=1
        )
        
        # Update the client
        client.phone = "987654321"
        result = client.update()
        self.assertTrue(result)
        
        # Verify update
        updated_client = Client.get_by_email("john@example.com")
        self.assertEqual(updated_client.phone, "987654321")

    def test_delete_client(self):
        # First create a client
        client = Client.create(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            phone="1234567890",
            company_name="Test Company",
            sales_contact_id=1
        )
        
        # Delete the client
        result = client.delete()
        self.assertTrue(result)
        
        # Verify deletion
        deleted_client = Client.get_by_email("john@example.com")
        self.assertIsNone(deleted_client)

if __name__ == '__main__':
    unittest.main()