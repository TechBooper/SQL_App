import argparse
import sys
import getpass
import logging
from auth import authenticate, get_user_role, hash_password, create_user
from controllers import (
    create_user,
    update_user,
    delete_user,
    create_client,
    update_client,
    delete_client,
    create_contract,
    update_contract,
    delete_contract,
    create_event,
    update_event,
    delete_event,
    assign_support_to_event,
    get_all_clients,
    get_all_events,
    get_all_contracts,
    filter_contracts_by_status,
    filter_events_unassigned,
    filter_events_by_support_user
)
import sentry_setup
from models import User, Role

logging.basicConfig(
    filename='cli.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def main():
    parser = argparse.ArgumentParser(description="Epic Events CRM CLI")
    subparsers = parser.add_subparsers(dest='command')

    # Login Command
    login_parser = subparsers.add_parser('login')
    login_parser.add_argument('username')

    args = parser.parse_args()
    session = {}

    if args.command == 'login':
        password = getpass.getpass("Password: ")
        user_info = authenticate(args.username, password)
        if user_info:
            session['user_id'] = user_info['user_id']
            session['role_id'] = user_info['role_id']
            session['role'] = get_user_role(user_info['user_id'])
            print(f"Logged in as {args.username} with role {session['role']}.")

            # Start interactive session
            interactive_session(session)
        else:
            print("Authentication failed.")
    else:
        parser.print_help()

def interactive_session(session):
    print("Type 'help' to see available commands.")
    while True:
        try:
            command_input = input("> ").strip()
            if not command_input:
                continue
            command_parts = command_input.split()
            command = command_parts[0]

            if command == 'logout':
                print("Logged out.")
                break
            elif command == 'help':
                print("Available commands:")
                print("  view_profile")
                print("  update_profile <email>")
                print("  create_user <username> <password> <role_id> <email>  # Gestion only")
                print("  update_user <user_id> <username> <email> <role_id>  # Gestion only")
                print("  delete_user <user_id>                                # Gestion only")
                print("  create_client <first_name> <last_name> <email> <phone> <company_name>  # Commercial only")
                print("  update_client <client_id> <first_name> <last_name> <email> <phone> <company_name>")
                print("  delete_client <client_id>                            # Gestion only")
                print("  create_contract <client_id> <total_amount> <amount_remaining> <status>")
                print("  update_contract <contract_id> <total_amount> <amount_remaining> <status>")
                print("  delete_contract <contract_id>                        # Gestion only")
                print("  create_event <contract_id> <event_date_start> <event_date_end> <location> <attendees> <notes>  # Commercial only")
                print("  update_event <event_id> <event_date_start> <event_date_end> <location> <attendees> <notes>")
                print("  assign_support <event_id> <support_user_id>          # Gestion only")
                print("  view_clients")
                print("  view_contracts")
                print("  view_events")
                print("  filter_contracts <status>                            # Commercial only")
                print("  filter_events_unassigned                             # Gestion only")
                print("  filter_events_assigned_to_me                         # Support only")
                print("  logout")
            elif command == 'view_profile':
                user_id = session['user_id']
                user = User.get_by_id(user_id)
                if user:
                    print(f"User Profile:")
                    print(f"  Username: {user.username}")
                    print(f"  Email: {user.email}")
                    print(f"  Role: {session['role']}")
                else:
                    print("Error fetching user profile.")
            elif command == 'update_profile':
                if len(command_parts) == 2:
                    new_email = command_parts[1]
                    user_id = session['user_id']
                    user = User.get_by_id(user_id)
                    if user:
                        user.email = new_email
                        if user.update():
                            print("Profile updated successfully.")
                        else:
                            print("Failed to update profile.")
                    else:
                        print("User not found.")
                else:
                    print("Usage: update_profile <new_email>")
            elif command == 'create_user':
                if session['role'] == 'Gestion':
                    if len(command_parts) == 5:
                        username = command_parts[1]
                        password = command_parts[2]
                        role_id = int(command_parts[3])
                        email = command_parts[4]
                        password_hash = hash_password(password)
                        result = create_user(
                            username,
                            password_hash,
                            role_id,
                            email
                        )
                        if result:
                            print(f"User {username} created successfully.")
                        else:
                            print("Failed to create user.")
                    else:
                        print("Usage: create_user <username> <password> <role_id> <email>")
                else:
                    print("Permission denied.")
            elif command == 'update_user':
                if session['role'] == 'Gestion':
                    if len(command_parts) == 5:
                        user_id_to_update = int(command_parts[1])
                        username = command_parts[2]
                        email = command_parts[3]
                        role_id = int(command_parts[4])
                        result = update_user(
                            session['user_id'],
                            user_id_to_update,
                            username,
                            email,
                            role_id
                        )
                        print(result)
                    else:
                        print("Usage: update_user <user_id> <username> <email> <role_id>")
                else:
                    print("Permission denied.")
            elif command == 'delete_user':
                if session['role'] == 'Gestion':
                    if len(command_parts) == 2:
                        user_id_to_delete = int(command_parts[1])
                        result = delete_user(
                            session['user_id'],
                            user_id_to_delete
                        )
                        print(result)
                    else:
                        print("Usage: delete_user <user_id>")
                else:
                    print("Permission denied.")
            elif command == 'create_client':
                if session['role'] == 'Commercial':
                    if len(command_parts) >= 6:
                        first_name = command_parts[1]
                        last_name = command_parts[2]
                        email = command_parts[3]
                        phone = command_parts[4]
                        company_name = ' '.join(command_parts[5:])
                        result = create_client(
                            session['user_id'],
                            first_name,
                            last_name,
                            email,
                            phone,
                            company_name
                        )
                        print(result)
                    else:
                        print("Usage: create_client <first_name> <last_name> <email> <phone> <company_name>")
                else:
                    print("Permission denied.")
            elif command == 'update_client':
                if session['role'] in ['Commercial', 'Gestion']:
                    if len(command_parts) >= 7:
                        client_id = int(command_parts[1])
                        first_name = command_parts[2]
                        last_name = command_parts[3]
                        email = command_parts[4]
                        phone = command_parts[5]
                        company_name = ' '.join(command_parts[6:])
                        result = update_client(
                            session['user_id'],
                            client_id,
                            first_name,
                            last_name,
                            email,
                            phone,
                            company_name
                        )
                        print(result)
                    else:
                        print("Usage: update_client <client_id> <first_name> <last_name> <email> <phone> <company_name>")
                else:
                    print("Permission denied.")
            elif command == 'delete_client':
                if session['role'] == 'Gestion':
                    if len(command_parts) == 2:
                        client_id = int(command_parts[1])
                        result = delete_client(
                            session['user_id'],
                            client_id
                        )
                        print(result)
                    else:
                        print("Usage: delete_client <client_id>")
                else:
                    print("Permission denied.")
            elif command == 'create_contract':
                if session['role'] in ['Commercial', 'Gestion']:
                    if len(command_parts) == 5:
                        client_id = int(command_parts[1])
                        total_amount = float(command_parts[2])
                        amount_remaining = float(command_parts[3])
                        status = command_parts[4]
                        result = create_contract(
                            session['user_id'],
                            client_id,
                            total_amount,
                            amount_remaining,
                            status
                        )
                        print(result)
                    else:
                        print("Usage: create_contract <client_id> <total_amount> <amount_remaining> <status>")
                else:
                    print("Permission denied.")
            elif command == 'update_contract':
                if session['role'] in ['Commercial', 'Gestion']:
                    if len(command_parts) == 5:
                        contract_id = int(command_parts[1])
                        total_amount = float(command_parts[2])
                        amount_remaining = float(command_parts[3])
                        status = command_parts[4]
                        result = update_contract(
                            session['user_id'],
                            contract_id,
                            total_amount,
                            amount_remaining,
                            status
                        )
                        print(result)
                    else:
                        print("Usage: update_contract <contract_id> <total_amount> <amount_remaining> <status>")
                else:
                    print("Permission denied.")
            elif command == 'delete_contract':
                if session['role'] == 'Gestion':
                    if len(command_parts) == 2:
                        contract_id = int(command_parts[1])
                        result = delete_contract(
                            session['user_id'],
                            contract_id
                        )
                        print(result)
                    else:
                        print("Usage: delete_contract <contract_id>")
                else:
                    print("Permission denied.")
            elif command == 'create_event':
                if session['role'] == 'Commercial':
                    if len(command_parts) >= 7:
                        contract_id = int(command_parts[1])
                        event_date_start = command_parts[2]
                        event_date_end = command_parts[3]
                        location = command_parts[4]
                        attendees = int(command_parts[5])
                        notes = ' '.join(command_parts[6:])
                        result = create_event(
                            session['user_id'],
                            contract_id,
                            event_date_start,
                            event_date_end,
                            location,
                            attendees,
                            notes
                        )
                        print(result)
                    else:
                        print("Usage: create_event <contract_id> <event_date_start> <event_date_end> <location> <attendees> <notes>")
                else:
                    print("Permission denied.")
            elif command == 'update_event':
                if session['role'] in ['Support', 'Gestion']:
                    if len(command_parts) >= 7:
                        event_id = int(command_parts[1])
                        event_date_start = command_parts[2]
                        event_date_end = command_parts[3]
                        location = command_parts[4]
                        attendees = int(command_parts[5])
                        notes = ' '.join(command_parts[6:])
                        result = update_event(
                            session['user_id'],
                            event_id,
                            event_date_start,
                            event_date_end,
                            location,
                            attendees,
                            notes
                        )
                        print(result)
                    else:
                        print("Usage: update_event <event_id> <event_date_start> <event_date_end> <location> <attendees> <notes>")
                else:
                    print("Permission denied.")
            elif command == 'assign_support':
                if session['role'] == 'Gestion':
                    if len(command_parts) == 3:
                        event_id = int(command_parts[1])
                        support_user_id = int(command_parts[2])
                        result = assign_support_to_event(
                            session['user_id'],
                            event_id,
                            support_user_id
                        )
                        print(result)
                    else:
                        print("Usage: assign_support <event_id> <support_user_id>")
                else:
                    print("Permission denied.")
            elif command == 'view_clients':
                clients = get_all_clients()
                for client in clients:
                    print(client)
            elif command == 'view_contracts':
                contracts = get_all_contracts()
                for contract in contracts:
                    print(contract)
            elif command == 'view_events':
                events = get_all_events(session['user_id'])
                for event in events:
                    print(event)
            elif command == 'filter_contracts':
                if session['role'] == 'Commercial':
                    if len(command_parts) == 2:
                        status = command_parts[1]
                        contracts = filter_contracts_by_status(session['user_id'], status)
                        for contract in contracts:
                            print(contract)
                    else:
                        print("Usage: filter_contracts <status>")
                else:
                    print("Permission denied.")
            elif command == 'filter_events_unassigned':
                if session['role'] == 'Gestion':
                    events = filter_events_unassigned()
                    for event in events:
                        print(event)
                else:
                    print("Permission denied.")
            elif command == 'filter_events_assigned_to_me':
                if session['role'] == 'Support':
                    events = filter_events_by_support_user(session['user_id'])
                    for event in events:
                        print(event)
                else:
                    print("Permission denied.")
            else:
                print("Unknown command. Type 'help' to see available commands.")
        except Exception as e:
            sentry_setup.capture_exception(e)
            logging.error(f"An error occurred: {e}")
            print("An error occurred while processing your command.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        sentry_setup.capture_exception(e)
        logging.error(f"An unexpected error occurred: {e}")
        print("An unexpected error occurred.")
