# CLI.py

import argparse
import sys
import getpass
import logging
from auth import authenticate, get_user_role
from controllers import (
    create_client,
    update_contract,
    update_event,
    create_event,
    assign_support_to_event,
    get_all_clients,
    get_all_contracts,
    get_all_events,
)
from models import User, Role
from permissions import has_permission
import sentry_setup

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
                print("  update_profile <bio>")
                print("  create_client <first_name> <last_name> <email> <phone> <company_name>")
                print("  update_contract <contract_id> <total_amount> <amount_remaining> <status>")
                print("  create_event <contract_id> <event_date_start> <event_date_end> <location> <attendees> <notes>")
                print("  assign_support <event_id> <support_user_id>")
                print("  view_clients")
                print("  view_contracts")
                print("  view_events")
                print("  logout")
            elif command == 'view_profile':
                # Implement view_profile function or adjust as needed
                pass
            elif command == 'update_profile':
                # Implement update_profile function or adjust as needed
                pass
            elif command == 'create_client':
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
            elif command == 'update_contract':
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
            elif command == 'create_event':
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
            elif command == 'assign_support':
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
            elif command == 'view_clients':
                clients = get_all_clients()
                for client in clients:
                    print(client)
            elif command == 'view_contracts':
                contracts = get_all_contracts()
                for contract in contracts:
                    print(contract)
            elif command == 'view_events':
                events = get_all_events()
                for event in events:
                    print(event)
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
