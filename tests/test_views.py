import unittest
from unittest.mock import patch, MagicMock
from io import StringIO
import sys

from getpass import getpass
from tabulate import tabulate
from main.views import (
    display_welcome_message,
    display_login_prompt,
    display_main_menu,
    prompt_choice,
    display_profile,
    prompt_input,
    confirm_action,
    display_sub_menu,
    display_users,
    display_clients,
    display_contracts,
    display_events,
)


class TestDisplayFunctions(unittest.TestCase):

    def setUp(self):
        self.original_stdout = sys.stdout
        self.mock_stdout = StringIO()
        sys.stdout = self.mock_stdout

    def tearDown(self):
        sys.stdout = self.original_stdout

    def test_display_welcome_message(self):
        display_welcome_message()
        output = self.mock_stdout.getvalue()
        self.assertIn("Welcome to Epic Events CRM", output)
        self.assertIn("--------------------------", output)

    @patch("builtins.input", return_value="test_user")
    @patch("getpass.getpass", return_value="test_password")
    def test_display_login_prompt(self, mock_getpass, mock_input):
        username, password = display_login_prompt()
        self.assertEqual(username, "test_user")
        self.assertEqual(password, "test_password")

    def test_display_main_menu(self):
        options = {"1": "Option One", "2": "Option Two"}
        display_main_menu(options)
        output = self.mock_stdout.getvalue()
        self.assertIn("Main Menu:", output)
        self.assertIn("1. Option One", output)
        self.assertIn("2. Option Two", output)

    @patch("builtins.input", return_value="1")
    def test_prompt_choice(self, mock_input):
        choice = prompt_choice()
        self.assertEqual(choice, "1")

    def test_display_profile(self):
        mock_user = MagicMock(
            username="jdoe", email="jdoe@example.com", role_id="Commercial"
        )
        display_profile(mock_user)
        output = self.mock_stdout.getvalue()
        self.assertIn("User Profile:", output)
        self.assertIn("Username: jdoe", output)
        self.assertIn("Email: jdoe@example.com", output)
        self.assertIn("Role: Commercial", output)

    @patch("builtins.input", return_value="test input")
    def test_prompt_input(self, mock_input):
        result = prompt_input("Enter something: ")
        self.assertEqual(result, "test input")

    @patch("builtins.input", return_value="yes")
    def test_confirm_action_yes(self, mock_input):
        result = confirm_action("delete this item")
        self.assertTrue(result)

    @patch("builtins.input", return_value="no")
    def test_confirm_action_no(self, mock_input):
        result = confirm_action("delete this item")
        self.assertFalse(result)

    def test_display_sub_menu(self):
        options = {"1": "Sub Option One", "2": "Sub Option Two"}
        display_sub_menu("Test Sub Menu", options)
        output = self.mock_stdout.getvalue()
        self.assertIn("Test Sub Menu:", output)
        self.assertIn("1. Sub Option One", output)
        self.assertIn("2. Sub Option Two", output)

    def test_display_users_no_users(self):
        display_users([])
        output = self.mock_stdout.getvalue()
        self.assertIn("Users List:", output)
        self.assertIn("No users found.", output)

    def test_display_users(self):
        class MockUser:
            def __init__(self, username, email, role_id):
                self.username = username
                self.email = email
                self.role_id = role_id

        users = [
            MockUser("user1", "user1@example.com", "Commercial"),
            MockUser("user2", "user2@example.com", "Management"),
        ]
        display_users(users)
        output = self.mock_stdout.getvalue()
        self.assertIn("Users List:", output)
        self.assertIn("user1", output)
        self.assertIn("user2", output)
        self.assertIn("Commercial", output)
        self.assertIn("Management", output)

    def test_display_clients_no_clients(self):
        display_clients([])
        output = self.mock_stdout.getvalue()
        self.assertIn("No clients found.", output)

    def test_display_clients(self):
        clients = [
            {
                "email": "client1@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "phone": "1234567890",
                "company_name": "TestCorp",
                "last_contact": "2024-01-01",
                "sales_contact_id": "sales_user",
                "created_at": "2024-01-01",
                "updated_at": "2024-01-02",
            }
        ]
        display_clients(clients)
        output = self.mock_stdout.getvalue()
        self.assertIn("Clients List:", output)
        self.assertIn("client1@example.com", output)
        self.assertIn("John", output)
        self.assertIn("Doe", output)
        self.assertIn("TestCorp", output)
        self.assertIn("sales_user", output)

    def test_display_contracts_no_contracts(self):
        display_contracts([])
        output = self.mock_stdout.getvalue()
        self.assertIn("No contracts found.", output)

    def test_display_contracts(self):
        contracts = [
            {
                "id": 1,
                "client_id": "client@example.com",
                "sales_contact_id": "sales_user",
                "total_amount": 1000,
                "amount_remaining": 500,
                "status": "Signed",
                "created_at": "2024-01-01",
                "updated_at": "2024-01-02",
            }
        ]
        display_contracts(contracts, title="Test Contracts")
        output = self.mock_stdout.getvalue()
        self.assertIn("Test Contracts:", output)
        self.assertIn("client@example.com", output)
        self.assertIn("Signed", output)

    def test_display_events_no_events(self):
        display_events([])
        output = self.mock_stdout.getvalue()
        self.assertIn("No events found.", output)

    def test_display_events(self):
        events = [
            {
                "id": 1,
                "contract_id": 101,
                "support_contact_id": "support_user",
                "event_date_start": "2024-01-01 10:00",
                "event_date_end": "2024-01-01 12:00",
                "location": "Test Location",
                "attendees": 50,
                "notes": "Test Event",
                "created_at": "2024-01-01",
                "updated_at": "2024-01-02",
            }
        ]
        display_events(events, title="Test Events")
        output = self.mock_stdout.getvalue()
        self.assertIn("Test Events:", output)
        self.assertIn("support_user", output)
        self.assertIn("Test Location", output)
        self.assertIn("Test Event", output)


if __name__ == "__main__":
    unittest.main()
