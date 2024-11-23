"""Controllers module for Epic Events CRM.

This module handles business logic and CRUD operations for clients, contracts, events, and users.
It includes permission checks and interactions with the models.
"""

import logging
from models import User, Client, Contract, Event, Permission, Role, Database
import sqlite3
import bcrypt

logging.basicConfig(
    filename="controllers.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def has_permission(user_id, entity, action, resource_owner_id=None):
    """Check if a user has permission to perform a certain action on an entity.

    Args:
        user_id (int): The ID of the user performing the action.
        entity (str): The entity type (e.g., 'client', 'contract', 'event').
        action (str): The action to perform (e.g., 'create', 'update', 'delete').
        resource_owner_id (int, optional): The ID of the resource owner, if applicable.

    Returns:
        bool: True if the user has permission, False otherwise.
    """
    user = User.get_by_id(user_id)
    if not user:
        logging.warning(f"User with ID {user_id} not found.")
        return False

    # Get the role name
    role = Role.get_by_id(user.role_id)
    if not role:
        logging.error(f"Role with ID {user.role_id} not found for user ID {user_id}.")
        return False

    # Check if the user has the permission for the action
    permissions = Permission.get_permissions_by_role(user.role_id)
    has_perm = any(
        perm.entity == entity and perm.action == action for perm in permissions
    )

    if not has_perm:
        logging.warning(
            f"Permission denied for user ID {user_id} to {action} {entity}."
        )
        return False

    # Ownership checks for certain actions
    if action in ["update", "delete"] and entity in ["client", "contract", "event"]:
        if role.name == "Management":
            return True  # Management can modify any resource
        if resource_owner_id is not None:
            return user_id == resource_owner_id  # Only owner can modify
        return False  # No ownership ID provided

    # Commercial users can only create events for their own clients
    if action == "create" and entity == "event" and role.name == "Commercial":
        return resource_owner_id == user_id

    return True  # No additional ownership check needed


# CRUD operations

def create_client(user_id, first_name, last_name, email, phone, company_name):
    """Create a new client.

    Args:
        user_id (int): The ID of the user creating the client.
        first_name (str): Client's first name.
        last_name (str): Client's last name.
        email (str): Client's email address.
        phone (str): Client's phone number.
        company_name (str): Client's company name.

    Returns:
        str: Success message or error message.
    """
    if not has_permission(user_id, "client", "create"):
        return "Permission denied."

    if not all([first_name, last_name, email, phone, company_name]):
        return "All client fields are required."

    result = Client.create(
        first_name=first_name,
        last_name=last_name,
        email=email,
        phone=phone,
        company_name=company_name,
        sales_contact_id=user_id,
    )

    if isinstance(result, str):
        # An error message was returned from the model
        return result
    elif result:
        logging.info(f"Client {first_name} {last_name} created by user ID {user_id}.")
        return f"Client {first_name} {last_name} created successfully."
    else:
        logging.error(
            f"Error creating client {first_name} {last_name} by user ID {user_id}."
        )
        return "An error occurred while creating the client."


def update_client(
    user_id,
    client_id,
    first_name=None,
    last_name=None,
    email=None,
    phone=None,
    company_name=None,
):
    """Update an existing client's information.

    Args:
        user_id (int): The ID of the user updating the client.
        client_id (int): The ID of the client to update.
        first_name (str, optional): New first name.
        last_name (str, optional): New last name.
        email (str, optional): New email address.
        phone (str, optional): New phone number.
        company_name (str, optional): New company name.

    Returns:
        str: Success message or error message.
    """
    client = Client.get_by_id(client_id)
    if not client:
        logging.warning(f"Client ID {client_id} not found.")
        return "Client not found."

    if not has_permission(
        user_id, "client", "update", resource_owner_id=client.sales_contact_id
    ):
        return "Permission denied."

    try:
        if first_name:
            client.first_name = first_name
        if last_name:
            client.last_name = last_name
        if email:
            client.email = email
        if phone:
            client.phone = phone
        if company_name:
            client.company_name = company_name

        result = client.update()
        if result is True:
            logging.info(f"Client ID {client_id} updated by user ID {user_id}.")
            return f"Client ID {client_id} updated successfully."
        elif isinstance(result, str):
            # An error message was returned from the model
            return result
        else:
            logging.error(f"Error updating client ID {client_id} by user ID {user_id}.")
            return "Error updating client."
    except sqlite3.Error as e:
        logging.error(f"Database error updating client: {e}")
        return "Database error."


def delete_client(user_id, client_id):
    """Delete a client.

    Args:
        user_id (int): The ID of the user deleting the client.
        client_id (int): The ID of the client to delete.

    Returns:
        str: Success message or error message.
    """
    client = Client.get_by_id(client_id)
    if not client:
        logging.warning(f"Client ID {client_id} not found.")
        return "Client not found."

    if not has_permission(
        user_id, "client", "delete", resource_owner_id=client.sales_contact_id
    ):
        return "Permission denied."

    try:
        if client.delete():
            logging.info(f"Client ID {client_id} deleted by user ID {user_id}.")
            return f"Client ID {client_id} deleted successfully."
        else:
            logging.error(f"Error deleting client ID {client_id} by user ID {user_id}.")
            return "Error deleting client."
    except sqlite3.Error as e:
        logging.error(f"Database error deleting client: {e}")
        return "Database error."


def create_contract(user_id, client_id, total_amount, amount_remaining, status):
    """Create a new contract for a client.

    Args:
        user_id (int): The ID of the user creating the contract.
        client_id (int): The ID of the client.
        total_amount (float): Total contract amount.
        amount_remaining (float): Amount remaining.
        status (str): Contract status ('Signed' or 'Not Signed').

    Returns:
        str: Success message or error message.
    """
    if not has_permission(user_id, "contract", "create"):
        return "Permission denied."

    client = Client.get_by_id(client_id)
    if not client:
        logging.warning(f"Client ID {client_id} not found.")
        return "Client not found."

    try:
        result = Contract.create(
            client_id=client_id,
            sales_contact_id=user_id,
            total_amount=total_amount,
            amount_remaining=amount_remaining,
            status=status,
        )

        if isinstance(result, str):
            # An error message was returned from the model
            return result
        elif result:
            logging.info(
                f"Contract created for client ID {client_id} by user ID {user_id}."
            )
            return "Contract created successfully."
        else:
            logging.error(
                f"Error creating contract for client ID {client_id} by user ID {user_id}."
            )
            return "Error creating contract."
    except sqlite3.Error as e:
        logging.error(f"Database error creating contract: {e}")
        return "Database error."


def update_contract(user_id, contract_id, total_amount, amount_remaining, status):
    """Update an existing contract.

    Args:
        user_id (int): The ID of the user updating the contract.
        contract_id (int): The ID of the contract to update.
        total_amount (float): New total amount.
        amount_remaining (float): New amount remaining.
        status (str): New status ('Signed' or 'Not Signed').

    Returns:
        str: Success message or error message.
    """
    contract = Contract.get_by_id(contract_id)
    if not contract:
        logging.warning(f"Contract ID {contract_id} not found.")
        return "Contract not found."

    if not has_permission(
        user_id, "contract", "update", resource_owner_id=contract.sales_contact_id
    ):
        return "Permission denied."

    try:
        contract.total_amount = total_amount
        contract.amount_remaining = amount_remaining
        contract.status = status

        result = contract.update()
        if result is True:
            logging.info(f"Contract ID {contract_id} updated by user ID {user_id}.")
            return f"Contract ID {contract_id} updated successfully."
        elif isinstance(result, str):
            # An error message was returned from the model
            return result
        else:
            logging.error(
                f"Error updating contract ID {contract_id} by user ID {user_id}."
            )
            return "Error updating contract."
    except sqlite3.Error as e:
        logging.error(f"Database error updating contract: {e}")
        return "Database error."


def delete_contract(user_id, contract_id):
    """Delete a contract.

    Args:
        user_id (int): The ID of the user deleting the contract.
        contract_id (int): The ID of the contract to delete.

    Returns:
        str: Success message or error message.
    """
    contract = Contract.get_by_id(contract_id)
    if not contract:
        logging.warning(f"Contract ID {contract_id} not found.")
        return "Contract not found."

    if not has_permission(
        user_id, "contract", "delete", resource_owner_id=contract.sales_contact_id
    ):
        return "Permission denied."

    try:
        if contract.delete():
            logging.info(f"Contract ID {contract_id} deleted by user ID {user_id}.")
            return f"Contract ID {contract_id} deleted successfully."
        else:
            logging.error(
                f"Error deleting contract ID {contract_id} by user ID {user_id}."
            )
            return "Error deleting contract."
    except sqlite3.Error as e:
        logging.error(f"Database error deleting contract: {e}")
        return "Database error."


def create_event(
    user_id, contract_id, event_date_start, event_date_end, location, attendees, notes
):
    """Create a new event associated with a contract.

    Args:
        user_id (int): The ID of the user creating the event.
        contract_id (int): The ID of the associated contract.
        event_date_start (str): Event start date and time.
        event_date_end (str): Event end date and time.
        location (str): Event location.
        attendees (int): Number of attendees.
        notes (str): Additional notes.

    Returns:
        str: Success message or error message.
    """
    # Check if the contract exists and is signed
    contract = Contract.get_by_id(contract_id)
    if not contract or contract.status != "Signed":
        logging.warning(f"Contract ID {contract_id} is not valid or not signed.")
        return "Contract not valid or not signed."

    # Fetch the client to verify ownership
    client = Client.get_by_id(contract.client_id)
    if not client:
        logging.warning(f"Client associated with contract ID {contract_id} not found.")
        return "Client not found."

    resource_owner_id = client.sales_contact_id

    if not has_permission(
        user_id, "event", "create", resource_owner_id=resource_owner_id
    ):
        return "Permission denied."

    try:
        result = Event.create(
            contract_id=contract_id,
            support_contact_id=None,  # Initially, no support contact assigned
            event_date_start=event_date_start,
            event_date_end=event_date_end,
            location=location,
            attendees=attendees,
            notes=notes,
        )

        if isinstance(result, str):
            # An error message was returned from the model
            return result
        elif result:
            logging.info(
                f"Event created successfully for contract ID {contract_id} by user ID {user_id}."
            )
            return "Event created successfully."
        else:
            logging.error(
                f"Error creating event for contract ID {contract_id} by user ID {user_id}."
            )
            return "Error creating event."
    except sqlite3.Error as e:
        logging.error(f"Database error creating event: {e}")
        return "Database error."


def update_event(user_id, event_id, **kwargs):
    """Update an existing event.

    Args:
        user_id (int): The ID of the user updating the event.
        event_id (int): The ID of the event to update.
        **kwargs: Arbitrary keyword arguments representing fields to update.

    Returns:
        str: Success message or error message.
    """
    event = Event.get_by_id(event_id)
    if not event:
        logging.warning(f"Event ID {event_id} not found.")
        return "Event not found."

    # Determine the resource owner
    resource_owner_id = event.support_contact_id or event.contract.sales_contact_id

    if not has_permission(
        user_id, "event", "update", resource_owner_id=resource_owner_id
    ):
        return "Permission denied."

    try:
        for key, value in kwargs.items():
            setattr(event, key, value)

        result = event.update()
        if result is True:
            logging.info(f"Event ID {event_id} updated successfully by user ID {user_id}.")
            return f"Event ID {event_id} updated successfully."
        elif isinstance(result, str):
            # An error message was returned from the model
            return result
        else:
            logging.error(f"Error updating event ID {event_id} by user ID {user_id}.")
            return "Error updating event."
    except sqlite3.Error as e:
        logging.error(f"Database error updating event: {e}")
        return "Database error."


def delete_event(user_id, event_id):
    """Delete an event.

    Args:
        user_id (int): The ID of the user deleting the event.
        event_id (int): The ID of the event to delete.

    Returns:
        str: Success message or error message.
    """
    event = Event.get_by_id(event_id)
    if not event:
        logging.warning(f"Event ID {event_id} not found.")
        return "Event not found."

    # Determine the resource owner
    resource_owner_id = event.support_contact_id or event.contract.sales_contact_id

    if not has_permission(
        user_id, "event", "delete", resource_owner_id=resource_owner_id
    ):
        return "Permission denied."

    try:
        if event.delete():
            logging.info(f"Event ID {event_id} deleted by user ID {user_id}.")
            return f"Event ID {event_id} deleted successfully."
        else:
            logging.error(f"Error deleting event ID {event_id} by user ID {user_id}.")
            return "Error deleting event."
    except sqlite3.Error as e:
        logging.error(f"Database error deleting event: {e}")
        return "Database error."


def assign_support_to_event(user_id, event_id, support_user_id):
    """Assign a support user to an event.

    Args:
        user_id (int): The ID of the management user assigning support.
        event_id (int): The ID of the event.
        support_user_id (int): The ID of the support user to assign.

    Returns:
        str: Success message or error message.
    """
    # Only Management can assign support contacts
    if not has_permission(user_id, "event", "update"):
        return "Permission denied."

    event = Event.get_by_id(event_id)
    if not event:
        logging.warning(f"Event ID {event_id} not found.")
        return "Event not found."

    # Assign support contact
    event.support_contact_id = support_user_id

    result = event.update()
    if result is True:
        logging.info(
            f"Support contact ID {support_user_id} assigned to event ID {event_id} by user ID {user_id}."
        )
        return f"Support contact assigned to event ID {event_id}."
    elif isinstance(result, str):
        # An error message was returned from the model
        return result
    else:
        logging.error(
            f"Error assigning support contact to event ID {event_id} by user ID {user_id}."
        )
        return "Error assigning support contact."


def create_user(admin_user_id, username, password, role_id, email):
    """Create a new user.

    Args:
        admin_user_id (int): The ID of the admin user creating the new user.
        username (str): The username for the new user.
        password (str): The password for the new user.
        role_id (int): The role ID for the new user.
        email (str): The email address for the new user.

    Returns:
        str: Success message or error message.
    """
    if not has_permission(admin_user_id, "user", "create"):
        return "Permission denied."

    try:
        result = User.create(
            username=username, password=password, role_id=role_id, email=email
        )

        if isinstance(result, str):
            # An error message was returned from the model
            return result
        elif result:
            logging.info(f"User '{username}' created by admin user ID {admin_user_id}.")
            return f"User '{username}' created successfully."
        else:
            logging.error(
                f"Error creating user '{username}' by admin user ID {admin_user_id}."
            )
            return "Error creating user."
    except sqlite3.Error as e:
        logging.error(f"Database error creating user: {e}")
        return "Database error."


def update_user(admin_user_id, user_id, username=None, password=None, role_id=None, email=None):
    """Update an existing user's information.

    Args:
        admin_user_id (int): The ID of the admin user updating the user.
        user_id (int): The ID of the user to update.
        username (str, optional): New username.
        password (str, optional): New password.
        role_id (int, optional): New role ID.
        email (str, optional): New email address.

    Returns:
        str: Success message or error message.
    """
    if not has_permission(admin_user_id, "user", "update"):
        return "Permission denied."

    user = User.get_by_id(user_id)
    if not user:
        logging.warning(
            f"User ID {user_id} not found for update by admin user ID {admin_user_id}."
        )
        return "User not found."

    try:
        if username:
            user.username = username
        if password:
            # Hash the new password
            user.password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
        if role_id:
            user.role_id = role_id
        if email:
            user.email = email

        result = user.update()
        if result is True:
            logging.info(f"User ID {user_id} updated by admin user ID {admin_user_id}.")
            return f"User ID {user_id} updated successfully."
        elif isinstance(result, str):
            # An error message was returned from the model
            return result
        else:
            logging.error(
                f"Error updating user ID {user_id} by admin user ID {admin_user_id}."
            )
            return "Error updating user."
    except sqlite3.Error as e:
        logging.error(f"Database error updating user: {e}")
        return "Database error."


def delete_user(admin_user_id, user_id):
    """Delete a user.

    Args:
        admin_user_id (int): The ID of the admin user deleting the user.
        user_id (int): The ID of the user to delete.

    Returns:
        str: Success message or error message.
    """
    if not has_permission(admin_user_id, "user", "delete"):
        return "Permission denied."

    user = User.get_by_id(user_id)
    if not user:
        logging.warning(
            f"User ID {user_id} not found for deletion by admin user ID {admin_user_id}."
        )
        return "User not found."

    try:
        if user.delete():
            logging.info(f"User ID {user_id} deleted by admin user ID {admin_user_id}.")
            return f"User ID {user_id} deleted successfully."
        else:
            logging.error(
                f"Error deleting user ID {user_id} by admin user ID {admin_user_id}."
            )
            return "Error deleting user."
    except sqlite3.Error as e:
        logging.error(f"Database error deleting user: {e}")
        return "Database error."


def get_all_clients():
    """Retrieve all clients.

    Returns:
        list: A list of dictionaries representing clients.
    """
    clients = []
    try:
        with Database.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM clients")
            rows = cursor.fetchall()
            clients = [dict(row) for row in rows]
        return clients
    except sqlite3.Error as e:
        logging.error(f"Database error in get_all_clients: {e}")
        return []


def get_all_contracts():
    """Retrieve all contracts along with client names.

    Returns:
        list: A list of dictionaries representing contracts.
    """
    contracts = []
    try:
        with Database.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT contracts.*, clients.first_name AS client_first_name, clients.last_name AS client_last_name
                FROM contracts
                JOIN clients ON contracts.client_id = clients.id
            """
            )
            rows = cursor.fetchall()
            contracts = [
                {
                    **dict(row),
                    "client_name": f"{row['client_first_name']} {row['client_last_name']}",
                }
                for row in rows
            ]
        return contracts
    except sqlite3.Error as e:
        logging.error(f"Database error in get_all_contracts: {e}")
        return []


def get_all_events(user_id):
    """Retrieve all events accessible to the user.

    Args:
        user_id (int): The ID of the user requesting events.

    Returns:
        list: A list of dictionaries representing events.
    """
    events = []
    try:
        user = User.get_by_id(user_id)
        if not user:
            logging.warning(f"User with ID {user_id} not found.")
            return []

        role = Role.get_by_id(user.role_id)
        if not role:
            logging.error(
                f"Role with ID {user.role_id} not found for user ID {user_id}."
            )
            return []

        with Database.connect() as conn:
            cursor = conn.cursor()
            if role.name == "Support":
                cursor.execute(
                    """
                    SELECT events.*, contracts.client_id, clients.first_name AS client_first_name, clients.last_name AS client_last_name
                    FROM events
                    JOIN contracts ON events.contract_id = contracts.id
                    JOIN clients ON contracts.client_id = clients.id
                    WHERE events.support_contact_id = ?
                """,
                    (user_id,),
                )
            else:
                cursor.execute(
                    """
                    SELECT events.*, contracts.client_id, clients.first_name AS client_first_name, clients.last_name AS client_last_name
                    FROM events
                    JOIN contracts ON events.contract_id = contracts.id
                    JOIN clients ON contracts.client_id = clients.id
                """
                )

            rows = cursor.fetchall()
            events = [
                {
                    **dict(row),
                    "client_name": f"{row['client_first_name']} {row['client_last_name']}",
                }
                for row in rows
            ]
        return events
    except sqlite3.Error as e:
        logging.error(f"Database error in get_all_events: {e}")
        return []


def filter_contracts_by_status(status):
    """Filter contracts by status.

    Args:
        status (str): The status to filter by ('Signed' or 'Not Signed').

    Returns:
        list: A list of dictionaries representing contracts.
    """
    contracts = []
    try:
        with Database.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT contracts.*, clients.first_name AS client_first_name, clients.last_name AS client_last_name
                FROM contracts
                JOIN clients ON contracts.client_id = clients.id
                WHERE contracts.status = ?
            """,
                (status,),
            )
            rows = cursor.fetchall()
            contracts = [
                {
                    **dict(row),
                    "client_name": f"{row['client_first_name']} {row['client_last_name']}",
                }
                for row in rows
            ]
        return contracts
    except sqlite3.Error as e:
        logging.error(f"Database error in filter_contracts_by_status: {e}")
        return []


