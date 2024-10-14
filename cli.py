import argparse
import sys
import getpass
from auth import authenticate, get_user_role
from profile import view_profile, update_profile
from controllers import create_client, update_contract, view_contracts, has_permission
import sentry_setup

def main():
    parser = argparse.ArgumentParser(description="Application CLI")
    subparsers = parser.add_subparsers(dest='command')

    # Login Command
    login_parser = subparsers.add_parser('login')
    login_parser.add_argument('username')

    # Additional Commands as Needed...

    args = parser.parse_args()
    session = {}

    if args.command == 'login':
        password = getpass.getpass("Password: ")
        user = authenticate(args.username, password)
        if user:
            session['user_id'] = user['user_id']
            session['role'] = get_user_role(user['user_id'])
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
                print("  view_contracts")
                print("  logout")
            elif command == 'view_profile':
                view_profile(session['user_id'])
            elif command == 'update_profile':
                if len(command_parts) > 1:
                    bio = ' '.join(command_parts[1:])
                    update_profile(session['user_id'], bio)
                else:
                    print("Usage: update_profile <bio>")
            elif command == 'create_client':
                if len(command_parts) >= 6:
                    first_name = command_parts[1]
                    last_name = command_parts[2]
                    email = command_parts[3]
                    phone = command_parts[4]
                    company_name = ' '.join(command_parts[5:])
                    if has_permission(session['user_id'], 'client', 'create'):
                        create_client(session['user_id'], first_name, last_name, email, phone, company_name)
                    else:
                        print("You do not have permission to create clients.")
                else:
                    print("Usage: create_client <first_name> <last_name> <email> <phone> <company_name>")
            elif command == 'update_contract':
                if len(command_parts) == 5:
                    contract_id = int(command_parts[1])
                    total_amount = float(command_parts[2])
                    amount_remaining = float(command_parts[3])
                    status = command_parts[4]
                    if has_permission(session['user_id'], 'contract', 'update'):
                        update_contract(session['user_id'], contract_id, total_amount, amount_remaining, status)
                    else:
                        print("You do not have permission to update contracts.")
                else:
                    print("Usage: update_contract <contract_id> <total_amount> <amount_remaining> <status>")
            elif command == 'view_contracts':
                if has_permission(session['user_id'], 'contract', 'read'):
                    view_contracts(session['user_id'])
                else:
                    print("You do not have permission to view contracts.")
            else:
                print("Unknown command. Type 'help' to see available commands.")
        except Exception as e:
            sentry_setup.capture_exception(e)
            print("An error occurred while processing your command.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        sentry_setup.capture_exception(e)
        print("An unexpected error occurred.")
