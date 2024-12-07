# cli.py

"""
CLI application for Epic Events CRM.

This module serves as the controller for the Epic Events CRM application.
It manages user authentication, interacts with the models, and utilizes the views
to handle user interactions.
"""

import sys
import re
import logging
import getpass
import os
import sentry_sdk
from auth import authenticate, get_user_role, has_permission
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
    get_all_users,
)
from models import User
from configs import sentry_setup
from views import (
    display_welcome_message,
    display_login_prompt,
    display_main_menu,
    prompt_choice,
    display_profile,
    display_clients,
    display_contracts,
    display_events,
    prompt_input,
    confirm_action,
    display_users,
)
import sentry_sdk

logging.basicConfig(
    filename="cli.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__)))
DATABASE_FOLDER = os.path.join(BASE_DIR, "database")
DATABASE_URL = os.path.join(DATABASE_FOLDER, "app.db")


def main():
    """Main entry point for the CLI application.

    Initiates the login process.
    """
    # Check if the database exists
    if not os.path.exists(DATABASE_URL):
        print(
            "Database not found. Please initialize the database by running 'python database.py' before proceeding."
        )
        sys.exit(1)

    session = {}
    display_welcome_message()
    while True:
        username, password = display_login_prompt()
        user_info = authenticate(username, password)
        if user_info:
            session["user_id"] = user_info["user_id"]
            session["role_id"] = user_info["role_id"]
            session["role"] = get_user_role(user_info["user_id"])
            print(f"\nLogged in as {username} with role {session['role']}.\n")
            # Start interactive session
            interactive_session(session)
            break
        else:
            print("Authentication failed. Please try again.\n")


def interactive_session(session):
    """Starts an interactive session for the authenticated user.

    Displays menus and handles user choices.

    Args:
        session (dict): Contains user session information, including user ID and role.
    """
    while True:
        options = build_main_menu_options(session)
        display_main_menu(options)
        choice = prompt_choice()

        # Check if the user choice is a valid option
        if choice in options:
            selection = options[choice]

            if selection == "View Profile":
                handle_view_profile(session)
            elif selection == "Update Email":
                handle_update_email(session)
            elif selection == "Manage Users":
                manage_users(session)
            elif selection == "Manage Clients":
                manage_clients(session)
            elif selection == "Manage Contracts":
                manage_contracts(session)
            elif selection == "Manage Events":
                manage_events(session)
            elif selection == "Logout":
                print("Logging out...")
                break
            else:
                print("Invalid selection. Please try again.\n")
        else:
            # The user typed something that's not in the options
            print("Invalid selection. Please try again.\n")


def build_main_menu_options(session):
    """Builds the main menu options based on user permissions.

    Args:
        session (dict): User session data.

    Returns:
        dict: A dictionary mapping menu option numbers (as strings) to their descriptions.
    """
    options = {
        "1": "View Profile",
        "2": "Update Email",  # Renamed from "Update Profile" to "Update Email"
    }
    option_number = 3

    # Add 'Manage Users' if user has any user management permission or read permission for users
    if has_permission(
        session["role_id"], "user", "read"
    ) or has_any_user_management_permission(session):
        options[str(option_number)] = "Manage Users"
        option_number += 1

    # Add 'Manage Clients' if user has read permission for clients
    if has_permission(session["role_id"], "client", "read"):
        options[str(option_number)] = "Manage Clients"
        option_number += 1

    # Add 'Manage Contracts' if user has read permission for contracts
    if has_permission(session["role_id"], "contract", "read"):
        options[str(option_number)] = "Manage Contracts"
        option_number += 1

    # Add 'Manage Events' if user has read permission for events
    if has_permission(session["role_id"], "event", "read"):
        options[str(option_number)] = "Manage Events"
        option_number += 1

    # Finally, add the 'Logout' option
    options[str(option_number)] = "Logout"

    return options


def handle_view_users(session):
    """Handles the viewing of all users."""
    users = get_all_users()
    display_users(users)


def display_main_menu(options):
    """Displays the main menu based on available options.

    Args:
        options (dict): Menu options to display.
    """
    print("\nMain Menu:")
    for key in sorted(options.keys(), key=int):
        print(f"{key}. {options[key]}")


def has_any_user_management_permission(session):
    return (
        has_permission(session["role_id"], "user", "create")
        or has_permission(session["role_id"], "user", "update")
        or has_permission(session["role_id"], "user", "delete")
    )


def handle_view_profile(session):
    # All users can view their own profile
    user_id = session["user_id"]
    user = User.get_by_id(user_id)
    if user:
        display_profile(user)
    else:
        print("Error fetching user profile.\n")


def handle_update_email(session):
    """Handles updating the user's email."""
    print("\nUpdate Email:")

    # email regex pattern for validation purposes
    email_pattern = r"^[^@]+@[^@]+\.[^@]+$"

    while True:
        new_email = prompt_input("Enter new email address: ")
        if re.match(email_pattern, new_email):
            user_id = session["user_id"]
            user = User.get_by_id(user_id)
            if user:
                user.email = new_email
                if user.update():
                    print("Email updated successfully.\n")
                else:
                    print("Failed to update email.\n")
            else:
                print("User not found.\n")
            break
        else:
            print(
                "Invalid email format. Please enter a valid email (e.g., user@example.com)."
            )


def manage_users(session):
    if has_permission(
        session["role_id"], "user", "read"
    ) or has_any_user_management_permission(session):
        while True:
            options = build_manage_users_options(session)
            display_sub_menu("Manage Users", options)
            choice = prompt_choice()

            if choice in options:
                selection = options[choice]
                if selection == "View Users":
                    handle_view_users(session)
                elif selection == "Create User":
                    handle_create_user(session)
                elif selection == "Update User":
                    handle_update_user(session)
                elif selection == "Delete User":
                    handle_delete_user(session)
                elif selection == "Back to Main Menu":
                    break
                else:
                    print("Invalid selection. Please try again.\n")
            else:
                print("Invalid selection. Please try again.\n")
    else:
        print("Permission denied.\n")


def build_manage_users_options(session):
    options = {}
    option_number = 1

    # If user can read users, show 'View Users' first
    if has_permission(session["role_id"], "user", "read"):
        options[str(option_number)] = "View Users"
        option_number += 1

    if has_permission(session["role_id"], "user", "create"):
        options[str(option_number)] = "Create User"
        option_number += 1

    if has_permission(session["role_id"], "user", "update"):
        options[str(option_number)] = "Update User"
        option_number += 1

    if has_permission(session["role_id"], "user", "delete"):
        options[str(option_number)] = "Delete User"
        option_number += 1

    options[str(option_number)] = "Back to Main Menu"

    return options


def display_sub_menu(title, options):
    print(f"\n{title}:")
    for key in sorted(options.keys(), key=int):
        print(f"{key}. {options[key]}")


def handle_create_user(session):
    print("\nCreate User:")
    username = prompt_input("Enter username: ")
    email = prompt_input("Enter email: ")
    password = getpass.getpass("Enter password: ")
    confirm_password = getpass.getpass("Confirm password: ")
    if password != confirm_password:
        print("Passwords do not match.\n")
        return
    role_id_input = prompt_input(
        "Enter role ID (e.g., 1 for Management, 2 for Sales, 3 for Support): "
    )
    try:
        role_id = int(role_id_input)
        result = create_user(
            admin_user_id=session["user_id"],
            username=username,
            password=password,
            role_id=role_id,
            email=email,
        )
        print(f"{result}\n")
    except ValueError:
        print("Invalid role ID.\n")


def handle_update_user(session):
    print("\nUpdate User:")
    user_id_input = prompt_input("Enter user ID to update: ")
    try:
        user_id = int(user_id_input)
        username = prompt_input("Enter new username: ")
        email = prompt_input("Enter new email: ")
        role_id_input = prompt_input(
            "Enter new role ID (e.g., 1 for Management, 2 for Sales, 3 for Support): "
        )
        role_id = int(role_id_input)
        result = update_user(
            admin_user_id=session["user_id"],
            user_id=user_id,
            username=username,
            email=email,
            role_id=role_id,
        )
        print(f"{result}\n")
    except ValueError:
        print("Invalid input. Please enter valid numbers for IDs.\n")


def handle_delete_user(session):
    print("\nDelete User:")
    user_id_input = prompt_input("Enter user ID to delete: ")
    confirm = confirm_action("delete this user")
    if confirm:
        try:
            user_id = int(user_id_input)
            result = delete_user(admin_user_id=session["user_id"], user_id=user_id)
            print(f"{result}\n")
        except ValueError:
            print("Invalid user ID.\n")
    else:
        print("Deletion cancelled.\n")


def manage_clients(session):
    if has_permission(session["role_id"], "client", "read"):
        while True:
            options = build_manage_clients_options(session)
            display_sub_menu("Manage Clients", options)
            choice = prompt_choice()

            if choice in options:
                selection = options[choice]

                if selection == "View Clients":
                    handle_view_clients(session)
                elif selection == "Create Client":
                    handle_create_client(session)
                elif selection == "Update Client":
                    handle_update_client(session)
                elif selection == "Delete Client":
                    handle_delete_client(session)
                elif selection == "Back to Main Menu":
                    break
                else:
                    print("Invalid selection. Please try again.\n")
            else:
                print("Invalid selection. Please try again.\n")
    else:
        print("Permission denied.\n")


def build_manage_clients_options(session):
    options = {"1": "View Clients"}
    option_number = 2

    if has_permission(session["role_id"], "client", "create"):
        options[str(option_number)] = "Create Client"
        option_number += 1

    if has_permission(session["role_id"], "client", "update"):
        options[str(option_number)] = "Update Client"
        option_number += 1

    if has_permission(session["role_id"], "client", "delete"):
        options[str(option_number)] = "Delete Client"
        option_number += 1

    options[str(option_number)] = "Back to Main Menu"

    return options


def handle_view_clients(session):
    clients = get_all_clients()
    display_clients(clients)


def handle_create_client(session):
    print("\nCreate Client:")
    first_name = prompt_input("Enter first name: ")
    last_name = prompt_input("Enter last name: ")
    email = prompt_input("Enter email: ")
    phone = prompt_input("Enter phone number: ")
    company_name = prompt_input("Enter company name: ")
    result = create_client(
        user_id=session["user_id"],
        first_name=first_name,
        last_name=last_name,
        email=email,
        phone=phone,
        company_name=company_name,
    )
    print(f"{result}\n")


def handle_update_client(session):
    print("\nUpdate Client:")
    client_id_input = prompt_input("Enter client ID to update: ")
    try:
        client_id = int(client_id_input)
        first_name = prompt_input("Enter new first name: ")
        last_name = prompt_input("Enter new last name: ")
        email = prompt_input("Enter new email: ")
        phone = prompt_input("Enter new phone number: ")
        company_name = prompt_input("Enter new company name: ")
        result = update_client(
            user_id=session["user_id"],
            client_id=client_id,
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            company_name=company_name,
        )
        print(f"{result}\n")
    except ValueError:
        print("Invalid client ID.\n")


def handle_delete_client(session):
    print("\nDelete Client:")
    client_id_input = prompt_input("Enter client ID to delete: ")
    confirm = confirm_action("delete this client")
    if confirm:
        try:
            client_id = int(client_id_input)
            result = delete_client(user_id=session["user_id"], client_id=client_id)
            print(f"{result}\n")
        except ValueError:
            print("Invalid client ID.\n")
    else:
        print("Deletion cancelled.\n")


def manage_contracts(session):
    if has_permission(session["role_id"], "contract", "read"):
        while True:
            options = build_manage_contracts_options(session)
            display_sub_menu("Manage Contracts", options)
            choice = prompt_choice()

            if choice in options:
                selection = options[choice]
                if selection == "View Contracts":
                    handle_view_contracts(session)
                elif selection == "Create Contract":
                    handle_create_contract(session)
                elif selection == "Update Contract":
                    handle_update_contract(session)
                elif selection == "Delete Contract":
                    handle_delete_contract(session)
                elif selection == "Filter Contracts by Status":
                    handle_filter_contracts(session)
                elif selection == "Back to Main Menu":
                    break
                else:
                    print("Invalid selection. Please try again.\n")
            else:
                print("Invalid selection. Please try again.\n")
    else:
        print("Permission denied.\n")


def build_manage_contracts_options(session):
    options = {"1": "View Contracts"}
    option_number = 2

    if has_permission(session["role_id"], "contract", "create"):
        options[str(option_number)] = "Create Contract"
        option_number += 1

    if has_permission(session["role_id"], "contract", "update"):
        options[str(option_number)] = "Update Contract"
        option_number += 1

    if has_permission(session["role_id"], "contract", "delete"):
        options[str(option_number)] = "Delete Contract"
        option_number += 1

    options[str(option_number)] = "Filter Contracts by Status"
    option_number += 1

    options[str(option_number)] = "Back to Main Menu"

    return options


def handle_view_contracts(session):
    contracts = get_all_contracts()
    display_contracts(contracts)


def handle_create_contract(session):
    print("\nCreate Contract:")
    client_id_input = prompt_input("Enter client ID: ")
    total_amount_input = prompt_input("Enter total amount: ")
    amount_remaining_input = prompt_input("Enter amount remaining: ")

    # Provide clear options for status
    print("Select contract status:")
    print("1. Signed")
    print("2. Not Signed")
    status_choice = prompt_input("Enter the number corresponding to the status: ")

    status_mapping = {"1": "Signed", "2": "Not Signed"}
    status = status_mapping.get(status_choice)

    try:
        client_id = int(client_id_input)
        total_amount = float(total_amount_input)
        amount_remaining = float(amount_remaining_input)

        if status:
            result = create_contract(
                user_id=session["user_id"],
                client_id=client_id,
                total_amount=total_amount,
                amount_remaining=amount_remaining,
                status=status,
            )
            print(f"{result}\n")
        else:
            print("Invalid selection. Please enter 1 or 2.\n")
    except ValueError:
        print("Invalid input. Please enter valid numbers for IDs and amounts.\n")


def handle_update_contract(session):
    print("\nUpdate Contract:")
    contract_id_input = prompt_input("Enter contract ID to update: ")
    total_amount_input = prompt_input("Enter new total amount: ")
    amount_remaining_input = prompt_input("Enter new amount remaining: ")

    # Provide clear options for status
    print("Select new contract status:")
    print("1. Signed")
    print("2. Not Signed")
    status_choice = prompt_input("Enter the number corresponding to the status: ")

    status_mapping = {"1": "Signed", "2": "Not Signed"}
    status = status_mapping.get(status_choice)

    try:
        contract_id = int(contract_id_input)
        total_amount = float(total_amount_input)
        amount_remaining = float(amount_remaining_input)

        if status:
            result = update_contract(
                user_id=session["user_id"],
                contract_id=contract_id,
                total_amount=total_amount,
                amount_remaining=amount_remaining,
                status=status,
            )
            print(f"{result}\n")
        else:
            print("Invalid selection. Please enter 1 or 2.\n")
    except ValueError:
        print("Invalid input. Please enter valid numbers for IDs and amounts.\n")


def handle_delete_contract(session):
    print("\nDelete Contract:")
    contract_id_input = prompt_input("Enter contract ID to delete: ")
    confirm = confirm_action("delete this contract")
    if confirm:
        try:
            contract_id = int(contract_id_input)
            result = delete_contract(
                user_id=session["user_id"], contract_id=contract_id
            )
            print(f"{result}\n")
        except ValueError:
            print("Invalid contract ID.\n")
    else:
        print("Deletion cancelled.\n")


def handle_filter_contracts(session):
    print("\nFilter Contracts by Status:")
    print("Select contract status to filter:")
    print("1. Signed")
    print("2. Not Signed")
    status_choice = prompt_input("Enter the number corresponding to the status: ")

    status_mapping = {"1": "Signed", "2": "Not Signed"}
    status = status_mapping.get(status_choice)

    if status:
        contracts = filter_contracts_by_status(status)
        if not contracts:
            print(f"No contracts found with status '{status}'.\n")
            return
        display_contracts(contracts, title=f"Contracts with status '{status}'")
    else:
        print("Invalid selection. Please enter 1 or 2.\n")


def manage_events(session):
    if has_permission(session["role_id"], "event", "read"):
        while True:
            options = build_manage_events_options(session)
            display_sub_menu("Manage Events", options)
            choice = prompt_choice()

            if choice in options:
                selection = options[choice]
                if selection == "View Events":
                    handle_view_events(session)
                elif selection == "Create Event":
                    handle_create_event(session)
                elif selection == "Update Event":
                    handle_update_event(session)
                elif selection == "Delete Event":
                    handle_delete_event(session)
                elif selection == "Assign Support to Event":
                    handle_assign_support(session)
                elif selection == "View Events Assigned to Me":
                    handle_filter_events_assigned_to_me(session)
                elif selection == "Filter Unassigned Events":
                    handle_filter_events_unassigned(session)
                elif selection == "Back to Main Menu":
                    break
                else:
                    print("Invalid selection. Please try again.\n")
            else:
                print("Invalid selection. Please try again.\n")
    else:
        print("Permission denied.\n")


def build_manage_events_options(session):
    options = {"1": "View Events"}
    option_number = 2

    if has_permission(session["role_id"], "event", "create"):
        options[str(option_number)] = "Create Event"
        option_number += 1

    if has_permission(session["role_id"], "event", "update"):
        options[str(option_number)] = "Update Event"
        option_number += 1

    if has_permission(session["role_id"], "event", "delete"):
        options[str(option_number)] = "Delete Event"
        option_number += 1

    if has_permission(session["role_id"], "event", "update"):
        options[str(option_number)] = "Assign Support to Event"
        option_number += 1

    if session["role"] == "Support":
        options[str(option_number)] = "View Events Assigned to Me"
    elif has_permission(session["role_id"], "event", "read"):
        options[str(option_number)] = "Filter Unassigned Events"
    option_number += 1

    options[str(option_number)] = "Back to Main Menu"

    return options


def handle_view_events(session):
    if session["role"] == "Support":
        events = filter_events_by_support_user(session["user_id"])
    else:
        events = get_all_events(session["user_id"])
    display_events(
        events,
        title=(
            "Events Assigned to You" if session["role"] == "Support" else "Events List"
        ),
    )


def handle_create_event(session):
    print("\nCreate Event:")
    contract_id_input = prompt_input("Enter contract ID: ")
    event_date_start = prompt_input("Enter event start date (YYYY-MM-DD): ")
    event_date_end = prompt_input("Enter event end date (YYYY-MM-DD): ")
    location = prompt_input("Enter event location: ")
    attendees_input = prompt_input("Enter number of attendees: ")
    notes = prompt_input("Enter event notes: ")
    try:
        contract_id = int(contract_id_input)
        attendees = int(attendees_input)
        result = create_event(
            user_id=session["user_id"],
            contract_id=contract_id,
            event_date_start=event_date_start,
            event_date_end=event_date_end,
            location=location,
            attendees=attendees,
            notes=notes,
        )
        print(f"{result}\n")
    except ValueError:
        print("Invalid input. Please enter valid numbers for IDs and attendees.\n")


def handle_update_event(session):
    print("\nUpdate Event:")
    event_id_input = prompt_input("Enter event ID to update: ")
    event_date_start = prompt_input("Enter new event start date (YYYY-MM-DD): ")
    event_date_end = prompt_input("Enter new event end date (YYYY-MM-DD): ")
    location = prompt_input("Enter new event location: ")
    attendees_input = prompt_input("Enter new number of attendees: ")
    notes = prompt_input("Enter new event notes: ")
    try:
        event_id = int(event_id_input)
        attendees = int(attendees_input)
        result = update_event(
            user_id=session["user_id"],
            event_id=event_id,
            event_date_start=event_date_start,
            event_date_end=event_date_end,
            location=location,
            attendees=attendees,
            notes=notes,
        )
        print(f"{result}\n")
    except ValueError:
        print("Invalid input. Please enter valid numbers for IDs and attendees.\n")


def handle_delete_event(session):
    print("\nDelete Event:")
    event_id_input = prompt_input("Enter event ID to delete: ")
    confirm = confirm_action("delete this event")
    if confirm:
        try:
            event_id = int(event_id_input)
            result = delete_event(user_id=session["user_id"], event_id=event_id)
            print(f"{result}\n")
        except ValueError:
            print("Invalid event ID.\n")
    else:
        print("Deletion cancelled.\n")


def handle_assign_support(session):
    print("\nAssign Support to Event:")
    event_id_input = prompt_input("Enter event ID: ")
    support_user_id_input = prompt_input("Enter support user ID to assign: ")
    try:
        event_id = int(event_id_input)
        support_user_id = int(support_user_id_input)
        result = assign_support_to_event(
            user_id=session["user_id"],
            event_id=event_id,
            support_user_id=support_user_id,
        )
        print(f"{result}\n")
    except ValueError:
        print("Invalid input. Please enter valid numbers for IDs.\n")


def handle_filter_events_unassigned(session):
    events = filter_events_unassigned()
    display_events(events, title="Unassigned Events")


def handle_filter_events_assigned_to_me(session):
    events = filter_events_by_support_user(session["user_id"])
    display_events(events, title="Events Assigned to You")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logging.error(f"An error occurred: {e}")
        print("An unexpected error occurred. Please try again.")