def filter_events_unassigned():
    """Retrieve events that have no support contact assigned.

    Returns:
        list: A list of dictionaries representing unassigned events.
    """
    events = []
    try:
        with Database.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT events.*, contracts.client_id, clients.first_name AS client_first_name, clients.last_name AS client_last_name
                FROM events
                JOIN contracts ON events.contract_id = contracts.id
                JOIN clients ON contracts.client_id = clients.id
                WHERE events.support_contact_id IS NULL
            """
            )
            rows = cursor.fetchall()
            events = [
                {
                    **dict(row),
                    "client_name": f"{row['client_first_name']} {row['client_last_name']}",
                }
                for row in rows
            ]
        return events
    except sqlite3.Error as e:
        logging.error(f"Database error in filter_events_unassigned: {e}")
        return []


def filter_events_by_support_user(support_user_id):
    """Retrieve events assigned to a specific support user.

    Args:
        support_user_id (int): The ID of the support user.

    Returns:
        list: A list of dictionaries representing events.
    """
    events = []
    try:
        with Database.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT events.*, contracts.client_id, clients.first_name AS client_first_name, clients.last_name AS client_last_name
                FROM events
                JOIN contracts ON events.contract_id = contracts.id
                JOIN clients ON contracts.client_id = clients.id
                WHERE events.support_contact_id = ?
            """,
                (support_user_id,),
            )
            rows = cursor.fetchall()
            events = [
                {
                    **dict(row),
                    "client_name": f"{row['client_first_name']} {row['client_last_name']}",
                }
                for row in rows
            ]
        return events
    except sqlite3.Error as e:
        logging.error(f"Database error in filter_events_by_support_user: {e}")
        return []
