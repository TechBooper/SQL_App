import unittest
import os
import sqlite3
import tempfile
import logging
import bcrypt
from unittest.mock import patch, MagicMock
from io import StringIO
import sys
import re
import getpass


class TestDatabaseInitialization(unittest.TestCase):
    def setUp(self):
        # Redirect stdout to capture printed output
        self.original_stdout = sys.stdout
        sys.stdout = StringIO()

        # Create a temporary directory structure that includes a "database" folder
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database_dir = os.path.join(self.temp_dir.name, "database")
        os.makedirs(self.database_dir, exist_ok=True)
        self.db_path = os.path.join(self.database_dir, "app.db")

        # Create patch objects but don't start them yet
        self.patches = [
            patch("main.database.DATABASE_FOLDER", self.database_dir),
            patch("main.database.DATABASE_URL", self.db_path),
            patch("main.DATABASE_FOLDER", self.database_dir),
            patch("main.DATABASE_URL", self.db_path),
        ]

        # Start all patches
        self.mocks = [p.start() for p in self.patches]

        # Adjust logging to avoid file creation and to prevent noise during tests
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        # Stop all patches
        for p in self.patches:
            p.stop()

        # Restore stdout
        sys.stdout = self.original_stdout

        # Cleanup the temporary directory
        self.temp_dir.cleanup()

        # Re-enable logging
        logging.disable(logging.NOTSET)

    def test_is_password_strong(self):
        from main.database import is_password_strong

        self.assertFalse(is_password_strong("weak"))
        self.assertFalse(is_password_strong("abcdABCD"))  # No digit
        self.assertFalse(is_password_strong("abc12345"))  # No uppercase
        self.assertTrue(is_password_strong("Abcd1234"))

    def test_create_database_connection(self):
        from main.database import create_connection

        conn = create_connection()
        self.assertIsInstance(conn, sqlite3.Connection)
        conn.close()

    def test_create_tables_and_triggers(self):
        from main.database import create_connection, create_tables_and_triggers

        conn = create_connection()
        create_tables_and_triggers(conn)

        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='users';
        """
        )
        self.assertIsNotNone(cursor.fetchone())
        conn.close()

    def test_get_role_id(self):
        from main.database import (
            create_connection,
            create_tables_and_triggers,
            get_role_id,
        )

        conn = create_connection()
        create_tables_and_triggers(conn)

        # Test default roles
        self.assertEqual(get_role_id(conn, "Management"), "Management")
        self.assertEqual(get_role_id(conn, "Commercial"), "Commercial")
        self.assertEqual(get_role_id(conn, "Support"), "Support")

        # Test non-existing role
        self.assertIsNone(get_role_id(conn, "NonExistent"))
        conn.close()

    def test_create_user(self):
        from main.database import (
            create_connection,
            create_tables_and_triggers,
            create_user,
        )

        conn = create_connection()
        create_tables_and_triggers(conn)

        # Test user creation
        test_data = {
            "username": "admin_user",
            "password": "StrongP4ss!",
            "email": "admin@example.com",
            "role_id": "Management",
        }

        create_user(conn, **test_data)

        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT * FROM users WHERE username=?
        """,
            (test_data["username"],),
        )

        user = cursor.fetchone()
        self.assertIsNotNone(user)
        self.assertEqual(user["username"], test_data["username"])
        self.assertEqual(user["email"], test_data["email"])
        self.assertEqual(user["role_id"], test_data["role_id"])

        # Verify password hash
        self.assertTrue(
            bcrypt.checkpw(
                test_data["password"].encode("utf-8"),
                user["password_hash"].encode("utf-8"),
            )
        )
        conn.close()

    @patch("builtins.input", side_effect=["admin", "admin@example.com"])
    @patch("getpass.getpass", side_effect=["StrongP4ss!", "StrongP4ss!"])
    def test_initialize_database(self, mock_getpass, mock_input):
        from main.database import initialize_database

        initialize_database()

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE username='admin'")
        user = cursor.fetchone()

        self.assertIsNotNone(user)
        self.assertEqual(user["username"], "admin")
        self.assertEqual(user["email"], "admin@example.com")
        self.assertEqual(user["role_id"], "Management")
        conn.close()

    @patch("builtins.input", side_effect=["admin", "not-an-email", "admin@example.com"])
    @patch("getpass.getpass", side_effect=["StrongP4ss!", "StrongP4ss!"])
    def test_initialize_database_invalid_email(self, mock_getpass, mock_input):
        from main.database import initialize_database

        initialize_database()

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE username='admin'")
        user = cursor.fetchone()

        self.assertIsNotNone(user)
        self.assertEqual(user["email"], "admin@example.com")
        conn.close()

    @patch("builtins.input", side_effect=["admin", "admin@example.com"])
    @patch(
        "getpass.getpass",
        side_effect=["weakpass", "weakpass", "StrongP4ss!", "StrongP4ss!"],
    )
    def test_initialize_database_weak_password(self, mock_getpass, mock_input):
        from main.database import initialize_database

        initialize_database()

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE username='admin'")
        user = cursor.fetchone()

        self.assertIsNotNone(user)
        self.assertTrue(
            bcrypt.checkpw(b"StrongP4ss!", user["password_hash"].encode("utf-8"))
        )
        conn.close()

    @patch("builtins.input", side_effect=["admin", "admin@example.com"])
    @patch(
        "getpass.getpass",
        side_effect=["StrongP4ss!", "MismatchP4ss!", "StrongP4ss!", "StrongP4ss!"],
    )
    def test_initialize_database_password_mismatch(self, mock_getpass, mock_input):
        from main.database import initialize_database

        initialize_database()

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE username='admin'")
        user = cursor.fetchone()

        self.assertIsNotNone(user)
        self.assertTrue(
            bcrypt.checkpw(b"StrongP4ss!", user["password_hash"].encode("utf-8"))
        )
        conn.close()


if __name__ == "__main__":
    unittest.main()
