# controllers.py
import logging
from models import User, Client, Contract, Event, Permission, Role, Database
from permissions import has_permission
import sqlite3

logging.basicConfig(
    filename='controllers.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Permission checking function (using the models)
def has_permission(user_id, entity, action, resource_owner_id=None):
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
    has_perm = any(perm.entity == entity and perm.action == action for perm in permissions)

    if not has_perm:
        logging.warning(f"Permission denied for user ID {user_id} to {action} {entity}.")
        return False

    # Ownership checks for certain actions
    if action in ['update', 'delete'] and entity in ['client', 'contract', 'event']:
        if role.name == 'Management':
            return True  # Management can modify any resource
        if resource_owner_id is not None:
            return user_id == resource_owner_id  # Only owner can modify
        return False  # No ownership ID provided

    # Sales can only create events for their own clients
    if action == 'create' and entity == 'event' and role.name == 'Sales':
        return resource_owner_id == user_id

    return True  # No additional ownership check needed


# CRUD operations

def create_client(user_id, first_name, last_name, email, phone, company_name):
    if not has_permission(user_id, 'client', 'create'):
        return "Permission denied."

    try:
        client = Client.create(
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            company_name=company_name,
            sales_contact_id=user_id
        )
        if client:
            logging.info(f"Client {first_name} {last_name} created by user ID {user_id}.")
            return f"Client {first_name} {last_name} created successfully."
        else:
            logging.error(f"Error creating client {first_name} {last_name} by user ID {user_id}.")
            return "Error creating client."
    except sqlite3.Error as e:
        logging.error(f"Database error creating client: {e}")
        return "Database error."


def update_contract(user_id, contract_id, total_amount, amount_remaining, status):
    contract = Contract.get_by_id(contract_id)
    if not contract:
        logging.warning(f"Contract ID {contract_id} not found.")
        return "Contract not found."

    if not has_permission(user_id, 'contract', 'update', resource_owner_id=contract.sales_contact_id):
        return "Permission denied."

    try:
        contract.total_amount = total_amount
        contract.amount_remaining = amount_remaining
        contract.status = status
        if contract.update():
            logging.info(f"Contract ID {contract_id} updated by user ID {user_id}.")
            return f"Contract ID {contract_id} updated successfully."
        else:
            logging.error(f"Error updating contract ID {contract_id} by user ID {user_id}.")
            return "Error updating contract."
    except sqlite3.Error as e:
        logging.error(f"Database error updating contract: {e}")
        return "Database error."


def update_event(user_id, event_id, support_contact_id, location, attendees, notes):
    event = Event.get_by_id(event_id)
    if not event:
        logging.warning(f"Event ID {event_id} not found.")
        return "Event not found."

    # Fetch the event's support_contact_id for ownership check
    resource_owner_id = event.support_contact_id

    if not has_permission(user_id, 'event', 'update', resource_owner_id=resource_owner_id):
        return "Permission denied."

    # Update event details
    event.support_contact_id = support_contact_id
    event.location = location
    event.attendees = attendees
    event.notes = notes

    if event.update():
        logging.info(f"Event ID {event_id} updated successfully by user ID {user_id}.")
        return f"Event ID {event_id} updated successfully."
    else:
        logging.error(f"Error updating event ID {event_id} by user ID {user_id}.")
        return "Error updating event."

# Additional CRUD operations as per your requirements

def create_event(user_id, contract_id, event_date_start, event_date_end, location, attendees, notes):
    # Check if the contract exists and is signed
    contract = Contract.get_by_id(contract_id)
    if not contract or contract.status != 'Signed':
        logging.warning(f"Contract ID {contract_id} is not valid or not signed.")
        return "Contract not valid or not signed."

    # Fetch the client to verify ownership
    client = Client.get_by_id(contract.client_id)
    if not client:
        logging.warning(f"Client associated with contract ID {contract_id} not found.")
        return "Client not found."

    resource_owner_id = client.sales_contact_id

    if not has_permission(user_id, 'event', 'create', resource_owner_id=resource_owner_id):
        return "Permission denied."

    # Create the event
    event = Event.create(
        contract_id=contract_id,
        support_contact_id=None,  # Initially, no support contact assigned
        event_date_start=event_date_start,
        event_date_end=event_date_end,
        location=location,
        attendees=attendees,
        notes=notes
    )

    if event:
        logging.info(f"Event created successfully for contract ID {contract_id} by user ID {user_id}.")
        return "Event created successfully."
    else:
        logging.error(f"Error creating event for contract ID {contract_id} by user ID {user_id}.")
        return "Error creating event."

def assign_support_to_event(user_id, event_id, support_user_id):
    # Only Management can assign support contacts
    if not has_permission(user_id, 'event', 'update'):
        return "Permission denied."

    event = Event.get_by_id(event_id)
    if not event:
        logging.warning(f"Event ID {event_id} not found.")
        return "Event not found."

    # Assign support contact
    event.support_contact_id = support_user_id

    if event.update():
        logging.info(f"Support contact ID {support_user_id} assigned to event ID {event_id} by user ID {user_id}.")
        return f"Support contact assigned to event ID {event_id}."
    else:
        logging.error(f"Error assigning support contact to event ID {event_id} by user ID {user_id}.")
        return "Error assigning support contact."

# Function to retrieve all clients (read-only access)
def get_all_clients():
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

# Function to retrieve all contracts (read-only access)
def get_all_contracts():
    contracts = []
    try:
        with Database.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT contracts.*, clients.first_name AS client_first_name, clients.last_name AS client_last_name
                FROM contracts
                JOIN clients ON contracts.client_id = clients.id
            """)
            rows = cursor.fetchall()
            contracts = [
                {**dict(row), 'client_name': f"{row['client_first_name']} {row['client_last_name']}"}
                for row in rows
            ]
        return contracts
    except sqlite3.Error as e:
        logging.error(f"Database error in get_all_contracts: {e}")
        return []


# Function to retrieve all events (read-only access)
def get_all_events(user_id):
    events = []
    try:
        user = User.get_by_id(user_id)
        if not user:
            logging.warning(f"User with ID {user_id} not found.")
            return []

        role = Role.get_by_id(user.role_id)
        if not role:
            logging.error(f"Role with ID {user.role_id} not found for user ID {user_id}.")
            return []

        with Database.connect() as conn:
            cursor = conn.cursor()
            if role.name == 'Support':
                cursor.execute("""
                    SELECT events.*, contracts.client_id, clients.first_name AS client_first_name, clients.last_name AS client_last_name
                    FROM events
                    JOIN contracts ON events.contract_id = contracts.id
                    JOIN clients ON contracts.client_id = clients.id
                    WHERE events.support_contact_id = ?
                """, (user_id,))
            else:
                cursor.execute("""
                    SELECT events.*, contracts.client_id, clients.first_name AS client_first_name, clients.last_name AS client_last_name
                    FROM events
                    JOIN contracts ON events.contract_id = contracts.id
                    JOIN clients ON contracts.client_id = clients.id
                """)

            rows = cursor.fetchall()
            events = [
                {**dict(row), 'client_name': f"{row['client_first_name']} {row['client_last_name']}"}
                for row in rows
            ]
        return events
    except sqlite3.Error as e:
        logging.error(f"Database error in get_all_events: {e}")
        return []

