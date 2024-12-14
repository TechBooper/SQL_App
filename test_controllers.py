import unittest
from unittest.mock import Mock, patch, call
import bcrypt
from models import User, Client, Contract, Event, Permission, Role, Database
from controllers import (
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

class TestControllers(unittest.TestCase):
    def setUp(self):
        # Mock user setup
        self.mock_user = Mock()
        self.mock_user.username = "test_user"
        self.mock_user.role_id = "Commercial"
        self.mock_user.email = "test@example.com"

        # Mock role setup with expanded permissions
        self.mock_role = Mock()
        self.mock_role.name = "Commercial"

        # Mock permissions setup with all necessary permissions
        self.mock_permissions = [
            Mock(entity="client", action="create"),
            Mock(entity="client", action="update"),
            Mock(entity="client", action="delete"),
            Mock(entity="contract", action="create"),
            Mock(entity="contract", action="update"),
            Mock(entity="event", action="create"),
            Mock(entity="user", action="create"),
            Mock(entity="event", action="assign_support")
        ]

        # Mock client setup
        self.mock_client = Mock()
        self.mock_client.email = "client@example.com"
        self.mock_client.first_name = "John"
        self.mock_client.last_name = "Doe"
        self.mock_client.sales_contact_id = "test_user"

        # Mock contract setup
        self.mock_contract = Mock()
        self.mock_contract.id = 1
        self.mock_contract.client_id = "client@example.com"
        self.mock_contract.sales_contact_id = "test_user"
        self.mock_contract.status = "Signed"

        # Mock event setup
        self.mock_event = Mock()
        self.mock_event.id = 1
        self.mock_event.contract_id = 1
        self.mock_event.support_contact_id = None

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
        with patch('models.User.get_by_username', return_value=None):
            result = has_permission("nonexistent_user", "client", "create")
            self.assertFalse(result)

    def test_has_permission_role_not_found(self):
        with patch('models.User.get_by_username', return_value=self.mock_user):
            with patch('models.Role.get_by_name', return_value=None):
                result = has_permission("test_user", "client", "create")
                self.assertFalse(result)

    def test_has_permission_granted(self):
        with patch('models.User.get_by_username', return_value=self.mock_user):
            with patch('models.Role.get_by_name', return_value=self.mock_role):
                with patch('models.Permission.get_permissions_by_role', return_value=self.mock_permissions):
                    result = has_permission("test_user", "client", "create")
                    self.assertTrue(result)

    def test_create_client_success(self):
        with patch('models.User.get_by_username', return_value=self.mock_user):
            with patch('models.Role.get_by_name', return_value=self.mock_role):
                with patch('models.Permission.get_permissions_by_role', return_value=self.mock_permissions):
                    with patch('models.Client.create', return_value=True):
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
        with patch('models.User.get_by_username', return_value=self.mock_user):
            with patch('models.Role.get_by_name', return_value=self.mock_role):
                with patch('models.Permission.get_permissions_by_role', return_value=self.mock_permissions):
                    with patch('models.Client.get_by_email', return_value=self.mock_client):
                        with patch.object(self.mock_client, 'update', return_value=True):
                            result = update_client(
                                "test_user",
                                "client@example.com",
                                first_name="Jane"
                            )
                            self.assertIn("updated successfully", result)

    def test_delete_client_success(self):
        with patch('models.User.get_by_username', return_value=self.mock_user):
            with patch('models.Role.get_by_name', return_value=self.mock_role):
                with patch('models.Permission.get_permissions_by_role', return_value=self.mock_permissions):
                    with patch('models.Client.get_by_email', return_value=self.mock_client):
                        with patch.object(self.mock_client, 'delete', return_value=True):
                            result = delete_client("test_user", "client@example.com")
                            self.assertIn("deleted successfully", result)

    def test_create_contract_success(self):
        with patch('models.User.get_by_username', return_value=self.mock_user):
            with patch('models.Role.get_by_name', return_value=self.mock_role):
                with patch('models.Permission.get_permissions_by_role', return_value=self.mock_permissions):
                    with patch('models.Client.get_by_email', return_value=self.mock_client):
                        with patch('models.Contract.create', return_value=True):
                            result = create_contract(
                                "test_user",
                                "client@example.com",
                                1000,
                                1000,
                                "Pending"
                            )
                            self.assertIn("created successfully", result)

    def test_update_contract_success(self):
        with patch('models.User.get_by_username', return_value=self.mock_user):
            with patch('models.Role.get_by_name', return_value=self.mock_role):
                with patch('models.Permission.get_permissions_by_role', return_value=self.mock_permissions):
                    with patch('models.Contract.get_by_id', return_value=self.mock_contract):
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
        with patch('models.User.get_by_username', return_value=self.mock_user):
            with patch('models.Role.get_by_name', return_value=self.mock_role):
                with patch('models.Permission.get_permissions_by_role', return_value=self.mock_permissions):
                    with patch('models.Contract.get_by_id', return_value=self.mock_contract):
                        with patch('models.Client.get_by_email', return_value=self.mock_client):
                            with patch('models.Event.create', return_value=True):
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
        with patch('models.User.get_by_username', return_value=self.mock_user):
            with patch('models.Role.get_by_name', return_value=self.mock_role):
                with patch('models.Permission.get_permissions_by_role', return_value=self.mock_permissions):
                    with patch('models.User.create', return_value=True):
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
        
        with patch('models.Database.connect', return_value=self.create_db_mock(mock_data)):
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
        
        with patch('models.Database.connect', return_value=self.create_db_mock(mock_data)):
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
        
        with patch('models.Database.connect', return_value=self.create_db_mock(mock_data)):
            results = filter_contracts_by_status("Active")
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0]["status"], "Active")

    def test_assign_support_to_event_success(self):
        with patch('models.User.get_by_username', return_value=self.mock_user):
            with patch('models.Role.get_by_name', return_value=self.mock_role):
                with patch('models.Permission.get_permissions_by_role', return_value=self.mock_permissions):
                    with patch('models.Event.get_by_id', return_value=self.mock_event):
                        with patch.object(self.mock_event, 'update', return_value=True):
                            result = assign_support_to_event(
                                "admin_user",
                                1,
                                "support_user"
                            )
                            self.assertIn("Support contact assigned", result)

if __name__ == '__main__':
    unittest.main()