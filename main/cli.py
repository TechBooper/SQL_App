"""CLI application for Epic Events CRM.

This module provides a command-line interface for the Epic Events CRM application.
Users can authenticate and perform various operations based on their roles and permissions.
"""

import argparse
import sys
import getpass
import logging
import os
from auth import authenticate, get_user_role, hash_password, has_permission

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(BASE_DIR)

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
    filter_events_by_support_user,
)
import sentry_sdk
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from configs import sentry_setup
from models import User, Role

logging.basicConfig(
    filename="cli.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

DATABASE_FOLDER = os.path.join(BASE_DIR, 'database')
DATABASE_URL = os.path.join(DATABASE_FOLDER, 'app.db')

def main():
    """Main entry point for the CLI application.

    Parses command-line arguments and initiates the login process.
    """
    # Check if the database exists
    if not os.path.exists(DATABASE_URL):
        print("Database not found. Please initialize the database by running 'python database.py' before proceeding.")
        sys.exit(1)

    parser = argparse.ArgumentParser(description="Epic Events CRM CLI")
    subparsers = parser.add_subparsers(dest="command")

    # Login Command
    login_parser = subparsers.add_parser("login")
    login_parser.add_argument("username")

    args = parser.parse_args()
    session = {}

    if args.command == "login":
        password = getpass.getpass("Password: ")
        user_info = authenticate(args.username, password)
        if user_info:
            session["user_id"] = user_info["user_id"]
            session["role_id"] = user_info["role_id"]
            session["role"] = get_user_role(user_info["user_id"])
            print(f"Logged in as {args.username} with role {session['role']}.")
            # Start interactive session
            interactive_session(session)
        else:
            print("Authentication failed.")
    else:
        parser.print_help()


def interactive_session(session):
    """Starts an interactive session for the authenticated user.

    Processes user commands in a loop until the user logs out.

    Args:
        session (dict): Contains user session information, including user ID and role.
    """
    print("Type 'help' to see available commands.")
    while True:
        try:
            command_input = input("> ").strip()
            if not command_input:
                continue
            command_parts = command_input.split()
            command = command_parts[0]

            if command == "logout":
                print("Logged out.")
                break
            elif command == "help":
                print("Available commands:")
                print("  view_profile")
                print("  update_profile <email>")
                print(
                    "  create_user <username> <role_id> <email>  # Management only"
                )
                print(
                    "  update_user <user_id> <username> <email> <role_id>  # Management only"
                )
                print(
                    "  delete_user <user_id>                                # Management only"
                )
                print(
                    "  create_client <first_name> <last_name> <email> <phone> <company_name>  # Commercial only"
                )
                print(
                    "  update_client <client_id> <first_name> <last_name> <email> <phone> <company_name>"
                )
                print(
                    "  delete_client <client_id>                            # Management only"
                )
                print(
                    "  create_contract <client_id> <total_amount> <amount_remaining> <status>"
                )
                print(
                    "  update_contract <contract_id> <total_amount> <amount_remaining> <status>"
                )
                print(
                    "  delete_contract <contract_id>                        # Management only"
                )
                print(
                    "  create_event <contract_id> <event_date_start> <event_date_end> <location> <attendees> <notes>  # Commercial only"
                )
                print(
                    "  update_event <event_id> <event_date_start> <event_date_end> <location> <attendees> <notes>"
                )
                print(
                    "  assign_support <event_id> <support_user_id>          # Management only"
                )
                print("  view_clients")
                print("  view_contracts")
                print("  view_events")
                print(
                    "  filter_contracts <status>                            # Commercial only"
                )
                print(
                    "  filter_events_unassigned                             # Management only"
                )
                print(
                    "  filter_events_assigned_to_me                         # Support only"
                )
                print("  logout")
            elif command == "view_profile":
                if has_permission(session["role_id"], "user", "read"):
                    user_id = session["user_id"]
                    user = User.get_by_id(user_id)
                    if user:
                        print(f"User Profile:")
                        print(f"  Username: {user.username}")
                        print(f"  Email: {user.email}")
                        print(f"  Role: {session['role']}")
                    else:
                        print("Error fetching user profile.")
                else:
                    print("Permission denied.")
            elif command == "update_profile":
                if has_permission(session["role_id"], "user", "update"):
                    if len(command_parts) == 2:
                        new_email = command_parts[1]
                        user_id = session["user_id"]
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
                else:
                    print("Permission denied.")
            elif command == "create_user":
                if has_permission(session["role_id"], "user", "create"):
                    if len(command_parts) == 4:
                        username = command_parts[1]
                        role_id = int(command_parts[2])
                        email = command_parts[3]
                        password = getpass.getpass("Password: ")
                        result = create_user(
                            admin_user_id=session["user_id"],
                            username=username,
                            password=password,
                            role_id=role_id,
                            email=email,
                        )
                        print(result)
                    else:
                        print("Usage: create_user <username> <role_id> <email>")
                else:
                    print("Permission denied.")
            elif command == "update_user":
                if has_permission(session["role_id"], "user", "update"):
                    if len(command_parts) == 5:
                        user_id_to_update = int(command_parts[1])
                        username = command_parts[2]
                        email = command_parts[3]
                        role_id = int(command_parts[4])
                        result = update_user(
                            admin_user_id=session["user_id"],
                            user_id=user_id_to_update,
                            username=username,
                            email=email,
                            role_id=role_id,
                        )
                        print(result)
                    else:
                        print(
                            "Usage: update_user <user_id> <username> <email> <role_id>"
                        )
                else:
                    print("Permission denied.")

            elif command == "delete_user":
                if has_permission(session["role_id"], "user", "delete"):
                    if len(command_parts) == 2:
                        user_id_to_delete = int(command_parts[1])
                        result = delete_user(
                            admin_user_id=session["user_id"], user_id=user_id_to_delete
                        )
                        print(result)
                    else:
                        print("Usage: delete_user <user_id>")
                else:
                    print("Permission denied.")

            elif command == "create_client":
                if has_permission(session["role_id"], "client", "create"):
                    if len(command_parts) >= 6:
                        first_name = command_parts[1]
                        last_name = command_parts[2]
                        email = command_parts[3]
                        phone = command_parts[4]
                        company_name = " ".join(command_parts[5:])
                        result = create_client(
                            user_id=session["user_id"],
                            first_name=first_name,
                            last_name=last_name,
                            email=email,
                            phone=phone,
                            company_name=company_name,
                        )
                        print(result)
                    else:
                        print(
                            "Usage: create_client <first_name> <last_name> <email> <phone> <company_name>"
                        )
                else:
                    print("Permission denied.")

            elif command == "update_client":
                if has_permission(session["role_id"], "client", "update"):
                    if len(command_parts) >= 7:
                        client_id = int(command_parts[1])
                        first_name = command_parts[2]
                        last_name = command_parts[3]
                        email = command_parts[4]
                        phone = command_parts[5]
                        company_name = " ".join(command_parts[6:])
                        result = update_client(
                            user_id=session["user_id"],
                            client_id=client_id,
                            first_name=first_name,
                            last_name=last_name,
                            email=email,
                            phone=phone,
                            company_name=company_name,
                        )
                        print(result)
                    else:
                        print(
                            "Usage: update_client <client_id> <first_name> <last_name> <email> <phone> <company_name>"
                        )
                else:
                    print("Permission denied.")

            elif command == "delete_client":
                if has_permission(session["role_id"], "client", "delete"):
                    if len(command_parts) == 2:
                        client_id = int(command_parts[1])
                        result = delete_client(
                            user_id=session["user_id"], client_id=client_id
                        )
                        print(result)
                    else:
                        print("Usage: delete_client <client_id>")
                else:
                    print("Permission denied.")

            elif command == "create_contract":
                if has_permission(session["role_id"], "contract", "create"):
                    if len(command_parts) >= 5:
                        client_id = int(command_parts[1])
                        total_amount = float(command_parts[2])
                        amount_remaining = float(command_parts[3])
                        # Join the rest of the command_parts to capture 'status' even if it contains spaces
                        status_input = " ".join(command_parts[4:]).strip().lower()
                        # Normalize and validate status input
                        if status_input in ['signed', 'not signed']:
                            status = 'Signed' if status_input == 'signed' else 'Not Signed'
                        else:
                            print("Invalid status. Please enter 'Signed' or 'Not Signed'.")
                            continue  # Return to the command prompt
                        # For debugging: print the status value
                        print(f"Status after processing: '{status}'")
                        result = create_contract(
                            user_id=session["user_id"],
                            client_id=client_id,
                            total_amount=total_amount,
                            amount_remaining=amount_remaining,
                            status=status,
                        )
                        print(result)
                    else:
                        print(
                            "Usage: create_contract <client_id> <total_amount> <amount_remaining> <status ('Signed'/'Not Signed')>"
                        )
                else:
                    print("Permission denied.")

            elif command == "update_contract":
                if has_permission(session["role_id"], "contract", "update"):
                    if len(command_parts) == 5:
                        contract_id = int(command_parts[1])
                        total_amount = float(command_parts[2])
                        amount_remaining = float(command_parts[3])
                        status = command_parts[4]
                        result = update_contract(
                            user_id=session["user_id"],
                            contract_id=contract_id,
                            total_amount=total_amount,
                            amount_remaining=amount_remaining,
                            status=status,
                        )
                        print(result)
                    else:
                        print(
                            "Usage: update_contract <contract_id> <total_amount> <amount_remaining> <status>"
                        )
                else:
                    print("Permission denied.")

            elif command == "delete_contract":
                if has_permission(session["role_id"], "contract", "delete"):
                    if len(command_parts) == 2:
                        contract_id = int(command_parts[1])
                        result = delete_contract(
                            user_id=session["user_id"], contract_id=contract_id
                        )
                        print(result)
                    else:
                        print("Usage: delete_contract <contract_id>")
                else:
                    print("Permission denied.")

            elif command == "create_event":
                if has_permission(session["role_id"], "event", "create"):
                    if len(command_parts) >= 7:
                        contract_id = int(command_parts[1])
                        event_date_start = command_parts[2]
                        event_date_end = command_parts[3]
                        location = command_parts[4]
                        attendees = int(command_parts[5])
                        notes = " ".join(command_parts[6:])
                        result = create_event(
                            user_id=session["user_id"],
                            contract_id=contract_id,
                            event_date_start=event_date_start,
                            event_date_end=event_date_end,
                            location=location,
                            attendees=attendees,
                            notes=notes,
                        )
                        print(result)
                    else:
                        print(
                            "Usage: create_event <contract_id> <event_date_start> <event_date_end> <location> <attendees> <notes>"
                        )
                else:
                    print("Permission denied.")

            elif command == "update_event":
                if has_permission(session["role_id"], "event", "update"):
                    if len(command_parts) >= 7:
                        event_id = int(command_parts[1])
                        event_date_start = command_parts[2]
                        event_date_end = command_parts[3]
                        location = command_parts[4]
                        attendees = int(command_parts[5])
                        notes = " ".join(command_parts[6:])
                        result = update_event(
                            user_id=session["user_id"],
                            event_id=event_id,
                            event_date_start=event_date_start,
                            event_date_end=event_date_end,
                            location=location,
                            attendees=attendees,
                            notes=notes,
                        )
                        print(result)
                    else:
                        print(
                            "Usage: update_event <event_id> <event_date_start> <event_date_end> <location> <attendees> <notes>"
                        )
                else:
                    print("Permission denied.")

            elif command == "assign_support":
                if has_permission(session["role_id"], "event", "update"):
                    if len(command_parts) == 3:
                        event_id = int(command_parts[1])
                        support_user_id = int(command_parts[2])
                        result = assign_support_to_event(
                            user_id=session["user_id"],
                            event_id=event_id,
                            support_user_id=support_user_id,
                        )
                        print(result)
                    else:
                        print("Usage: assign_support <event_id> <support_user_id>")
                else:
                    print("Permission denied.")

            elif command == "view_clients":
                if has_permission(session["role_id"], "client", "read"):
                    clients = get_all_clients()
                    for client in clients:
                        print(client)
                else:
                    print("Permission denied.")

            elif command == "view_contracts":
                if has_permission(session["role_id"], "contract", "read"):
                    contracts = get_all_contracts()
                    for contract in contracts:
                        print(contract)
                else:
                    print("Permission denied.")

            elif command == "view_events":
                if has_permission(session["role_id"], "event", "read"):
                    events = get_all_events(session["user_id"])
                    for event in events:
                        print(event)
                else:
                    print("Permission denied.")

            elif command == "filter_contracts":
                if has_permission(session["role_id"], "contract", "read"):
                    if len(command_parts) == 2:
                        status = command_parts[1]
                        contracts = filter_contracts_by_status(status)
                        for contract in contracts:
                            print(contract)
                    else:
                        print("Usage: filter_contracts <status>")
                else:
                    print("Permission denied.")

            elif command == "filter_events_unassigned":
                if has_permission(session["role_id"], "event", "read"):
                    events = filter_events_unassigned()
                    for event in events:
                        print(event)
                else:
                    print("Permission denied.")

            elif command == "filter_events_assigned_to_me":
                if has_permission(session["role_id"], "event", "read"):
                    events = filter_events_by_support_user(session["user_id"])
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
        sentry_sdk.capture_exception(e)
        logging.error(f"An error occurred: {e}")
        print("An error occurred while processing your command.")
