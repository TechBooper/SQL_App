from models import Session, User, Client, Contract, Event, Role, Permission
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime

# Session to interact with the database
session = Session()

# Helper function to check if a user has permission for a given action
def has_permission(user_id, entity, action):
    try:
        # Get user's role
        user = session.query(User).filter_by(id=user_id).first()
        if not user:
            print(f"User with ID {user_id} not found.")
            return False

        # Check if the user's role has the required permission
        permission = session.query(Permission).filter_by(role_id=user.role_id, entity=entity, action=action).first()
        if permission:
            return True
        else:
            print(f"Permission denied for user ID {user_id} to {action} {entity}.")
            return False
    except SQLAlchemyError as e:
        print(f"Error checking permissions: {e}")
        return False

# Function to create a new client (for commercial users)
def create_client(user_id, first_name, last_name, email, phone, company_name):
    if not has_permission(user_id, 'client', 'create'):
        return

    try:
        new_client = Client(
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            company_name=company_name,
            date_created=datetime.now(),
            sales_contact_id=user_id,  # Assigning the client to the user who created it
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        session.add(new_client)
        session.commit()
        print(f"Client {first_name} {last_name} created successfully.")
    except SQLAlchemyError as e:
        session.rollback()
        print(f"Error creating client: {e}")

# Function to update a contract (for commercial or management users)
def update_contract(user_id, contract_id, total_amount, amount_remaining, status):
    if not has_permission(user_id, 'contract', 'update'):
        return

    try:
        contract = session.query(Contract).filter_by(id=contract_id).first()
        if contract:
            contract.total_amount = total_amount
            contract.amount_remaining = amount_remaining
            contract.status = status
            contract.updated_at = datetime.now()
            session.commit()
            print(f"Contract ID {contract_id} updated successfully.")
        else:
            print(f"Contract ID {contract_id} not found.")
    except SQLAlchemyError as e:
        session.rollback()
        print(f"Error updating contract: {e}")

# Function to update an event (for support or management users)
def update_event(user_id, event_id, support_contact_id, location, attendees, notes):
    if not has_permission(user_id, 'event', 'update'):
        return

    try:
        event = session.query(Event).filter_by(id=event_id).first()
        if event:
            event.support_contact_id = support_contact_id
            event.location = location
            event.attendees = attendees
            event.notes = notes
            event.updated_at = datetime.now()
            session.commit()
            print(f"Event ID {event_id} updated successfully.")
        else:
            print(f"Event ID {event_id} not found.")
    except SQLAlchemyError as e:
        session.rollback()
        print(f"Error updating event: {e}")
