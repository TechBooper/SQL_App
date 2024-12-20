import unittest
from unittest.mock import Mock, patch
from main.controllers import (
    has_permission,
    create_client,
    update_client,
    delete_client,
    create_contract,
    update_contract,
    delete_contract,
    create_event,
    update_event,
    delete_event,
    create_user,
    update_user,
    delete_user,
    get_all_clients,
    get_all_contracts,
    get_all_events,
    get_all_users,
    filter_contracts_by_status,
    filter_events_unassigned,
    filter_events_by_support_user,
    assign_support_to_event
)
from main.models import User, Client, Contract, Event, Role, Database


class TestControllers(unittest.TestCase):
    def setUp(self):
        # Mock user setup
        self.mock_user = Mock(username="test_user", role_id="Commercial", email="test@example.com")

        # Mock role setup
        self.mock_role = Mock(name="Commercial")

        # Mock permissions setup
        self.mock_permissions = [
            Mock(entity="client", action="create"),
            Mock(entity="client", action="update"),
            Mock(entity="client", action="delete"),
            Mock(entity="contract", action="create"),
            Mock(entity="contract", action="update"),
            Mock(entity="event", action="create"),
            Mock(entity="event", action="assign_support"),
            Mock(entity="user", action="create")
        ]

        # Mock client setup
        self.mock_client = Mock(
            email="client@example.com",
            first_name="John",
            last_name="Doe",
            sales_contact_id="test_user"
        )

        # Mock contract setup
        self.mock_contract = Mock(
            id=1,
            client_id="client@example.com",
            sales_contact_id="test_user",
            status="Signed"
        )

        # Mock event setup
        self.mock_event = Mock(
            id=1,
            contract_id=1,
            support_contact_id=None
        )

        # Helper method for creating database mocks
        def create_db_mock(return_value):
            mock_cursor = Mock()
            mock_cursor.fetchall.return_value = return_value
            mock_conn = Mock()
            mock_conn.cursor.return_value = mock_cursor
            mock_cm = Mock()
            mock_cm.__enter__ = Mock(return_value=mock_conn)
            mock_cm.__exit__ = Mock(return_value=None)
            return mock_cm

        self.create_db_mock = create_db_mock

    def test_has_permission_user_not_found(self):
        with patch('main.models.User.get_by_username', return_value=None):
            result = has_permission("nonexistent_user", "client", "create")
            self.assertFalse(result)

    def test_has_permission_role_not_found(self):
        with patch('main.models.User.get_by_username', return_value=self.mock_user):
            with patch('main.models.Role.get_by_name', return_value=None):
                result = has_permission("test_user", "client", "create")
                self.assertFalse(result)

    def test_has_permission_granted(self):
        with patch('main.models.User.get_by_username', return_value=self.mock_user):
            with patch('main.models.Role.get_by_name', return_value=self.mock_role):
                with patch('main.models.Permission.get_permissions_by_role', return_value=self.mock_permissions):
                    result = has_permission("test_user", "client", "create")
                    self.assertTrue(result)

    def test_has_permission_commercial_event_create(self):
        commercial_role = Mock(name="Commercial")
        commercial_user = Mock(username="sales", role_id="Commercial")
        with patch('main.models.User.get_by_username', return_value=commercial_user):
            with patch('main.models.Role.get_by_name', return_value=commercial_role):
                with patch('main.models.Permission.get_permissions_by_role', return_value=self.mock_permissions):
                    result = has_permission("sales", "event", "create", resource_owner_username="sales")
                    self.assertTrue(result)

    def test_update_event_not_found(self):
        with patch('main.models.Event.get_by_id', return_value=None):
            result = update_event("test_user", 999, notes="Updated notes")
            self.assertEqual(result, "Event not found.")

    def test_delete_event_success(self):
        with patch('main.models.Event.get_by_id', return_value=self.mock_event):
            with patch('main.models.Contract.get_by_id', return_value=self.mock_contract):
                with patch('main.models.Client.get_by_email', return_value=self.mock_client):
                    with patch('main.controllers.has_permission', return_value=True):
                        with patch.object(self.mock_event, 'delete', return_value=True):
                            result = delete_event("test_user", 1)
                            self.assertIn("deleted successfully", result)

    def test_delete_event_not_found(self):
        with patch('main.models.Event.get_by_id', return_value=None):
            result = delete_event("test_user", 999)
            self.assertEqual(result, "Event not found.")

    def test_get_all_events_success(self):
        mock_data = [{
            "id": 1,
            "contract_id": 1,
            "support_contact_id": "support_user",
            "client_first_name": "John",
            "client_last_name": "Doe"
        }]
        
        with patch('main.models.User.get_by_username', return_value=self.mock_user):
            with patch('main.models.Role.get_by_name', return_value=self.mock_role):
                with patch('main.models.Database.connect', return_value=self.create_db_mock(mock_data)):
                    results = get_all_events("test_user")
                    self.assertEqual(len(results), 1)
                    self.assertEqual(results[0]["client_name"], "John Doe")

    def test_get_all_events_user_not_found(self):
        with patch('main.models.User.get_by_username', return_value=None):
            results = get_all_events("nonexistent_user")
            self.assertEqual(results, [])

    def test_update_user_success(self):
        with patch('main.models.User.get_by_username', return_value=self.mock_user):
            with patch('main.controllers.has_permission', return_value=True):
                with patch.object(self.mock_user, 'update', return_value=True):
                    result = update_user(
                        "admin_user",
                        "test_user",
                        new_username="new_username",
                        email="new@example.com"
                    )
                    self.assertIn("updated successfully", result)

    def test_update_user_not_found(self):
        with patch('main.models.User.get_by_username', return_value=None):
            result = update_user("admin_user", "nonexistent_user")
            self.assertEqual(result, "User not found.")

    def test_delete_user_success(self):
        with patch('main.models.User.get_by_username', return_value=self.mock_user):
            with patch('main.controllers.has_permission', return_value=True):
                with patch.object(self.mock_user, 'delete', return_value=True):
                    result = delete_user("admin_user", "test_user")
                    self.assertIn("deleted successfully", result)

    def test_delete_user_not_found(self):
        with patch('main.models.User.get_by_username', return_value=None):
            result = delete_user("admin_user", "nonexistent_user")
            self.assertEqual(result, "User not found.")

    def test_create_client_success(self):
        with patch('main.models.User.get_by_username', return_value=self.mock_user):
            with patch('main.models.Role.get_by_name', return_value=self.mock_role):
                with patch('main.models.Permission.get_permissions_by_role', return_value=self.mock_permissions):
                    with patch('main.models.Client.create', return_value=True):
                        result = create_client(
                            "test_user",
                            "John",
                            "Doe",
                            "john@example.com",
                            "1234567890",
                            "Test Company"
                        )
                        self.assertIn("created successfully", result)

    def test_update_client_success(self):
        with patch('main.models.User.get_by_username', return_value=self.mock_user):
            with patch('main.models.Role.get_by_name', return_value=self.mock_role):
                with patch('main.models.Permission.get_permissions_by_role', return_value=self.mock_permissions):
                    with patch('main.models.Client.get_by_email', return_value=self.mock_client):
                        with patch.object(self.mock_client, 'update', return_value=True):
                            result = update_client(
                                "test_user",
                                "client@example.com",
                                first_name="Jane"
                            )
                            self.assertIn("updated successfully", result)

    def test_delete_client_success(self):
        with patch('main.models.User.get_by_username', return_value=self.mock_user):
            with patch('main.models.Role.get_by_name', return_value=self.mock_role):
                with patch('main.models.Permission.get_permissions_by_role', return_value=self.mock_permissions):
                    with patch('main.models.Client.get_by_email', return_value=self.mock_client):
                        with patch.object(self.mock_client, 'delete', return_value=True):
                            result = delete_client("test_user", "client@example.com")
                            self.assertIn("deleted successfully", result)

    def test_create_contract_success(self):
        with patch('main.models.User.get_by_username', return_value=self.mock_user):
            with patch('main.models.Role.get_by_name', return_value=self.mock_role):
                with patch('main.models.Permission.get_permissions_by_role', return_value=self.mock_permissions):
                    with patch('main.models.Client.get_by_email', return_value=self.mock_client):
                        with patch('main.models.Contract.create', return_value=True):
                            result = create_contract(
                                "test_user",
                                "client@example.com",
                                1000,
                                1000,
                                "Pending"
                            )
                            self.assertIn("created successfully", result)

    def test_update_contract_success(self):
        with patch('main.models.User.get_by_username', return_value=self.mock_user):
            with patch('main.models.Role.get_by_name', return_value=self.mock_role):
                with patch('main.models.Permission.get_permissions_by_role', return_value=self.mock_permissions):
                    with patch('main.models.Contract.get_by_id', return_value=self.mock_contract):
                        with patch.object(self.mock_contract, 'update', return_value=True):
                            result = update_contract(
                                "test_user",
                                1,
                                2000,
                                1500,
                                "Active"
                            )
                            self.assertIn("updated successfully", result)

    def test_create_event_success(self):
        with patch('main.models.User.get_by_username', return_value=self.mock_user):
            with patch('main.models.Role.get_by_name', return_value=self.mock_role):
                with patch('main.models.Permission.get_permissions_by_role', return_value=self.mock_permissions):
                    with patch('main.models.Contract.get_by_id', return_value=self.mock_contract):
                        with patch('main.models.Client.get_by_email', return_value=self.mock_client):
                            with patch('main.models.Event.create', return_value=True):
                                result = create_event(
                                    "test_user",
                                    1,
                                    "2024-01-01",
                                    "2024-01-02",
                                    "Test Location",
                                    100,
                                    "Test Notes"
                                )
                                self.assertIn("created successfully", result)

    def test_create_user_success(self):
        with patch('main.models.User.get_by_username', return_value=self.mock_user):
            with patch('main.models.Role.get_by_name', return_value=self.mock_role):
                with patch('main.models.Permission.get_permissions_by_role', return_value=self.mock_permissions):
                    with patch('main.models.User.create', return_value=True):
                        result = create_user(
                            "admin_user",
                            "new_user",
                            "password123",
                            "Commercial",
                            "new@example.com"
                        )
                        self.assertIn("created successfully", result)

    def test_get_all_clients_success(self):
        mock_data = [
            {"email": "client1@example.com", "first_name": "John", "last_name": "Doe"},
            {"email": "client2@example.com", "first_name": "Jane", "last_name": "Smith"}
        ]

        with patch('main.models.Database.connect', return_value=self.create_db_mock(mock_data)):
            results = get_all_clients()
            self.assertEqual(len(results), 2)
            self.assertEqual(results[0]["email"], "client1@example.com")

    def test_get_all_contracts_success(self):
        mock_data = [{
            "id": 1,
            "client_id": "client@example.com",
            "client_first_name": "John",
            "client_last_name": "Doe"
        }]

        with patch('main.models.Database.connect', return_value=self.create_db_mock(mock_data)):
            results = get_all_contracts()
            self.assertEqual(len(results), 1)
            self.assertIn("client_name", results[0])

    def test_filter_contracts_by_status_success(self):
        mock_data = [{
            "id": 1,
            "status": "Active",
            "client_first_name": "John",
            "client_last_name": "Doe"
        }]

        with patch('main.models.Database.connect', return_value=self.create_db_mock(mock_data)):
            results = filter_contracts_by_status("Active")
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0]["status"], "Active")

    def test_filter_unassigned_events(self):
        mock_data = [{
            "id": 1,
            "contract_id": 1,
            "support_contact_id": None,
            "event_date_start": "2024-01-01",
            "event_date_end": "2024-01-02",
            "client_first_name": "John",
            "client_last_name": "Doe"
        }]

        with patch('main.models.Database.connect', return_value=self.create_db_mock(mock_data)):
            results = filter_events_unassigned()
            self.assertEqual(len(results), 1)
            self.assertIsNone(results[0]["support_contact_id"])
            self.assertEqual(results[0]["client_name"], "John Doe")

    def test_filter_events_by_support_user(self):
        mock_data = [{
            "id": 1,
            "contract_id": 1,
            "support_contact_id": "support_user",
            "event_date_start": "2024-01-01",
            "event_date_end": "2024-01-02",
            "client_first_name": "John",
            "client_last_name": "Doe"
        }]

        with patch('main.models.Database.connect', return_value=self.create_db_mock(mock_data)):
            results = filter_events_by_support_user("support_user")
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0]["support_contact_id"], "support_user")
            self.assertEqual(results[0]["client_name"], "John Doe")

    def test_assign_support_to_event_success(self):
        with patch('main.models.User.get_by_username', return_value=self.mock_user):
            with patch('main.models.Role.get_by_name', return_value=self.mock_role):
                with patch('main.models.Permission.get_permissions_by_role', return_value=self.mock_permissions):
                    with patch('main.models.Event.get_by_id', return_value=self.mock_event):
                        with patch('main.controllers.has_permission', return_value=True):
                            with patch.object(self.mock_event, 'update', return_value=True):
                                result = assign_support_to_event(
                                    "admin_user",
                                    1,
                                    "support_user"
                                )
                                self.assertIn("Support contact assigned", result)

    def test_permission_denied_for_create_client(self):
        with patch('main.models.User.get_by_username', return_value=self.mock_user):
            with patch('main.models.Role.get_by_name', return_value=self.mock_role):
                with patch('main.models.Permission.get_permissions_by_role', return_value=[]):  # No permissions granted
                    result = create_client(
                        "test_user",
                        "John",
                        "Doe",
                        "john@example.com",
                        "1234567890",
                        "Test Company"
                    )
                    self.assertIn("Permission denied", result)

    def test_create_client_with_missing_fields(self):
        with patch('main.models.User.get_by_username', return_value=self.mock_user):
            with patch('main.models.Role.get_by_name', return_value=self.mock_role):
                with patch('main.models.Permission.get_permissions_by_role', return_value=self.mock_permissions):
                    result = create_client(
                        "test_user",
                        None,  # Missing first name
                        "Doe",
                        "john@example.com",
                        "1234567890",
                        "Test Company"
                    )
                    self.assertIn("All client fields are required", result)

    def test_create_contract_with_invalid_status(self):
        with patch('main.models.User.get_by_username', return_value=self.mock_user):
            with patch('main.models.Role.get_by_name', return_value=self.mock_role):
                with patch('main.models.Permission.get_permissions_by_role', return_value=self.mock_permissions):
                    with patch('main.models.Client.get_by_email', return_value=self.mock_client):
                        result = create_contract(
                            "test_user",
                            "client@example.com",
                            1000,
                            1000,
                            "InvalidStatus"
                        )
                        self.assertIn("CHECK constraint failed: status IN ('Signed', 'Not Signed')", result)

    def test_filter_contracts_invalid_status(self):
        mock_data = []  # No contracts found for invalid status
        with patch('main.models.Database.connect', return_value=self.create_db_mock(mock_data)):
            result = filter_contracts_by_status("NonexistentStatus")
            self.assertEqual(result, [])

    def test_delete_client_permission_denied(self):
        with patch('main.models.User.get_by_username', return_value=self.mock_user):
            with patch('main.models.Role.get_by_name', return_value=self.mock_role):
                with patch('main.models.Permission.get_permissions_by_role', return_value=[]):  # No permissions
                    with patch('main.models.Client.get_by_email', return_value=self.mock_client):  # Mock client exists
                        result = delete_client("test_user", "client@example.com")
                        self.assertIn("Permission denied", result)

    def test_delete_contract_not_found(self):
        with patch('main.models.User.get_by_username', return_value=self.mock_user):
            with patch('main.models.Role.get_by_name', return_value=self.mock_role):
                with patch('main.models.Permission.get_permissions_by_role', return_value=self.mock_permissions):
                    with patch('main.models.Contract.get_by_id', return_value=None):  # Contract not found
                        result = delete_contract("test_user", 999)  # Invalid contract ID
                        self.assertIn("Contract not found", result)

    def test_missing_permission_for_client_creation(self):
        with patch('main.models.User.get_by_username', return_value=self.mock_user):
            with patch('main.models.Role.get_by_name', return_value=self.mock_role):
                with patch('main.models.Permission.get_permissions_by_role', return_value=[]):
                    result = create_client(
                        "test_user",
                        "John",
                        "Doe",
                        "john@example.com",
                        "1234567890",
                        "Test Company"
                    )
                    self.assertEqual(result, "Permission denied.")

    def test_missing_fields_for_client_creation(self):
        with patch('main.models.User.get_by_username', return_value=self.mock_user):
            with patch('main.models.Role.get_by_name', return_value=self.mock_role):
                with patch('main.models.Permission.get_permissions_by_role', return_value=self.mock_permissions):
                    result = create_client(
                        "test_user",
                        "",
                        "Doe",
                        "john@example.com",
                        "1234567890",
                        "Test Company"
                    )
                    self.assertEqual(result, "All client fields are required.")

    def test_permission_denied_for_deleting_client(self):
        with patch('main.models.User.get_by_username', return_value=self.mock_user):
            with patch('main.models.Role.get_by_name', return_value=self.mock_role):
                with patch('main.models.Permission.get_permissions_by_role', return_value=[]):
                    with patch('main.models.Client.get_by_email', return_value=self.mock_client):
                        result = delete_client("test_user", "client@example.com")
                        self.assertEqual(result, "Permission denied.")

    def test_client_not_found_for_update(self):
        with patch('main.models.Client.get_by_email', return_value=None):
            result = update_client("test_user", "nonexistent@example.com", first_name="NewName")
            self.assertEqual(result, "Client not found.")

    def test_contract_not_found_for_update(self):
        with patch('main.models.Contract.get_by_id', return_value=None):
            result = update_contract("test_user", 999, 2000, 1500, "Signed")
            self.assertEqual(result, "Contract not found.")

    def test_event_not_found_for_update(self):
        with patch('main.models.Event.get_by_id', return_value=None):
            result = update_event("test_user", 999, notes="Updated notes")
            self.assertEqual(result, "Event not found.")

    def test_create_event_without_permission(self):
        with patch('main.models.User.get_by_username', return_value=self.mock_user):
            with patch('main.models.Role.get_by_name', return_value=self.mock_role):
                with patch('main.models.Permission.get_permissions_by_role', return_value=[]):
                    result = create_event(
                        "test_user",
                        1,
                        "2024-01-01",
                        "2024-01-02",
                        "Test Location",
                        100,
                        "Test Notes"
                    )
                    self.assertEqual(result, "Contract not valid or not signed.")

    def test_get_all_events_user_not_found(self):
        with patch('main.models.User.get_by_username', return_value=None):
            result = get_all_events("nonexistent_user")
            self.assertEqual(result, [])

    def test_get_all_events_role_not_found(self):
        with patch('main.models.User.get_by_username', return_value=self.mock_user):
            with patch('main.models.Role.get_by_name', return_value=None):
                result = get_all_events("test_user")
                self.assertEqual(result, [])

    def test_get_all_events_support_role(self):
        support_role = Mock(name="Support")
        support_user = Mock(username="support", role_id="Support")
        mock_data = [{
            "id": 1,
            "contract_id": 1,
            "client_first_name": "John",
            "client_last_name": "Doe"
        }]
        with patch('main.models.User.get_by_username', return_value=support_user):
            with patch('main.models.Role.get_by_name', return_value=support_role):
                with patch('main.models.Database.connect', return_value=self.create_db_mock(mock_data)):
                    result = get_all_events("support")
                    self.assertEqual(len(result), 1)

    def test_update_user_success(self):
        mock_user = Mock(username="test_user")
        with patch('main.models.User.get_by_username', return_value=mock_user):
            with patch('main.controllers.has_permission', return_value=True):
                with patch.object(mock_user, 'update', return_value=True):
                    result = update_user(
                        "admin",
                        "test_user",
                        new_username="new_username",
                        password="new_password",
                        role_name="new_role",
                        email="new@example.com"
                    )
                    self.assertIn("updated successfully", result)

    def test_update_user_not_found(self):
        with patch('main.models.User.get_by_username', return_value=None):
            result = update_user("admin", "nonexistent_user")
            self.assertEqual(result, "User not found.")

    def test_delete_user_success(self):
        mock_user = Mock(username="test_user")
        with patch('main.models.User.get_by_username', return_value=mock_user):
            with patch('main.controllers.has_permission', return_value=True):
                with patch.object(mock_user, 'delete', return_value=True):
                    result = delete_user("admin", "test_user")
                    self.assertIn("deleted successfully", result)

    def test_delete_user_not_found(self):
        with patch('main.models.User.get_by_username', return_value=None):
            result = delete_user("admin", "nonexistent_user")
            self.assertEqual(result, "User not found.")

    def test_delete_user_permission_denied(self):
        mock_user = Mock(username="test_user")
        with patch('main.models.User.get_by_username', return_value=mock_user):
            with patch('main.controllers.has_permission', return_value=False):
                result = delete_user("non_admin", "test_user")
                self.assertEqual(result, "Permission denied.")

    def test_database_error_handling(self):
        import sqlite3
        with patch('main.models.Database.connect', side_effect=sqlite3.Error("Database error")):
            result = get_all_clients()
            self.assertEqual(result, [])
            
            result = get_all_contracts()
            self.assertEqual(result, [])
            
            result = filter_contracts_by_status("Active")
            self.assertEqual(result, [])
            
            result = filter_events_unassigned()
            self.assertEqual(result, [])
            
            result = filter_events_by_support_user("support")
            self.assertEqual(result, [])

    def test_update_user_permission_denied(self):
        with patch('main.models.User.get_by_username', return_value=self.mock_user):
            with patch('main.models.Role.get_by_name', return_value=self.mock_role):
                with patch('main.models.Permission.get_permissions_by_role', return_value=[]):
                    result = update_user(
                        "test_user",
                        "existing_user",
                        email="updated_email@example.com"
                    )
                    self.assertEqual(result, "Permission denied.")


if __name__ == '__main__':
    unittest.main()
