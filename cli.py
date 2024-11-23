"""
CLI application for Epic Events CRM.

This module provides a command-line interface for the Epic Events CRM application.
Users can authenticate and perform various operations based on their roles and permissions.
"""

import sys
import getpass
import logging
import os
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
)
import sentry_sdk
from configs import sentry_setup
from models import User, Role, Database
from tabulate import tabulate

logging.basicConfig(
    filename="cli.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__),))
DATABASE_FOLDER = os.path.join(BASE_DIR, 'database')
DATABASE_URL = os.path.join(DATABASE_FOLDER, "app.db")

def main():
    """Main entry point for the CLI application.

    Initiates the login process.
    """
    # Check if the database exists
    if not os.path.exists(DATABASE_URL):
        print("Database not found. Please initialize the database by running 'python database.py' before proceeding.")
        sys.exit(1)

    session = {}
    print("Welcome to Epic Events CRM")
    print("--------------------------")
    while True:
        username = input("Username: ")
        password = getpass.getpass("Password: ")
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
        display_main_menu(session)
        choice = input("Select an option: ").strip()
        if choice == '1':
            handle_view_profile(session)
        elif choice == '2':
            handle_update_profile(session)
        elif choice == '3':
            if has_any_user_management_permission(session):
                manage_users(session)
            else:
                print("Permission denied.\n")
        elif choice == '4':
            if has_permission(session["role_id"], "client", "read"):
                manage_clients(session)
            else:
                print("Permission denied.\n")
        elif choice == '5':
            if has_permission(session["role_id"], "contract", "read"):
                manage_contracts(session)
            else:
                print("Permission denied.\n")
        elif choice == '6':
            if has_permission(session["role_id"], "event", "read"):
                manage_events(session)
            else:
                print("Permission denied.\n")
        elif choice == '7':
            print("Logging out...")
            break
        else:
            print("Invalid selection. Please try again.\n")


def display_main_menu(session):
    print("\nMain Menu:")
    print("1. View Profile")
    print("2. Update Profile")
    if has_any_user_management_permission(session):
        print("3. Manage Users")
    else:
        print("3. (No access)")
    if has_permission(session["role_id"], "client", "read"):
        print("4. Manage Clients")
    else:
        print("4. (No access)")
    if has_permission(session["role_id"], "contract", "read"):
        print("5. Manage Contracts")
    else:
        print("5. (No access)")
    if has_permission(session["role_id"], "event", "read"):
        print("6. Manage Events")
    else:
        print("6. (No access)")
    print("7. Logout")


def has_any_user_management_permission(session):
    return (
        has_permission(session["role_id"], "user", "create") or
        has_permission(session["role_id"], "user", "update") or
        has_permission(session["role_id"], "user", "delete")
    )


def handle_view_profile(session):
    # All users can view their own profile
    user_id = session["user_id"]
    user = User.get_by_id(user_id)
    if user:
        print(f"\nUser Profile:")
        print(f"  Username: {user.username}")
        print(f"  Email: {user.email}")
        print(f"  Role: {session['role']}\n")
    else:
        print("Error fetching user profile.\n")


def handle_update_profile(session):
    # All users can update their own profile
    print("\nUpdate Profile:")
    new_email = input("Enter new email address: ").strip()
    user_id = session["user_id"]
    user = User.get_by_id(user_id)
    if user:
        user.email = new_email
        if user.update():
            print("Profile updated successfully.\n")
        else:
            print("Failed to update profile.\n")
    else:
        print("User not found.\n")


def manage_users(session):
    if has_any_user_management_permission(session):
        while True:
            print("\nManage Users:")
            print("1. Create User")
            print("2. Update User")
            print("3. Delete User")
            print("4. Back to Main Menu")
            choice = input("Select an option: ").strip()
            if choice == '1':
                handle_create_user(session)
            elif choice == '2':
                handle_update_user(session)
            elif choice == '3':
                handle_delete_user(session)
            elif choice == '4':
                break
            else:
                print("Invalid selection. Please try again.\n")
    else:
        print("Permission denied.\n")


def handle_create_user(session):
    if has_permission(session["role_id"], "user", "create"):
        print("\nCreate User:")
        username = input("Enter username: ").strip()
        email = input("Enter email: ").strip()
        password = getpass.getpass("Enter password: ")
        confirm_password = getpass.getpass("Confirm password: ")
        if password != confirm_password:
            print("Passwords do not match.\n")
            return
        role_id = input("Enter role ID (e.g., 1 for Management, 2 for Sales, 3 for Support): ").strip()
        try:
            role_id = int(role_id)
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
    else:
        print("Permission denied.\n")


def handle_update_user(session):
    if has_permission(session["role_id"], "user", "update"):
        print("\nUpdate User:")
        user_id_input = input("Enter user ID to update: ").strip()
        try:
            user_id = int(user_id_input)
            username = input("Enter new username: ").strip()
            email = input("Enter new email: ").strip()
            role_id_input = input("Enter new role ID (e.g., 1 for Management, 2 for Sales, 3 for Support): ").strip()
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
    else:
        print("Permission denied.\n")


def handle_delete_user(session):
    if has_permission(session["role_id"], "user", "delete"):
        print("\nDelete User:")
        user_id_input = input("Enter user ID to delete: ").strip()
        confirm = input("Are you sure you want to delete this user? (yes/no): ").strip().lower()
        if confirm == 'yes':
            try:
                user_id = int(user_id_input)
                result = delete_user(
                    admin_user_id=session["user_id"], user_id=user_id
                )
                print(f"{result}\n")
            except ValueError:
                print("Invalid user ID.\n")
        else:
            print("Deletion cancelled.\n")
    else:
        print("Permission denied.\n")


def manage_clients(session):
    if has_permission(session["role_id"], "client", "read"):
        while True:
            print("\nManage Clients:")
            print("1. View Clients")
            if has_permission(session["role_id"], "client", "create"):
                print("2. Create Client")
            else:
                print("2. (No access)")
            if has_permission(session["role_id"], "client", "update"):
                print("3. Update Client")
            else:
                print("3. (No access)")
            if has_permission(session["role_id"], "client", "delete"):
                print("4. Delete Client")
            else:
                print("4. (No access)")
            print("5. Back to Main Menu")
            choice = input("Select an option: ").strip()
            if choice == '1':
                handle_view_clients(session)
            elif choice == '2':
                if has_permission(session["role_id"], "client", "create"):
                    handle_create_client(session)
                else:
                    print("Permission denied.\n")
            elif choice == '3':
                if has_permission(session["role_id"], "client", "update"):
                    handle_update_client(session)
                else:
                    print("Permission denied.\n")
            elif choice == '4':
                if has_permission(session["role_id"], "client", "delete"):
                    handle_delete_client(session)
                else:
                    print("Permission denied.\n")
            elif choice == '5':
                break
            else:
                print("Invalid selection. Please try again.\n")
    else:
        print("Permission denied.\n")


def handle_view_clients(session):
    clients = get_all_clients()
    if not clients:
        print("No clients found.\n")
        return
    headers = ["ID", "First Name", "Last Name", "Email", "Phone", "Company Name", "Last Contact", "Sales Contact ID", "Created At", "Updated At"]
    table = []
    for client in clients:
        table.append([
            client['id'],
            client['first_name'],
            client['last_name'],
            client['email'],
            client['phone'],
            client['company_name'],
            client['last_contact'],
            client['sales_contact_id'],
            client['created_at'],
            client['updated_at']
        ])
    print("\nClients List:")
    print(tabulate(table, headers=headers, tablefmt="grid"))
    print("")


def handle_create_client(session):
    print("\nCreate Client:")
    first_name = input("Enter first name: ").strip()
    last_name = input("Enter last name: ").strip()
    email = input("Enter email: ").strip()
    phone = input("Enter phone number: ").strip()
    company_name = input("Enter company name: ").strip()
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
    client_id_input = input("Enter client ID to update: ").strip()
    try:
        client_id = int(client_id_input)
        first_name = input("Enter new first name: ").strip()
        last_name = input("Enter new last name: ").strip()
        email = input("Enter new email: ").strip()
        phone = input("Enter new phone number: ").strip()
        company_name = input("Enter new company name: ").strip()
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
    client_id_input = input("Enter client ID to delete: ").strip()
    confirm = input("Are you sure you want to delete this client? (yes/no): ").strip().lower()
    if confirm == 'yes':
        try:
            client_id = int(client_id_input)
            result = delete_client(
                user_id=session["user_id"], client_id=client_id
            )
            print(f"{result}\n")
        except ValueError:
            print("Invalid client ID.\n")
    else:
        print("Deletion cancelled.\n")


def manage_contracts(session):
    if has_permission(session["role_id"], "contract", "read"):
        while True:
            print("\nManage Contracts:")
            print("1. View Contracts")
            if has_permission(session["role_id"], "contract", "create"):
                print("2. Create Contract")
            else:
                print("2. (No access)")
            if has_permission(session["role_id"], "contract", "update"):
                print("3. Update Contract")
            else:
                print("3. (No access)")
            if has_permission(session["role_id"], "contract", "delete"):
                print("4. Delete Contract")
            else:
                print("4. (No access)")
            print("5. Filter Contracts by Status")
            print("6. Back to Main Menu")
            choice = input("Select an option: ").strip()
            if choice == '1':
                handle_view_contracts(session)
            elif choice == '2':
                if has_permission(session["role_id"], "contract", "create"):
                    handle_create_contract(session)
                else:
                    print("Permission denied.\n")
            elif choice == '3':
                if has_permission(session["role_id"], "contract", "update"):
                    handle_update_contract(session)
                else:
                    print("Permission denied.\n")
            elif choice == '4':
                if has_permission(session["role_id"], "contract", "delete"):
                    handle_delete_contract(session)
                else:
                    print("Permission denied.\n")
            elif choice == '5':
                handle_filter_contracts(session)
            elif choice == '6':
                break
            else:
                print("Invalid selection. Please try again.\n")
    else:
        print("Permission denied.\n")


def handle_view_contracts(session):
    contracts = get_all_contracts()
    if not contracts:
        print("No contracts found.\n")
        return
    headers = ["ID", "Client ID", "Sales Contact ID", "Total Amount", "Amount Remaining", "Status", "Created At", "Updated At"]
    table = []
    for contract in contracts:
        table.append([
            contract['id'],
            contract['client_id'],
            contract['sales_contact_id'],
            contract['total_amount'],
            contract['amount_remaining'],
            contract['status'],
            contract['created_at'],
            contract['updated_at']
        ])
    print("\nContracts List:")
    print(tabulate(table, headers=headers, tablefmt="grid"))
    print("")


def handle_create_contract(session):
    print("\nCreate Contract:")
    client_id_input = input("Enter client ID: ").strip()
    total_amount_input = input("Enter total amount: ").strip()
    amount_remaining_input = input("Enter amount remaining: ").strip()
    status_input = input("Enter status ('Signed' or 'Not Signed'): ").strip()
    try:
        client_id = int(client_id_input)
        total_amount = float(total_amount_input)
        amount_remaining = float(amount_remaining_input)
        if status_input.lower() in ['signed', 'not signed']:
            status = status_input.capitalize()
            result = create_contract(
                user_id=session["user_id"],
                client_id=client_id,
                total_amount=total_amount,
                amount_remaining=amount_remaining,
                status=status,
            )
            print(f"{result}\n")
        else:
            print("Invalid status. Please enter 'Signed' or 'Not Signed'.\n")
    except ValueError:
        print("Invalid input. Please enter valid numbers for IDs and amounts.\n")


def handle_update_contract(session):
    print("\nUpdate Contract:")
    contract_id_input = input("Enter contract ID to update: ").strip()
    total_amount_input = input("Enter new total amount: ").strip()
    amount_remaining_input = input("Enter new amount remaining: ").strip()
    status_input = input("Enter new status ('Signed' or 'Not Signed'): ").strip()
    try:
        contract_id = int(contract_id_input)
        total_amount = float(total_amount_input)
        amount_remaining = float(amount_remaining_input)
        if status_input.lower() in ['signed', 'not signed']:
            status = status_input.capitalize()
            result = update_contract(
                user_id=session["user_id"],
                contract_id=contract_id,
                total_amount=total_amount,
                amount_remaining=amount_remaining,
                status=status,
            )
            print(f"{result}\n")
        else:
            print("Invalid status. Please enter 'Signed' or 'Not Signed'.\n")
    except ValueError:
        print("Invalid input. Please enter valid numbers for IDs and amounts.\n")


def handle_delete_contract(session):
    print("\nDelete Contract:")
    contract_id_input = input("Enter contract ID to delete: ").strip()
    confirm = input("Are you sure you want to delete this contract? (yes/no): ").strip().lower()
    if confirm == 'yes':
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
    status_input = input("Enter status to filter ('Signed' or 'Not Signed'): ").strip()
    if status_input.lower() in ['signed', 'not signed']:
        status = status_input.capitalize()
        contracts = filter_contracts_by_status(status)
        if not contracts:
            print(f"No contracts found with status '{status}'.\n")
            return
        headers = ["ID", "Client ID", "Sales Contact ID", "Total Amount", "Amount Remaining", "Status", "Created At", "Updated At"]
        table = []
        for contract in contracts:
            table.append([
                contract['id'],
                contract['client_id'],
                contract['sales_contact_id'],
                contract['total_amount'],
                contract['amount_remaining'],
                contract['status'],
                contract['created_at'],
                contract['updated_at']
            ])
        print(f"\nContracts with status '{status}':")
        print(tabulate(table, headers=headers, tablefmt="grid"))
        print("")
    else:
        print("Invalid status. Please enter 'Signed' or 'Not Signed'.\n")


def manage_events(session):
    if has_permission(session["role_id"], "event", "read"):
        while True:
            print("\nManage Events:")
            print("1. View Events")
            if has_permission(session["role_id"], "event", "create"):
                print("2. Create Event")
            else:
                print("2. (No access)")
            if has_permission(session["role_id"], "event", "update"):
                print("3. Update Event")
            else:
                print("3. (No access)")
            if has_permission(session["role_id"], "event", "delete"):
                print("4. Delete Event")
            else:
                print("4. (No access)")
            if has_permission(session["role_id"], "event", "update"):
                print("5. Assign Support to Event")
            else:
                print("5. (No access)")
            if session["role"] == "Support":
                print("6. View Events Assigned to Me")
            else:
                print("6. Filter Unassigned Events")
            print("7. Back to Main Menu")
            choice = input("Select an option: ").strip()
            if choice == '1':
                handle_view_events(session)
            elif choice == '2':
                if has_permission(session["role_id"], "event", "create"):
                    handle_create_event(session)
                else:
                    print("Permission denied.\n")
            elif choice == '3':
                if has_permission(session["role_id"], "event", "update"):
                    handle_update_event(session)
                else:
                    print("Permission denied.\n")
            elif choice == '4':
                if has_permission(session["role_id"], "event", "delete"):
                    handle_delete_event(session)
                else:
                    print("Permission denied.\n")
            elif choice == '5':
                if has_permission(session["role_id"], "event", "update"):
                    handle_assign_support(session)
                else:
                    print("Permission denied.\n")
            elif choice == '6':
                if session["role"] == "Support":
                    handle_filter_events_assigned_to_me(session)
                else:
                    handle_filter_events_unassigned(session)
            elif choice == '7':
                break
            else:
                print("Invalid selection. Please try again.\n")
    else:
        print("Permission denied.\n")


def handle_view_events(session):
    if session["role"] == "Support":
        events = filter_events_by_support_user(session["user_id"])
    else:
        events = get_all_events(session["user_id"])
    if not events:
        print("No events found.\n")
        return
    headers = ["ID", "Contract ID", "Support Contact ID", "Start Date", "End Date", "Location", "Attendees", "Notes", "Created At", "Updated At"]
    table = []
    for event in events:
        table.append([
            event['id'],
            event['contract_id'],
            event.get('support_contact_id', 'N/A'),
            event['event_date_start'],
            event['event_date_end'],
            event['location'],
            event['attendees'],
            event['notes'],
            event['created_at'],
            event['updated_at']
        ])
    print("\nEvents List:")
    print(tabulate(table, headers=headers, tablefmt="grid"))
    print("")


def handle_create_event(session):
    print("\nCreate Event:")
    contract_id_input = input("Enter contract ID: ").strip()
    event_date_start = input("Enter event start date (YYYY-MM-DD): ").strip()
    event_date_end = input("Enter event end date (YYYY-MM-DD): ").strip()
    location = input("Enter event location: ").strip()
    attendees_input = input("Enter number of attendees: ").strip()
    notes = input("Enter event notes: ").strip()
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
    event_id_input = input("Enter event ID to update: ").strip()
    event_date_start = input("Enter new event start date (YYYY-MM-DD): ").strip()
    event_date_end = input("Enter new event end date (YYYY-MM-DD): ").strip()
    location = input("Enter new event location: ").strip()
    attendees_input = input("Enter new number of attendees: ").strip()
    notes = input("Enter new event notes: ").strip()
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
    event_id_input = input("Enter event ID to delete: ").strip()
    confirm = input("Are you sure you want to delete this event? (yes/no): ").strip().lower()
    if confirm == 'yes':
        try:
            event_id = int(event_id_input)
            result = delete_event(
                user_id=session["user_id"], event_id=event_id
            )
            print(f"{result}\n")
        except ValueError:
            print("Invalid event ID.\n")
    else:
        print("Deletion cancelled.\n")


def handle_assign_support(session):
    print("\nAssign Support to Event:")
    event_id_input = input("Enter event ID: ").strip()
    support_user_id_input = input("Enter support user ID to assign: ").strip()
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
    if not events:
        print("No unassigned events found.\n")
        return
    headers = ["ID", "Contract ID", "Start Date", "End Date", "Location", "Attendees", "Notes", "Created At", "Updated At"]
    table = []
    for event in events:
        table.append([
            event['id'],
            event['contract_id'],
            event['event_date_start'],
            event['event_date_end'],
            event['location'],
            event['attendees'],
            event['notes'],
            event['created_at'],
            event['updated_at']
        ])
    print("\nUnassigned Events:")
    print(tabulate(table, headers=headers, tablefmt="grid"))
    print("")


def handle_filter_events_assigned_to_me(session):
    events = filter_events_by_support_user(session["user_id"])
    if not events:
        print("No events assigned to you.\n")
        return
    headers = ["ID", "Contract ID", "Start Date", "End Date", "Location", "Attendees", "Notes", "Created At", "Updated At"]
    table = []
    for event in events:
        table.append([
            event['id'],
            event['contract_id'],
            event['event_date_start'],
            event['event_date_end'],
            event['location'],
            event['attendees'],
            event['notes'],
            event['created_at'],
            event['updated_at']
        ])
    print("\nEvents Assigned to You:")
    print(tabulate(table, headers=headers, tablefmt="grid"))
    print("")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logging.error(f"An error occurred: {e}")
        print("An unexpected error occurred. Please try again.")
