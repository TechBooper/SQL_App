import logging
from .models import User, Client, Contract, Event, Permission, Role, Database
import sqlite3
import bcrypt

logging.basicConfig(
    filename="controllers.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def has_permission(username, entity, action, resource_owner_username=None):
    """Check if a user (identified by username) has permission to perform a certain action on an entity.

    Args:
        username (str): The username of the user performing the action.
        entity (str): The entity type (e.g., 'client', 'contract', 'event').
        action (str): The action to perform (e.g., 'create', 'update', 'delete').
        resource_owner_username (str, optional): The username of the resource owner, if applicable.

    Returns:
        bool: True if the user has permission, False otherwise.
    """
    user = User.get_by_username(username)
    if not user:
        logging.warning(f"User '{username}' not found.")
        return False

    role = Role.get_by_name(user.role_id)
    if not role:
        logging.error(f"Role '{user.role_id}' not found for user '{username}'.")
        return False

    # Debug logging
    logging.debug(f"""
        Permission check:
        Username: {username}
        Role: {role.name}
        Entity: {entity}
        Action: {action}
        Resource Owner: {resource_owner_username}
    """)

    # Management role should have all permissions
    if role.name == "Management":
        logging.debug(f"Management role detected for user {username}")
        return True

    permissions = Permission.get_permissions_by_role(user.role_id)
    has_perm = any(
        perm.entity == entity and perm.action == action for perm in permissions
    )

    if not has_perm:
        logging.warning(
            f"Permission denied for user '{username}' to {action} {entity}."
        )
        return False

    # Ownership checks for certain actions
    if action in ["update", "delete"] and entity in ["client", "contract", "event"]:
        if resource_owner_username is not None:
            return username == resource_owner_username
        return False  # No ownership provided

    # Commercial users can only create events for their own clients
    if action == "create" and entity == "event" and role.name == "Commercial":
        return resource_owner_username == username

    return True


def create_client(username, first_name, last_name, email, phone, company_name):
    """Create a new client."""
    if not has_permission(username, "client", "create"):
        return "Permission denied."

    if not all([first_name, last_name, email, phone, company_name]):
        return "All client fields are required."

    # Get the user ID from the username
    user = User.get_by_username(username)
    if not user:
        return "Invalid user."

    result = Client.create(
        first_name=first_name,
        last_name=last_name,
        email=email,
        phone=phone,
        company_name=company_name,
        sales_contact_id=username
    )

    if isinstance(result, str):
        return result
    elif result:
        logging.info(f"Client {first_name} {last_name} created by user '{username}'.")
        return f"Client {first_name} {last_name} created successfully."
    else:
        logging.error(
            f"Error creating client {first_name} {last_name} by user '{username}'."
        )
        return "An error occurred while creating the client."


def update_client(username, client_email, first_name=None, last_name=None, email=None, phone=None, company_name=None):
    """Update an existing client's information."""
    client = Client.get_by_email(client_email)
    if not client:
        logging.warning(f"Client with email '{client_email}' not found.")
        return "Client not found."

    if not has_permission(username, "client", "update", resource_owner_username=client.sales_contact_id):
        return "Permission denied."

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
        logging.info(f"Client '{client_email}' updated by user '{username}'.")
        return f"Client '{client_email}' updated successfully."
    elif isinstance(result, str):
        return result
    else:
        logging.error(f"Error updating client '{client_email}' by user '{username}'.")
        return "Error updating client."


def delete_client(username, client_email):
    """Delete a client."""
    client = Client.get_by_email(client_email)
    if not client:
        logging.warning(f"Client with email '{client_email}' not found.")
        return "Client not found."

    if not has_permission(username, "client", "delete", resource_owner_username=client.sales_contact_id):
        return "Permission denied."

    if client.delete():
        logging.info(f"Client '{client_email}' deleted by user '{username}'.")
        return f"Client '{client_email}' deleted successfully."
    else:
        logging.error(f"Error deleting client '{client_email}' by user '{username}'.")
        return "Error deleting client."


def create_contract(username, client_email, total_amount, amount_remaining, status):
    """Create a new contract for a client."""
    if not has_permission(username, "contract", "create"):
        return "Permission denied."

    client = Client.get_by_email(client_email)
    if not client:
        logging.warning(f"Client email '{client_email}' not found.")
        return "Client not found."

    try:
        result = Contract.create(
            client_id=client_email,
            sales_contact_id=username,
            total_amount=total_amount,
            amount_remaining=amount_remaining,
            status=status,
        )

        logging.debug(f"Result from Contract.create: {result}")

        if isinstance(result, str):
            return result
        elif result:
            logging.info(
                f"Contract created for client '{client_email}' by user '{username}'."
            )
            return "Contract created successfully."
        else:
            logging.error(
                f"Error creating contract for client '{client_email}' by user '{username}'."
            )
            return "Error creating contract."
        
    except sqlite3.IntegrityError as e:
        logging.error(f"IntegrityError message: {e}")
        error_msg = str(e)
        if "CHECK constraint failed: status" in error_msg:
            return "CHECK constraint failed: status IN ('Signed', 'Not Signed')"
        return "An error occurred while creating the contract."



def update_contract(username, contract_id, total_amount, amount_remaining, status):
    """Update an existing contract."""
    contract = Contract.get_by_id(contract_id)
    if not contract:
        logging.warning(f"Contract ID {contract_id} not found.")
        return "Contract not found."

    if not has_permission(username, "contract", "update", resource_owner_username=contract.sales_contact_id):
        return "Permission denied."

    contract.total_amount = total_amount
    contract.amount_remaining = amount_remaining
    contract.status = status

    result = contract.update()
    if result is True:
        logging.info(f"Contract ID {contract_id} updated by user '{username}'.")
        return f"Contract ID {contract_id} updated successfully."
    elif isinstance(result, str):
        return result
    else:
        logging.error(
            f"Error updating contract ID {contract_id} by user '{username}'."
        )
        return "Error updating contract."


def delete_contract(username, contract_id):
    """Delete a contract."""
    contract = Contract.get_by_id(contract_id)
    if not contract:
        logging.warning(f"Contract ID {contract_id} not found.")
        return "Contract not found."

    if not has_permission(username, "contract", "delete", resource_owner_username=contract.sales_contact_id):
        return "Permission denied."

    if contract.delete():
        logging.info(f"Contract ID {contract_id} deleted by user '{username}'.")
        return f"Contract ID {contract_id} deleted successfully."
    else:
        logging.error(
            f"Error deleting contract ID {contract_id} by user '{username}'."
        )
        return "Error deleting contract."


def create_event(username, contract_id, event_date_start, event_date_end, location, attendees, notes):
    """Create a new event associated with a contract."""
    contract = Contract.get_by_id(contract_id)
    if not contract or contract.status != "Signed":
        logging.warning(f"Contract ID {contract_id} is not valid or not signed.")
        return "Contract not valid or not signed."

    client = Client.get_by_email(contract.client_id)
    if not client:
        logging.warning(f"Client associated with contract ID {contract_id} not found.")
        return "Client not found."

    resource_owner_username = client.sales_contact_id

    if not has_permission(username, "event", "create", resource_owner_username=resource_owner_username):
        return "Permission denied."

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
        return result
    elif result:
        logging.info(
            f"Event created successfully for contract ID {contract_id} by user '{username}'."
        )
        return "Event created successfully."
    else:
        logging.error(
            f"Error creating event for contract ID {contract_id} by user '{username}'."
        )
        return "Error creating event."


def update_event(username, event_id, **kwargs):
    """Update an existing event."""
    # First check if event exists
    event = Event.get_by_id(event_id)
    if not event:
        logging.warning(f"Event ID {event_id} not found.")
        return "Event not found."

    # Get ownership chain with better error handling
    try:
        contract = Contract.get_by_id(event.contract_id)
        if not contract:
            logging.warning(f"Contract ID {event.contract_id} not found for event {event_id}.")
            return "Contract not found."

        client = Client.get_by_email(contract.client_id)
        if not client:
            logging.warning(f"Client email '{contract.client_id}' not found.")
            return "Client not found."

        resource_owner_username = client.sales_contact_id
        
        # Add debug logging
        logging.debug(f"""
            Update event check:
            Username: {username}
            Event ID: {event_id}
            Resource Owner: {resource_owner_username}
            Contract ID: {contract.id}
            Client Email: {client.email}
        """)

        # Check permissions
        if not has_permission(username, "event", "update", resource_owner_username=resource_owner_username):
            return "Permission denied."

        # Update event fields
        for key, value in kwargs.items():
            if hasattr(event, key):  # Only update valid attributes
                setattr(event, key, value)
            else:
                logging.warning(f"Invalid field '{key}' ignored for event update")

        result = event.update()
        if result is True:
            logging.info(f"Event ID {event_id} updated successfully by user '{username}'.")
            return f"Event ID {event_id} updated successfully."
        elif isinstance(result, str):
            logging.error(f"Update failed with message: {result}")
            return result
        else:
            logging.error(f"Error updating event ID {event_id} by user '{username}'.")
            return "Error updating event."

    except Exception as e:
        logging.error(f"Unexpected error updating event: {str(e)}")
        return "Error updating event."


def delete_event(username, event_id):
    """Delete an event."""
    event = Event.get_by_id(event_id)
    if not event:
        logging.warning(f"Event ID {event_id} not found.")
        return "Event not found."

    contract = Contract.get_by_id(event.contract_id)
    if not contract:
        logging.warning(f"Contract ID {event.contract_id} not found for event {event_id}.")
        return "Contract not found."

    client = Client.get_by_email(contract.client_id)
    if not client:
        logging.warning(f"Client '{contract.client_id}' not found.")
        return "Client not found."

    resource_owner_username = client.sales_contact_id

    if not has_permission(username, "event", "delete", resource_owner_username=resource_owner_username):
        return "Permission denied."

    if event.delete():
        logging.info(f"Event ID {event_id} deleted by user '{username}'.")
        return f"Event ID {event_id} deleted successfully."
    else:
        logging.error(f"Error deleting event ID {event_id} by user '{username}'.")
        return "Error deleting event."


def assign_support_to_event(username, event_id, support_user_username):
    """Assign a support user to an event."""
    # Only Management can assign support contacts
    if not has_permission(username, "event", "update"):
        return "Permission denied."

    event = Event.get_by_id(event_id)
    if not event:
        logging.warning(f"Event ID {event_id} not found.")
        return "Event not found."

    event.support_contact_id = support_user_username
    result = event.update()
    if result is True:
        logging.info(
            f"Support contact '{support_user_username}' assigned to event ID {event_id} by user '{username}'."
        )
        return f"Support contact assigned to event ID {event_id}."
    elif isinstance(result, str):
        return result
    else:
        logging.error(
            f"Error assigning support contact to event ID {event_id} by user '{username}'."
        )
        return "Error assigning support contact."


def create_user(admin_username, username, password, role_name, email):
    """Create a new user."""
    if not has_permission(admin_username, "user", "create"):
        return "Permission denied."

    result = User.create(username=username, password=password, role_id=role_name, email=email)

    if isinstance(result, str):
        return result
    elif result:
        logging.info(f"User '{username}' created by admin user '{admin_username}'.")
        return f"User '{username}' created successfully."
    else:
        logging.error(f"Error creating user '{username}' by admin user '{admin_username}'.")
        return "Error creating user."


def update_user(admin_username, username, new_username=None, password=None, role_name=None, email=None):
    """Update an existing user's information."""
    # First check if user exists
    user = User.get_by_username(username)
    if not user:
        logging.warning(
            f"User '{username}' not found for update by admin user '{admin_username}'."
        )
        return "User not found."

    # Then check permissions
    if not has_permission(admin_username, "user", "update"):
        return "Permission denied."

    if new_username:
        user.username = new_username
    if password:
        user.password_hash = bcrypt.hashpw(
            password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")
    if role_name:
        user.role_id = role_name
    if email:
        user.email = email

    result = user.update()
    if result is True:
        logging.info(f"User '{username}' updated by admin user '{admin_username}'.")
        return f"User '{username}' updated successfully."
    elif isinstance(result, str):
        return result
    else:
        logging.error(
            f"Error updating user '{username}' by admin user '{admin_username}'."
        )
        return "Error updating user."

def delete_user(admin_username, username):
    """Delete a user."""
    # First check if user exists
    user = User.get_by_username(username)
    if not user:
        logging.warning(
            f"User '{username}' not found for deletion by admin user '{admin_username}'."
        )
        return "User not found."

    # Then check permissions
    if not has_permission(admin_username, "user", "delete"):
        return "Permission denied."

    if user.delete():
        logging.info(f"User '{username}' deleted by admin user '{admin_username}'.")
        return f"User '{username}' deleted successfully."
    else:
        logging.error(
            f"Error deleting user '{username}' by admin user '{admin_username}'."
        )
        return "Error deleting user."


def get_all_clients():
    """Retrieve all clients."""
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
    """Retrieve all contracts along with client names."""
    contracts = []
    try:
        with Database.connect() as conn:
            cursor = conn.cursor()
            # Now clients are identified by email, and contracts have a client_id referencing that email.
            # But we do not have clients.id anymore, we must join on email.
            cursor.execute(
                """
                SELECT contracts.*, clients.first_name AS client_first_name, clients.last_name AS client_last_name
                FROM contracts
                JOIN clients ON contracts.client_id = clients.email
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


def get_all_events(username):
    """Retrieve all events accessible to the user."""
    events = []
    try:
        user = User.get_by_username(username)
        if not user:
            logging.warning(f"User '{username}' not found.")
            return []

        role = Role.get_by_name(user.role_id)
        if not role:
            logging.error(
                f"Role '{user.role_id}' not found for user '{username}'."
            )
            return []

        with Database.connect() as conn:
            cursor = conn.cursor()
            # Events join with contracts via contract_id, and contracts join with clients via email.
            # We'll select event + contract + client names
            if role.name == "Support":
                cursor.execute(
                    """
                    SELECT events.*, contracts.client_id, clients.first_name AS client_first_name, clients.last_name AS client_last_name
                    FROM events
                    JOIN contracts ON events.contract_id = contracts.id
                    JOIN clients ON contracts.client_id = clients.email
                    WHERE events.support_contact_id = ?
                    """,
                    (username,),
                )
            else:
                cursor.execute(
                    """
                    SELECT events.*, contracts.client_id, clients.first_name AS client_first_name, clients.last_name AS client_last_name
                    FROM events
                    JOIN contracts ON events.contract_id = contracts.id
                    JOIN clients ON contracts.client_id = clients.email
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


def get_all_users():
    """Retrieves all users from the database."""
    try:
        users = User.get_all_users()
        return users
    except Exception as e:
        logging.error(f"Error retrieving all users: {e}")
        return []


def filter_contracts_by_status(status):
    """Filter contracts by status."""
    contracts = []
    try:
        with Database.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT contracts.*, clients.first_name AS client_first_name, clients.last_name AS client_last_name
                FROM contracts
                JOIN clients ON contracts.client_id = clients.email
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
    """Retrieve events that have no support contact assigned."""
    events = []
    try:
        with Database.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT events.*, contracts.client_id, clients.first_name AS client_first_name, clients.last_name AS client_last_name
                FROM events
                JOIN contracts ON events.contract_id = contracts.id
                JOIN clients ON contracts.client_id = clients.email
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


def filter_events_by_support_user(support_user_username):
    """Retrieve events assigned to a specific support user."""
    events = []
    try:
        with Database.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT events.*, contracts.client_id, clients.first_name AS client_first_name, clients.last_name AS client_last_name
                FROM events
                JOIN contracts ON events.contract_id = contracts.id
                JOIN clients ON contracts.client_id = clients.email
                WHERE events.support_contact_id = ?
                """,
                (support_user_username,),
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
