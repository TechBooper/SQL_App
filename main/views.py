import getpass
from tabulate import tabulate



def display_welcome_message():
    """Displays the welcome message to the user."""
    print("Welcome to Epic Events CRM")
    print("--------------------------")


def display_login_prompt():
    """Prompts the user for login credentials.

    Returns:
        tuple: A tuple containing the username and password.
    """
    username = input("Username: ")
    password = getpass.getpass("Password: ")
    return username, password


def display_main_menu(options):
    """Displays the main menu based on available options.

    Args:
        options (dict): Menu options to display.
    """
    print("\nMain Menu:")
    for key in sorted(options.keys(), key=int):
        print(f"{key}. {options[key]}")


def prompt_choice():
    """Prompts the user to make a menu selection.

    Returns:
        str: The user's menu choice.
    """
    return input("Select an option: ").strip()


def display_profile(user):
    """Displays the user's profile information.

    Args:
        user (User): The user object containing profile information.
    """
    # With the new schema, 'user' has: username, email, role_id
    print(f"\nUser Profile:")
    print(f"  Username: {user.username}")
    print(f"  Email: {user.email}")
    print(f"  Role: {user.role_id}\n")


def prompt_input(prompt_message):
    """Prompts the user for input.

    Args:
        prompt_message (str): The message to display to the user.

    Returns:
        str: The user's input.
    """
    return input(prompt_message).strip()


def confirm_action(action_description):
    """Asks the user to confirm an action.

    Args:
        action_description (str): Description of the action to confirm.

    Returns:
        bool: True if the user confirms, False otherwise.
    """
    confirm = (
        input(f"Are you sure you want to {action_description}? (yes/no): ")
        .strip()
        .lower()
    )
    return confirm == "yes"


def display_sub_menu(title, options):
    """Displays a sub-menu based on available options.

    Args:
        title (str): The title of the sub-menu.
        options (dict): Menu options to display.
    """
    print(f"\n{title}:")
    for key in sorted(options.keys(), key=int):
        print(f"{key}. {options[key]}")


def display_users(users, title="Users List"):
    """
    Display a list of users in a formatted table.

    Args:
        users (list): A list of User objects.
        title (str): A title for the display.
    """
    print(f"\n{title}:")
    if not users:
        print("No users found.\n")
        return
    headers = ["Username", "Email", "Role"]
    table = []
    for user in users:
        table.append([user.username, user.email, user.role_id])

    print(tabulate(table, headers=headers, tablefmt="grid"))
    print("")


def display_clients(clients):
    """Displays a list of clients in a formatted table.

    Args:
        clients (list): A list of client dictionaries.
    """
    if not clients:
        print("No clients found.\n")
        return
    # New schema for clients:
    # email (PK), first_name, last_name, phone, company_name, last_contact, sales_contact_id, created_at, updated_at
    headers = [
        "Email",
        "First Name",
        "Last Name",
        "Phone",
        "Company Name",
        "Last Contact",
        "Sales Contact Username",
        "Created At",
        "Updated At",
    ]
    table = []
    for client in clients:
        table.append(
            [
                client["email"],
                client["first_name"],
                client["last_name"],
                client["phone"],
                client["company_name"],
                client["last_contact"],
                client["sales_contact_id"],
                client["created_at"],
                client["updated_at"],
            ]
        )
    print("\nClients List:")
    print(tabulate(table, headers=headers, tablefmt="grid"))
    print("")


def display_contracts(contracts, title="Contracts List"):
    """Displays a list of contracts in a formatted table.

    Args:
        contracts (list): A list of contract dictionaries.
        title (str): The title to display above the table.
    """
    if not contracts:
        print("No contracts found.\n")
        return
    headers = [
        "ID",
        "Client Email",
        "Sales Contact Username",
        "Total Amount",
        "Amount Remaining",
        "Status",
        "Created At",
        "Updated At",
    ]
    table = []
    for contract in contracts:
        table.append(
            [
                contract["id"],
                contract["client_id"],
                contract["sales_contact_id"],
                contract["total_amount"],
                contract["amount_remaining"],
                contract["status"],
                contract["created_at"],
                contract["updated_at"],
            ]
        )
    print(f"\n{title}:")
    print(tabulate(table, headers=headers, tablefmt="grid"))
    print("")


def display_events(events, title="Events List"):
    """Displays a list of events in a formatted table.

    Args:
        events (list): A list of event dictionaries.
        title (str): The title to display above the table.
    """
    if not events:
        print("No events found.\n")
        return
    headers = [
        "ID",
        "Contract ID",
        "Support Contact Username",
        "Start Date/Time",
        "End Date/Time",
        "Location",
        "Attendees",
        "Notes",
        "Created At",
        "Updated At",
    ]
    table = []
    for event in events:
        table.append(
            [
                event["id"],
                event["contract_id"],
                event.get("support_contact_id", "N/A"),
                event["event_date_start"],
                event["event_date_end"],
                event["location"],
                event["attendees"],
                event["notes"],
                event["created_at"],
                event["updated_at"],
            ]
        )
    print(f"\n{title}:")
    print(tabulate(table, headers=headers, tablefmt="grid"))
    print("")
