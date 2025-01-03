import unittest
from unittest.mock import patch, MagicMock
from main.database import create_connection
from cli import (
    authenticate,
    User, 
    interactive_session, 
    handle_view_profile,
    handle_update_client, 
    handle_update_email,
    manage_users,
    manage_clients,
    handle_view_clients,
    handle_create_contract,
    handle_assign_support,
    handle_filter_events_unassigned,
    handle_delete_client,
    handle_create_user,
    handle_update_user,
    handle_delete_user,
    handle_view_users,
    manage_contracts,
    handle_view_contracts,
    handle_update_contract,
    handle_delete_contract,
    handle_filter_contracts,
    handle_create_event,
    handle_update_event,
    handle_delete_event,
    manage_events,
    handle_filter_events_assigned_to_me
)
import bcrypt



class TestCLI(unittest.TestCase):
    def setUp(self):
        # Create a mock database connection
        self.db_patcher = patch('main.database.create_connection')
        self.mock_db = self.db_patcher.start()
        
        # Configure the mock to return a MagicMock connection object
        self.mock_conn = MagicMock()
        self.mock_db.return_value = self.mock_conn
        
        # Create a mock cursor
        self.mock_cursor = MagicMock()
        self.mock_conn.cursor.return_value = self.mock_cursor

        # Set up common test data
        self.test_session = {
            'username': 'test_user',
            'role': 'Management'
        }

    def tearDown(self):
        self.db_patcher.stop()

    def test_menu_navigation_view_profile(self):
        mock_user = MagicMock(spec=User)
        mock_user.username = 'test_user'
        mock_user.email = 'test@example.com'
        mock_user.role_id = 'Management'
        mock_user.created_at = '2024-01-01 00:00:00'
        mock_user.updated_at = '2024-01-01 00:00:00'

        with patch('cli.User.get_by_username', return_value=mock_user), \
             patch('builtins.print') as mock_print:
            
            handle_view_profile(self.test_session)
            
            # Verify that the profile display function was called with correct data
            mock_print.assert_called()
            # Verify User.get_by_username was called with correct username
            User.get_by_username.assert_called_once_with('test_user')

    def test_update_email(self):
        mock_user = MagicMock(spec=User)
        mock_user.username = 'test_user'
        mock_user.email = 'old@example.com'
        mock_user.update.return_value = True

        # Mock the input function to return a new email
        new_email = 'new@example.com'
        with patch('cli.User.get_by_username', return_value=mock_user), \
             patch('cli.prompt_input', return_value=new_email), \
             patch('builtins.print') as mock_print:
            
            handle_update_email(self.test_session)
            
            # Verify that the email was updated
            self.assertEqual(mock_user.email, new_email)
            mock_user.update.assert_called_once()
            # Verify success message was printed
            mock_print.assert_called_with('Email updated successfully.\n')

    def test_update_email_invalid_format(self):
        mock_user = MagicMock(spec=User)
        mock_user.username = 'test_user'
        mock_user.email = 'old@example.com'

        # Mock the input function to return an invalid email first, then a valid one
        invalid_email = 'invalid_email'
        valid_email = 'new@example.com'
        with patch('cli.User.get_by_username', return_value=mock_user), \
             patch('cli.prompt_input', side_effect=[invalid_email, valid_email]), \
             patch('builtins.print') as mock_print:
            
            handle_update_email(self.test_session)
            
            # Verify that the invalid email format message was printed
            mock_print.assert_any_call('Invalid email format. Please enter a valid email (e.g., user@example.com).')

    def test_update_email_user_not_found(self):
        # Mock User.get_by_username to return None (user not found)
        with patch('cli.User.get_by_username', return_value=None), \
             patch('cli.prompt_input', return_value='new@example.com'), \
             patch('builtins.print') as mock_print:
            
            handle_update_email(self.test_session)
            
            # Verify that the user not found message was printed
            mock_print.assert_called_with('User not found.\n')

    def test_update_email_update_failed(self):
        mock_user = MagicMock(spec=User)
        mock_user.username = 'test_user'
        mock_user.email = 'old@example.com'
        mock_user.update.return_value = False

        with patch('cli.User.get_by_username', return_value=mock_user), \
             patch('cli.prompt_input', return_value='new@example.com'), \
             patch('builtins.print') as mock_print:
            
            handle_update_email(self.test_session)
            
            # Verify that the update failed message was printed
            mock_print.assert_called_with('Failed to update email.\n')
    
    def test_manage_users_permission_denied(self):
        # Test accessing manage_users without proper permissions
        test_session = {
            'username': 'test_user',
            'role': 'Support'  # Support role typically doesn't have user management permissions
        }
        
        with patch('cli.has_permission', return_value=False), \
            patch('cli.has_any_user_management_permission', return_value=False), \
            patch('builtins.print') as mock_print:
            
            manage_users(test_session)
            
            # Verify permission denied message was printed
            mock_print.assert_called_with('Permission denied.\n')

    def test_manage_clients_view_clients(self):
        test_session = {
            'username': 'test_user',
            'role': 'Management'
        }
        
        mock_clients = [
            {'email': 'client1@test.com', 'first_name': 'John', 'last_name': 'Doe'},
            {'email': 'client2@test.com', 'first_name': 'Jane', 'last_name': 'Smith'}
        ]
        
        with patch('cli.has_permission', return_value=True), \
            patch('cli.get_all_clients', return_value=mock_clients), \
            patch('cli.display_clients') as mock_display:
            
            handle_view_clients(test_session)
            
            # Verify that get_all_clients was called and results were displayed
            mock_display.assert_called_once_with(mock_clients)

    def test_manage_contracts_create_contract_success(self):
        test_session = {
            'username': 'test_user',
            'role': 'Commercial'
        }
        
        # Mock input values
        mock_inputs = [
            'client@test.com',  # client_email
            '10000',            # total_amount
            '5000',             # amount_remaining
            '1'                 # status choice (1 for Signed)
        ]
        
        with patch('cli.prompt_input', side_effect=mock_inputs), \
            patch('cli.create_contract', return_value='Contract created successfully') as mock_create, \
            patch('builtins.print') as mock_print:
            
            handle_create_contract(test_session)
            
            # Adjusted user_id to username per previous changes
            mock_create.assert_called_once_with(
                username='test_user',
                client_id='client@test.com',
                total_amount=10000.0,
                amount_remaining=5000.0,
                status='Signed'
            )
            
            # Verify success message was printed
            mock_print.assert_called_with('Contract created successfully\n')

    def test_manage_events_assign_support_success(self):
        test_session = {
            'username': 'test_user',
            'role': 'Management'
        }
        
        # Mock input values
        mock_inputs = [
            '1',                    # event_id
            'support_user'          # support_user_username
        ]
        
        with patch('cli.prompt_input', side_effect=mock_inputs), \
            patch('cli.assign_support_to_event', return_value='Support user assigned successfully') as mock_assign, \
            patch('builtins.print') as mock_print:
            
            handle_assign_support(test_session)
            
            # Adjusted user_id to username per previous changes
            mock_assign.assert_called_once_with(
                username='test_user',
                event_id=1,
                support_user_id='support_user'
            )
            
            # Verify success message was printed
            mock_print.assert_called_with('Support user assigned successfully\n')

    def test_manage_events_filter_unassigned(self):
        test_session = {
            'username': 'test_user',
            'role': 'Management'
        }
        
        mock_events = [
            {'id': 1, 'location': 'Paris', 'support_user_id': None},
            {'id': 2, 'location': 'London', 'support_user_id': None}
        ]
        
        with patch('cli.filter_events_unassigned', return_value=mock_events), \
            patch('cli.display_events') as mock_display:
            
            handle_filter_events_unassigned(test_session)
            
            # Verify that unassigned events were displayed correctly
            mock_display.assert_called_once_with(mock_events, title='Unassigned Events')

    def test_menu_navigation_invalid_choice(self):
        test_session = {
            'username': 'test_user',
            'role': 'Management'
        }
        
        # Mock menu options that would be returned by build_main_menu_options
        mock_options = {
            "1": "View Profile",
            "2": "Update Email",
            "3": "Manage Users",
            "4": "Manage Clients",
            "5": "Manage Contracts",
            "6": "Manage Events",
            "7": "Logout"
        }
        
        # Mock responses: first an invalid choice, then select Logout
        mock_responses = ['999', '7']
        
        with patch('cli.build_main_menu_options', return_value=mock_options), \
             patch('cli.display_main_menu') as mock_display_menu, \
             patch('cli.prompt_choice', side_effect=mock_responses), \
             patch('cli.has_permission', return_value=True), \
             patch('cli.has_any_user_management_permission', return_value=True), \
             patch('builtins.print') as mock_print:
            
            interactive_session(test_session)
            
            # Verify the menu was displayed
            mock_display_menu.assert_called_with(mock_options)
            
            # Verify invalid selection message was printed
            mock_print.assert_any_call('Invalid selection. Please try again.\n')
            
            # Verify logout message was printed
            mock_print.assert_any_call('Logging out...')

    def test_handle_delete_client_cancelled(self):
        test_session = {
            'username': 'test_user',
            'role': 'Management'
        }
        
        with patch('cli.prompt_input', return_value='client@test.com'), \
            patch('cli.confirm_action', return_value=False), \
            patch('builtins.print') as mock_print:
            
            handle_delete_client(test_session)
            
            # Verify cancellation message was printed
            mock_print.assert_called_with('Deletion cancelled.\n')


    # ---------------------------------------------------------
    # ADDITIONAL TESTS TO IMPROVE COVERAGE START BELOW THIS LINE
    # ---------------------------------------------------------

    def test_create_user_password_mismatch(self):
        # Management role can create a user
        # Test that password mismatch is handled correctly
        with patch('cli.has_permission', return_value=True), \
             patch('cli.prompt_input', side_effect=["new_user", "new@example.com", "Management"]), \
             patch('cli.getpass.getpass', side_effect=["password1", "password2"]), \
             patch('builtins.print') as mock_print:
            handle_create_user(self.test_session)
            mock_print.assert_called_with('Passwords do not match.\n')

    def test_update_user_not_found(self):
        # Attempting to update a user that doesn't exist
        with patch('cli.has_permission', return_value=True), \
             patch('cli.prompt_input', side_effect=["old_user", "new_user", "new@example.com", "Management"]), \
             patch('cli.getpass.getpass', side_effect=["", ""]), \
             patch('cli.update_user', return_value='User not found'), \
             patch('builtins.print') as mock_print:
            handle_update_user(self.test_session)
            mock_print.assert_called_with('User not found\n')

    def test_delete_user_confirm_no(self):
        # Delete user cancelled
        with patch('cli.has_permission', return_value=True), \
             patch('cli.prompt_input', return_value="some_user"), \
             patch('cli.confirm_action', return_value=False), \
             patch('builtins.print') as mock_print:
            handle_delete_user(self.test_session)
            mock_print.assert_called_with('Deletion cancelled.\n')

    def test_view_users_none_found(self):
        # If no users returned
        with patch('cli.has_permission', return_value=True), \
             patch('cli.get_all_users', return_value=[]), \
             patch('cli.display_users') as mock_display:
            handle_view_users(self.test_session)
            mock_display.assert_called_once_with([])

    def test_manage_clients_no_permissions(self):
        # Attempt to manage clients without proper permissions
        test_session_no_perm = {
            'username': 'test_user',
            'role': 'UnknownRole'
        }
        with patch('cli.has_permission', return_value=False), \
             patch('builtins.print') as mock_print:
            manage_clients(test_session_no_perm)
            mock_print.assert_called_with('Permission denied.\n')

    def test_view_clients_no_data(self):
        # No clients found
        with patch('cli.has_permission', return_value=True), \
             patch('cli.get_all_clients', return_value=[]), \
             patch('cli.display_clients') as mock_display:
            handle_view_clients(self.test_session)
            mock_display.assert_called_once_with([])

    def test_update_client_no_such_client(self):
        # Client not found scenario
        with patch('cli.has_permission', return_value=True), \
             patch('cli.prompt_input', side_effect=["notfound@example.com", "John", "Doe", "new@example.com", "1234567890", "NewCo"]), \
             patch('cli.update_client', return_value='Client not found'), \
             patch('builtins.print') as mock_print:
            handle_update_client(self.test_session)
            mock_print.assert_called_with('Client not found\n')

    def test_delete_client_not_found(self):
        # Deletion of non-existent client
        with patch('cli.has_permission', return_value=True), \
             patch('cli.prompt_input', return_value="notfound@example.com"), \
             patch('cli.confirm_action', return_value=True), \
             patch('cli.delete_client', return_value='Client not found'), \
             patch('builtins.print') as mock_print:
            handle_delete_client(self.test_session)
            mock_print.assert_called_with('Client not found\n')

    def test_view_contracts_no_permissions(self):
        # No permission to read contracts
        test_session_no_perm = {
            'username': 'no_perm_user',
            'role': 'UnknownRole'
        }
        with patch('cli.has_permission', return_value=False), \
             patch('builtins.print') as mock_print:
            manage_contracts(test_session_no_perm)
            mock_print.assert_called_with('Permission denied.\n')

    def test_view_contracts_empty(self):
        # No contracts found
        with patch('cli.has_permission', return_value=True), \
             patch('cli.get_all_contracts', return_value=[]), \
             patch('cli.display_contracts') as mock_display:
            handle_view_contracts(self.test_session)
            mock_display.assert_called_once_with([])

    def test_update_contract_invalid_input(self):
        # Non-integer contract ID or non-float amounts
        with patch('cli.has_permission', return_value=True), \
             patch('cli.prompt_input', side_effect=["abc", "notfloat", "notfloat", "1"] ), \
             patch('builtins.print') as mock_print:
            handle_update_contract(self.test_session)
            mock_print.assert_called_with("Invalid input. Please enter valid numbers for ID and amounts.\n")

    def test_delete_contract_invalid_id(self):
        # Invalid contract ID
        with patch('cli.has_permission', return_value=True), \
             patch('cli.prompt_input', return_value="notint"), \
             patch('cli.confirm_action', return_value=True), \
             patch('builtins.print') as mock_print:
            handle_delete_contract(self.test_session)
            mock_print.assert_called_with("Invalid contract ID.\n")

    def test_filter_contracts_invalid_selection(self):
        # Invalid contract status filter selection
        with patch('cli.has_permission', return_value=True), \
             patch('cli.prompt_input', return_value="3"), \
             patch('builtins.print') as mock_print:
            handle_filter_contracts(self.test_session)
            mock_print.assert_called_with("Invalid selection. Please enter 1 or 2.\n")

    def test_manage_events_no_permission(self):
        no_perm_session = {
            'username': 'no_perm_user',
            'role': 'UnknownRole'
        }
        with patch('cli.has_permission', return_value=False), \
             patch('builtins.print') as mock_print:
            manage_events(no_perm_session)
            mock_print.assert_called_with('Permission denied.\n')

    def test_create_event_invalid_input(self):
        # Invalid event ID or attendees
        with patch('cli.has_permission', return_value=True), \
             patch('cli.prompt_input', side_effect=["notint", "2024-01-01", "2024-01-02", "Paris", "notint", "Notes"]), \
             patch('builtins.print') as mock_print:
            handle_create_event(self.test_session)
            mock_print.assert_called_with("Invalid input. Please enter valid numbers for IDs and attendees.\n")

    def test_update_event_not_found(self):
        # Trying to update a non-existent event
        with patch('cli.has_permission', return_value=True), \
             patch('cli.prompt_input', side_effect=["9999", "2024-01-01", "2024-01-02", "Paris", "100", "Notes"]), \
             patch('cli.update_event', return_value='Event not found'), \
             patch('builtins.print') as mock_print:
            handle_update_event(self.test_session)
            mock_print.assert_called_with('Event not found\n')

    def test_delete_event_not_found(self):
        # Trying to delete a non-existent event
        with patch('cli.has_permission', return_value=True), \
             patch('cli.prompt_input', return_value="9999"), \
             patch('cli.confirm_action', return_value=True), \
             patch('cli.delete_event', return_value='Event not found'), \
             patch('builtins.print') as mock_print:
            handle_delete_event(self.test_session)
            mock_print.assert_called_with('Event not found\n')

    def test_filter_events_unassigned_none(self):
        # No unassigned events found
        with patch('cli.filter_events_unassigned', return_value=[]), \
             patch('cli.display_events') as mock_display:
            handle_filter_events_unassigned(self.test_session)
            mock_display.assert_called_once_with([], title='Unassigned Events')

    def test_filter_events_assigned_to_me_none(self):
        # Support user with no assigned events
        support_session = {
            'username': 'support_user',
            'role': 'Support'
        }
        with patch('cli.filter_events_by_support_user', return_value=[]), \
             patch('cli.display_events') as mock_display:
            handle_filter_events_assigned_to_me(support_session)
            mock_display.assert_called_once_with([], title='Events Assigned to You')

    def test_interactive_session_logout_immediately(self):
        # Test interactive session logs out on immediate logout selection
        mock_options = {"1": "Logout"}
        with patch('cli.build_main_menu_options', return_value=mock_options), \
             patch('cli.display_main_menu'), \
             patch('cli.prompt_choice', return_value='1'), \
             patch('builtins.print') as mock_print:
            interactive_session(self.test_session)
            mock_print.assert_called_with('Logging out...')

    def test_interactive_session_invalid_selection_twice(self):
        # Test repeated invalid selections then logout
        mock_options = {"1": "View Profile", "2": "Logout"}
        with patch('cli.build_main_menu_options', return_value=mock_options), \
             patch('cli.display_main_menu'), \
             patch('cli.prompt_choice', side_effect=['999', '998', '2']), \
             patch('builtins.print') as mock_print:
            interactive_session(self.test_session)
            # Check that it printed invalid selection messages twice
            mock_print.assert_any_call('Invalid selection. Please try again.\n')
            # Finally logs out
            mock_print.assert_any_call('Logging out...')


if __name__ == '__main__':
    unittest.main()
