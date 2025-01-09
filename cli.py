import sys
import re
import logging
import getpass
import os
import sentry_sdk

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from main.auth import authenticate, has_permission
from main.controllers import (
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
from main.models import User
from main.views import (
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

from main.configs import sentry_setup
from main.database import create_connection


logging.basicConfig(
    filename="cli.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__)))
DATABASE_FOLDER = os.path.join(BASE_DIR, "db_folder")
DATABASE_URL = os.path.join(DATABASE_FOLDER, "app.db")


def display_sub_menu(title, options):
    """
    Displays a sub-menu with a given title and a dictionary of options.

    Args:
        title (str): The title of the sub-menu.
        options (dict): Dictionary where keys are option numbers (as strings),
                        and values are the corresponding option labels.
    """
    print(f"\n{title}:")
    for key in sorted(options.keys(), key=int):
        print(f"{key}. {options[key]}")


def main():
    """
    Main entry point for the CLI application.

    1. Connects to the database.
    2. Displays a welcome message.
    3. Prompts the user to log in.
    4. Starts an interactive session if authentication is successful.
    """
    conn = create_connection()
    if conn is None:
        print("Database connection failed. Please ensure the database is initialized.")
        return 1

    session = {}
    display_welcome_message()
    while True:
        username, password = display_login_prompt()
        user_info = authenticate(username, password)
        if user_info:
            session["username"] = user_info["username"]
            session["role"] = user_info["role_id"]
            print(
                f"\nLogged in as {session['username']} with role {session['role']}.\n"
            )
            interactive_session(session)
            break
        else:
            print("Authentication failed. Please try again.\n")


def interactive_session(session):
    """
    Presents the main menu loop for a logged-in user.

    Args:
        session (dict): A dictionary containing the username and role of the user.
    """
    while True:
        options = build_main_menu_options(session)
        display_main_menu(options)
        choice = prompt_choice()

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
            print("Invalid selection. Please try again.\n")


def build_main_menu_options(session):
    """
    Builds and returns a dictionary of main menu options based on the user's role/permissions.

    Args:
        session (dict): A dictionary with keys 'username' and 'role'.

    Returns:
        dict: A dictionary of option numbers (as strings) to option labels.
    """
    options = {
        "1": "View Profile",
        "2": "Update Email",
    }
    option_number = 3

    if has_permission(
        session["role"], "user", "read"
    ) or has_any_user_management_permission(session):
        options[str(option_number)] = "Manage Users"
        option_number += 1

    if has_permission(session["role"], "client", "read"):
        options[str(option_number)] = "Manage Clients"
        option_number += 1

    if has_permission(session["role"], "contract", "read"):
        options[str(option_number)] = "Manage Contracts"
        option_number += 1

    if has_permission(session["role"], "event", "read"):
        options[str(option_number)] = "Manage Events"
        option_number += 1

    options[str(option_number)] = "Logout"
    return options


def handle_view_profile(session):
    """
    Fetches and displays the profile of the currently logged-in user.

    Args:
        session (dict): Contains the current user's details such as username.
    """
    user = User.get_by_username(session["username"])
    if user:
        display_profile(user)
    else:
        print("Error fetching user profile.\n")


def handle_update_email(session):
    """
    Prompts the user to update their email address, validates the format, and
    updates the user's record in the database.

    Args:
        session (dict): Contains the current user's details such as username.
    """
    print("\nUpdate Email:")
    email_pattern = r"^[^@]+@[^@]+\.[^@]+$"

    while True:
        new_email = prompt_input("Enter new email address: ")
        if re.match(email_pattern, new_email):
            user = User.get_by_username(session["username"])
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


def has_any_user_management_permission(session):
    """
    Checks if the current user (by role) has any of the create, update, or delete
    permissions for the 'user' resource.

    Args:
        session (dict): Contains the current user's details such as username and role.

    Returns:
        bool: True if the user has any user-management permission, False otherwise.
    """
    return (
        has_permission(session["role"], "user", "create")
        or has_permission(session["role"], "user", "update")
        or has_permission(session["role"], "user", "delete")
    )


def manage_users(session):
    """
    Entry point for the "Manage Users" sub-menu. Based on the user's choice, it
    calls the corresponding handler (view, create, update, delete).

    Args:
        session (dict): Contains the current user's details such as username and role.
    """
    if has_permission(
        session["role"], "user", "read"
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
    """
    Constructs and returns a dictionary of user-management sub-menu options
    based on the user's permissions.

    Args:
        session (dict): Contains the current user's details such as username and role.

    Returns:
        dict: A dictionary of option numbers (as strings) to option labels.
    """
    options = {}
    option_number = 1

    if has_permission(session["role"], "user", "read"):
        options[str(option_number)] = "View Users"
        option_number += 1

    if has_permission(session["role"], "user", "create"):
        options[str(option_number)] = "Create User"
        option_number += 1

    if has_permission(session["role"], "user", "update"):
        options[str(option_number)] = "Update User"
        option_number += 1

    if has_permission(session["role"], "user", "delete"):
        options[str(option_number)] = "Delete User"
        option_number += 1

    options[str(option_number)] = "Back to Main Menu"
    return options


def handle_view_users(session):
    """
    Fetches and displays all users from the system.

    Args:
        session (dict): Contains the current user's details such as username and role.
    """
    users = get_all_users()
    display_users(users)


def handle_create_user(session):
    """
    Prompts the user for new-user details, including username, email, password, and role,
    then calls the controller to create the user.

    Args:
        session (dict): Contains the current user's details such as username and role.
    """
    print("\nCreate User:")
    username = prompt_input("Enter username: ")
    email = prompt_input("Enter email: ")
    password = getpass.getpass("Enter password: ")
    confirm_password = getpass.getpass("Confirm password: ")
    if password != confirm_password:
        print("Passwords do not match.\n")
        return
    role_name = prompt_input(
        "Enter role name (e.g., 'Management', 'Commercial', 'Support'): "
    ).strip()
    result = create_user(
        admin_username=session["username"],
        username=username,
        password=password,
        role_name=role_name,
        email=email,
    )
    print(f"{result}\n")


def handle_update_user(session):
    """
    Prompts for details to update an existing user (username, email, password, role).
    Calls the controller to perform the update.

    Args:
        session (dict): Contains the current user's details such as username and role.
    """
    print("\nUpdate User:")
    old_username = prompt_input("Enter the username of the user to update: ")
    new_username = prompt_input("Enter new username: ")
    email = prompt_input("Enter new email: ")
    password = getpass.getpass("Enter new password (leave blank to keep current): ")
    confirm_password = None
    if password:
        confirm_password = getpass.getpass("Confirm new password: ")
        if password != confirm_password:
            print("Passwords do not match.\n")
            return
    role_name = prompt_input(
        "Enter new role name (Management, Commercial, Support): "
    ).strip()

    if not password:
        password = None

    result = update_user(
        admin_username=session["username"],
        username=old_username,
        new_username=new_username,
        password=password,
        role_name=role_name,
        email=email,
    )
    print(f"{result}\n")


def handle_delete_user(session):
    """
    Prompts for a username to delete, confirms the action, and calls the controller to delete the user.

    Args:
        session (dict): Contains the current user's details such as username and role.
    """
    print("\nDelete User:")
    del_username = prompt_input("Enter username of the user to delete: ")
    confirm = confirm_action("delete this user")
    if confirm:
        result = delete_user(admin_username=session["username"], username=del_username)
        print(f"{result}\n")
    else:
        print("Deletion cancelled.\n")


def manage_clients(session):
    """
    Entry point for the "Manage Clients" sub-menu. Based on the user's choice,
    calls the corresponding handler (view, create, update, delete).

    Args:
        session (dict): Contains the current user's details such as username and role.
    """
    if has_permission(session["role"], "client", "read"):
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
    """
    Constructs and returns a dictionary of client-management sub-menu options
    based on the user's permissions.

    Args:
        session (dict): Contains the current user's details such as username and role.

    Returns:
        dict: A dictionary of option numbers (as strings) to option labels.
    """
    options = {"1": "View Clients"}
    option_number = 2

    if has_permission(session["role"], "client", "create"):
        options[str(option_number)] = "Create Client"
        option_number += 1

    if has_permission(session["role"], "client", "update"):
        options[str(option_number)] = "Update Client"
        option_number += 1

    if has_permission(session["role"], "client", "delete"):
        options[str(option_number)] = "Delete Client"
        option_number += 1

    options[str(option_number)] = "Back to Main Menu"
    return options


def handle_view_clients(session):
    """
    Fetches and displays all clients.

    Args:
        session (dict): Contains the current user's details such as username and role.
    """
    clients = get_all_clients()
    display_clients(clients)


def handle_create_client(session):
    """
    Prompts for client details (first name, last name, email, phone, company name)
    and calls the controller to create a new client record.

    Args:
        session (dict): Contains the current user's details such as username and role.
    """
    print("\nCreate Client:")
    first_name = prompt_input("Enter first name: ")
    last_name = prompt_input("Enter last name: ")
    email = prompt_input("Enter email: ")
    phone = prompt_input("Enter phone number: ")
    company_name = prompt_input("Enter company name: ")
    result = create_client(
        username=session["username"],
        first_name=first_name,
        last_name=last_name,
        email=email,
        phone=phone,
        company_name=company_name,
    )
    print(f"{result}\n")


def handle_update_client(session):
    """
    Prompts for a client's email and new details, then updates the client's record
    via the corresponding controller function.

    Args:
        session (dict): Contains the current user's details such as username and role.
    """
    print("\nUpdate Client:")
    client_email = prompt_input("Enter client email to update: ")
    first_name = prompt_input("Enter new first name: ")
    last_name = prompt_input("Enter new last name: ")
    new_email = prompt_input("Enter new email: ")
    phone = prompt_input("Enter new phone number: ")
    company_name = prompt_input("Enter new company name: ")
    result = update_client(
        username=session["username"],
        client_email=client_email,
        first_name=first_name,
        last_name=last_name,
        email=new_email,
        phone=phone,
        company_name=company_name,
    )
    print(f"{result}\n")


def handle_delete_client(session):
    """
    Prompts for a client's email, confirms the action, and calls the controller
    to delete the client record.

    Args:
        session (dict): Contains the current user's details such as username and role.
    """
    print("\nDelete Client:")
    client_email = prompt_input("Enter client email to delete: ")
    confirm = confirm_action("delete this client")
    if confirm:
        result = delete_client(username=session["username"], client_email=client_email)
        print(f"{result}\n")
    else:
        print("Deletion cancelled.\n")


def manage_contracts(session):
    """
    Entry point for the "Manage Contracts" sub-menu. Based on the user's choice,
    calls the corresponding handler (view, create, update, delete, filter).

    Args:
        session (dict): Contains the current user's details such as username and role.
    """
    if has_permission(session["role"], "contract", "read"):
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
    """
    Constructs and returns a dictionary of contract-management sub-menu options
    based on the user's permissions.

    Args:
        session (dict): Contains the current user's details such as username and role.

    Returns:
        dict: A dictionary of option numbers (as strings) to option labels.
    """
    options = {"1": "View Contracts"}
    option_number = 2

    if has_permission(session["role"], "contract", "create"):
        options[str(option_number)] = "Create Contract"
        option_number += 1

    if has_permission(session["role"], "contract", "update"):
        options[str(option_number)] = "Update Contract"
        option_number += 1

    if has_permission(session["role"], "contract", "delete"):
        options[str(option_number)] = "Delete Contract"
        option_number += 1

    options[str(option_number)] = "Filter Contracts by Status"
    option_number += 1

    options[str(option_number)] = "Back to Main Menu"
    return options


def handle_view_contracts(session):
    """
    Fetches and displays all contracts.

    Args:
        session (dict): Contains the current user's details such as username and role.
    """
    contracts = get_all_contracts()
    display_contracts(contracts)


def handle_create_contract(session):
    """
    Prompts for contract creation details (client email, total amount, amount remaining, status)
    and calls the controller function to create a new contract.

    Args:
        session (dict): Contains the current user's details such as username and role.
    """
    print("\nCreate Contract:")
    client_email = prompt_input("Enter client email: ")
    total_amount_input = prompt_input("Enter total amount: ")
    amount_remaining_input = prompt_input("Enter amount remaining: ")

    print("Select contract status:")
    print("1. Signed")
    print("2. Not Signed")
    status_choice = prompt_input("Enter the number corresponding to the status: ")

    status_mapping = {"1": "Signed", "2": "Not Signed"}
    status = status_mapping.get(status_choice)

    try:
        total_amount = float(total_amount_input)
        amount_remaining = float(amount_remaining_input)

        if status:
            result = create_contract(
                username=session["username"],
                client_email=client_email,
                total_amount=total_amount,
                amount_remaining=amount_remaining,
                status=status,
            )
            print(f"{result}\n")
        else:
            print("Invalid selection. Please enter 1 or 2.\n")
    except ValueError:
        print("Invalid input. Please enter valid numbers.\n")


def handle_update_contract(session):
    """
    Prompts for a contract ID, new amounts, and a new status, then updates the contract
    via the controller function.

    Args:
        session (dict): Contains the current user's details such as username and role.
    """
    print("\nUpdate Contract:")
    contract_id_input = prompt_input("Enter contract ID to update: ")
    total_amount_input = prompt_input("Enter new total amount: ")
    amount_remaining_input = prompt_input("Enter new amount remaining: ")

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
                username=session["username"],
                contract_id=contract_id,
                total_amount=total_amount,
                amount_remaining=amount_remaining,
                status=status,
            )
            print(f"{result}\n")
        else:
            print("Invalid selection. Please enter 1 or 2.\n")
    except ValueError:
        print("Invalid input. Please enter valid numbers for ID and amounts.\n")


def handle_delete_contract(session):
    """
    Prompts for a contract ID, confirms the deletion, and calls the controller function
    to delete the contract.

    Args:
        session (dict): Contains the current user's details such as username and role.
    """
    print("\nDelete Contract:")
    contract_id_input = prompt_input("Enter contract ID to delete: ")
    confirm = confirm_action("delete this contract")
    if confirm:
        try:
            contract_id = int(contract_id_input)
            result = delete_contract(
                username=session["username"], contract_id=contract_id
            )
            print(f"{result}\n")
        except ValueError:
            print("Invalid contract ID.\n")
    else:
        print("Deletion cancelled.\n")


def handle_filter_contracts(session):
    """
    Prompts the user to select a contract status (Signed/Not Signed), then displays
    a list of contracts filtered by that status.

    Args:
        session (dict): Contains the current user's details such as username and role.
    """
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
    """
    Entry point for the "Manage Events" sub-menu. Based on the user's choice,
    calls the corresponding handler (view, create, update, delete, assign, filters).

    Args:
        session (dict): Contains the current user's details such as username and role.
    """
    if has_permission(session["role"], "event", "read"):
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
    """
    Constructs and returns a dictionary of event-management sub-menu options
    based on the user's permissions and role.

    Args:
        session (dict): Contains the current user's details such as username and role.

    Returns:
        dict: A dictionary of option numbers (as strings) to option labels.
    """
    options = {"1": "View Events"}
    option_number = 2

    if has_permission(session["role"], "event", "create"):
        options[str(option_number)] = "Create Event"
        option_number += 1

    if has_permission(session["role"], "event", "update"):
        options[str(option_number)] = "Update Event"
        option_number += 1

    if has_permission(session["role"], "event", "delete"):
        options[str(option_number)] = "Delete Event"
        option_number += 1

    if has_permission(session["role"], "event", "update"):
        options[str(option_number)] = "Assign Support to Event"
        option_number += 1

    if session["role"] == "Support":
        options[str(option_number)] = "View Events Assigned to Me"
    elif has_permission(session["role"], "event", "read"):
        options[str(option_number)] = "Filter Unassigned Events"
    option_number += 1

    options[str(option_number)] = "Back to Main Menu"
    return options


def handle_view_events(session):
    """
    Displays events. If the user role is "Support", filters events for the support user;
    otherwise, shows all events.

    Args:
        session (dict): Contains the current user's details such as username and role.
    """
    if session["role"] == "Support":
        events = filter_events_by_support_user(session["username"])
    else:
        events = get_all_events(session["username"])
    display_events(
        events,
        title=(
            "Events Assigned to You" if session["role"] == "Support" else "Events List"
        ),
    )


def handle_create_event(session):
    """
    Prompts for a contract ID and event details (start date, end date, location, attendees, notes),
    then calls the controller to create the event.

    Args:
        session (dict): Contains the current user's details such as username and role.
    """
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
            username=session["username"],
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
    """
    Prompts for an event ID and new details (date, location, attendees, notes) to update the event.

    Args:
        session (dict): Contains the current user's details such as username and role.
    """
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
            username=session["username"],
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
    """
    Prompts for an event ID, confirms the action, and calls the controller to delete the event.

    Args:
        session (dict): Contains the current user's details such as username and role.
    """
    print("\nDelete Event:")
    event_id_input = prompt_input("Enter event ID to delete: ")
    confirm = confirm_action("delete this event")
    if confirm:
        try:
            event_id = int(event_id_input)
            result = delete_event(username=session["username"], event_id=event_id)
            print(f"{result}\n")
        except ValueError:
            print("Invalid event ID.\n")
    else:
        print("Deletion cancelled.\n")


def handle_assign_support(session):
    """
    Prompts for an event ID and a support user's username, then calls the controller
    to assign that support user to the event.

    Args:
        session (dict): Contains the current user's details such as username and role.
    """
    print("\nAssign Support to Event:")
    event_id_input = prompt_input("Enter event ID: ")
    support_user_username = prompt_input("Enter support user username to assign: ")
    try:
        event_id = int(event_id_input)
        result = assign_support_to_event(
            username=session["username"],
            event_id=event_id,
            support_user_id=support_user_username,
        )
        print(f"{result}\n")
    except ValueError:
        print("Invalid event ID.\n")


def handle_filter_events_unassigned(session):
    """
    Fetches and displays all events that have no support user assigned.

    Args:
        session (dict): Contains the current user's details such as username and role.
    """
    events = filter_events_unassigned()
    display_events(events, title="Unassigned Events")


def handle_filter_events_assigned_to_me(session):
    """
    Fetches and displays all events that are assigned to the current support user.

    Args:
        session (dict): Contains the current user's details such as username and role.
    """
    events = filter_events_by_support_user(session["username"])
    display_events(events, title="Events Assigned to You")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logging.error(f"An error occurred: {e}")
        print("An unexpected error occurred. Please try again.")
