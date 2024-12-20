import unittest
import sqlite3
from unittest.mock import patch, MagicMock

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from main.auth import create_user, hash_password




class TestAuthModule(unittest.TestCase):
    @patch("main.auth.Role.get_by_name")
    @patch("main.auth.User.create")
    def test_create_user_success(self, mock_user_create, mock_role_get_by_name):
        """
        Test creating a user successfully.
        """
        # Mock role existence
        mock_role_get_by_name.return_value = MagicMock()  # Simulate role exists

        # Mock user creation
        mock_user_obj = MagicMock()
        mock_user_create.return_value = mock_user_obj

        # Call function
        result = create_user("test_user", "password", "Management", "test@test.com")

        # Assertions
        self.assertIsNotNone(result)
        mock_role_get_by_name.assert_called_once_with("Management")
        mock_user_create.assert_called_once_with(
            username="test_user",
            password_hash=unittest.mock.ANY,  # Since the password is hashed
            role_id="Management",
            email="test@test.com"
        )

    @patch("main.auth.Role.get_by_name")
    @patch("main.auth.User.create")
    def test_create_user_invalid_role(self, mock_user_create, mock_role_get_by_name):
        """
        Test creating a user with an invalid role.
        """
        # Mock role does not exist
        mock_role_get_by_name.return_value = None

        # Call function
        result = create_user("test_user", "password", "InvalidRole", "test@test.com")

        # Assertions
        self.assertIsNone(result)
        mock_role_get_by_name.assert_called_once_with("InvalidRole")
        mock_user_create.assert_not_called()

    @patch("main.auth.Role.get_by_name")
    @patch("main.auth.User.create")
    def test_create_user_duplicate_email(self, mock_user_create, mock_role_get_by_name):
        """
        Test creating a user with a duplicate email.
        """
        # Mock role existence
        mock_role_get_by_name.return_value = MagicMock()

        # Simulate IntegrityError for duplicate email
        mock_user_create.side_effect = sqlite3.IntegrityError("UNIQUE constraint failed: users.email")

        # Call function
        result = create_user("test_user", "password", "Management", "duplicate@test.com")

        # Assertions
        self.assertIsNone(result)
        mock_user_create.assert_called_once_with(
            username="test_user",
            password_hash=unittest.mock.ANY,
            role_id="Management",
            email="duplicate@test.com"
        )

    def test_hash_password(self):
        """
        Test password hashing.
        """
        password = "test_password"
        hashed_password = hash_password(password)

        # Assert the hash is not equal to the plain password
        self.assertNotEqual(password, hashed_password)


if __name__ == "__main__":
    unittest.main()
