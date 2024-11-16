"""Models module for Epic Events CRM.

This module defines the data models for the application, including User, Role,
Client, Contract, Event, and Permission. Each model includes methods for CRUD
operations and interactions with the SQLite database.
"""

import sqlite3
import logging
from datetime import datetime
import bcrypt
import base64

logging.basicConfig(
    filename="models.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


class Database:
    """Database connection handler for the application."""

    DB_NAME = "app.db"

    @staticmethod
    def connect():
        """Establish a connection to the SQLite database.

        Returns:
            sqlite3.Connection: A connection object to the database.
        """
        conn = sqlite3.connect(Database.DB_NAME)
        conn.row_factory = sqlite3.Row
        return conn


class User:
    """Represents a user in the application."""

    def __init__(self, **kwargs):
        """Initialize a User instance.

        Args:
            **kwargs: Arbitrary keyword arguments for user attributes.
        """
        self.id = kwargs.get("id")
        self.username = kwargs.get("username")
        self.password_hash = kwargs.get("password_hash")
        self.role_id = kwargs.get("role_id")
        self.email = kwargs.get("email")
        self.bio = kwargs.get("bio", None)
        self.created_at = kwargs.get("created_at", None)
        self.updated_at = kwargs.get("updated_at", None)
        logging.debug(f"Created User instance: {self.__dict__}")

    @staticmethod
    def create(username, password, role_id, email):
        """Create a new user in the database.

        Args:
            username (str): The username of the new user.
            password (str): The plaintext password for the user.
            role_id (int): The role ID to assign to the user.
            email (str): The email address of the user.

        Returns:
            User or str: The created User object or an error message.
        """
        try:
            # Hash the password using bcrypt
            password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
            # Encode the password hash to a base64 string
            password_hash_encoded = base64.b64encode(password_hash).decode("ascii")
            with Database.connect() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO users (username, password_hash, role_id, email) VALUES (?, ?, ?, ?)",
                    (username, password_hash_encoded, role_id, email),
                )
                conn.commit()
                user_id = cursor.lastrowid
                logging.info(f"User {username} created with ID {user_id}.")
                return User.get_by_id(user_id)
        except sqlite3.IntegrityError as e:
            logging.error(f"Integrity error in User.create: {e}")
            if 'username' in str(e):
                return "A user with this username already exists."
            elif 'email' in str(e):
                return "A user with this email already exists."
            else:
                return "An error occurred while creating the user."
        except sqlite3.Error as e:
            logging.error(f"Database error in User.create: {e}")
            return "An error occurred while creating the user."

    @staticmethod
    def get_by_username(username):
        """Retrieve a user by username.

        Args:
            username (str): The username to search for.

        Returns:
            User or None: The User object if found, else None.
        """
        try:
            conn = Database.connect()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            user_row = cursor.fetchone()
            if user_row:
                user_data = dict(user_row)  # Convert Row to dict
                # Decode the password hash from base64
                password_hash_encoded = user_data["password_hash"]
                user_data["password_hash"] = base64.b64decode(
                    password_hash_encoded.encode("ascii")
                )
                logging.debug(f"user_data in get_by_username: {user_data}")
                return User(**user_data)
            return None
        except sqlite3.Error as e:
            logging.error(f"Database error in User.get_by_username: {e}")
            return None
        finally:
            conn.close()

    @staticmethod
    def get_by_id(user_id):
        """Retrieve a user by ID.

        Args:
            user_id (int): The ID of the user.

        Returns:
            User or None: The User object if found, else None.
        """
        try:
            conn = Database.connect()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            user_row = cursor.fetchone()
            if user_row:
                user_data = dict(user_row)  # Convert Row to dict
                # Decode the password hash from base64
                password_hash_encoded = user_data["password_hash"]
                user_data["password_hash"] = base64.b64decode(
                    password_hash_encoded.encode("ascii")
                )
                logging.debug(f"user_data in get_by_id: {user_data}")
                return User(**user_data)
            return None
        except sqlite3.Error as e:
            logging.error(f"Database error in User.get_by_id: {e}")
            return None
        finally:
            conn.close()

    def update(self, password=None):
        """Update the user's information in the database.

        Args:
            password (str, optional): New plaintext password. Defaults to None.

        Returns:
            bool or str: True if successful, False or error message otherwise.
        """
        try:
            with Database.connect() as conn:
                cursor = conn.cursor()
                if password:
                    # Hash the new password and encode it
                    password_hash = bcrypt.hashpw(
                        password.encode("utf-8"), bcrypt.gensalt()
                    )
                    password_hash_encoded = base64.b64encode(password_hash).decode(
                        "ascii"
                    )
                else:
                    # Keep the existing password hash (encode it)
                    password_hash_encoded = base64.b64encode(self.password_hash).decode(
                        "ascii"
                    )

                cursor.execute(
                    "UPDATE users SET username = ?, password_hash = ?, role_id = ?, email = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (
                        self.username,
                        password_hash_encoded,
                        self.role_id,
                        self.email,
                        self.id,
                    ),
                )
                conn.commit()
                logging.info(f"User {self.username} with ID {self.id} updated.")
                return True
        except sqlite3.IntegrityError as e:
            logging.error(f"Integrity error in User.update: {e}")
            if 'username' in str(e):
                return "A user with this username already exists."
            elif 'email' in str(e):
                return "A user with this email already exists."
            else:
                return "An error occurred while updating the user."
        except sqlite3.Error as e:
            logging.error(f"Database error in User.update: {e}")
            return False

    def delete(self):
        """Delete the user from the database.

        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            with Database.connect() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM users WHERE id = ?", (self.id,))
                conn.commit()
                logging.info(f"User {self.username} with ID {self.id} deleted.")
                return True
        except sqlite3.Error as e:
            logging.error(f"Database error in User.delete: {e}")
            return False

    def verify_password(self, password):
        """Verify the user's password.

        Args:
            password (str): The plaintext password to verify.

        Returns:
            bool: True if the password matches, False otherwise.
        """
        try:
            # Ensure the password is in bytes
            if isinstance(password, str):
                password_bytes = password.encode("utf-8")
            else:
                password_bytes = password  # Already bytes
            return bcrypt.checkpw(password_bytes, self.password_hash)
        except Exception as e:
            logging.error(f"Error verifying password for user {self.username}: {e}")
            return False


class Role:
    """Represents a role assigned to a user."""

    def __init__(self, **kwargs):
        """Initialize a Role instance.

        Args:
            **kwargs: Arbitrary keyword arguments for role attributes.
        """
        self.id = kwargs.get("id")
        self.name = kwargs.get("name")

    @staticmethod
    def get_by_id(role_id):
        """Retrieve a role by ID.

        Args:
            role_id (int): The ID of the role.

        Returns:
            Role or None: The Role object if found, else None.
        """
        try:
            conn = Database.connect()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM roles WHERE id = ?", (role_id,))
            role_row = cursor.fetchone()
            if role_row:
                role_data = dict(role_row)
                logging.debug(f"role_data in get_by_id: {role_data}")
                return Role(**role_data)
            return None
        except sqlite3.Error as e:
            logging.error(f"Database error in Role.get_by_id: {e}")
            return None
        finally:
            conn.close()

    @staticmethod
    def get_by_name(name):
        """Retrieve a role by name.

        Args:
            name (str): The name of the role.

        Returns:
            Role or None: The Role object if found, else None.
        """
        try:
            conn = Database.connect()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM roles WHERE name = ?", (name,))
            role_row = cursor.fetchone()
            if role_row:
                return Role(**role_row)
            return None
        except sqlite3.Error as e:
            logging.error(f"Database error in Role.get_by_name: {e}")
            return None
        finally:
            conn.close()


class Client:
    """Represents a client in the application."""

    def __init__(
        self,
        id,
        first_name,
        last_name,
        email,
        phone,
        company_name,
        date_created=None,
        last_contact=None,
        sales_contact_id=None,
        created_at=None,
        updated_at=None,
    ):
        """Initialize a Client instance.

        Args:
            id (int): The ID of the client.
            first_name (str): Client's first name.
            last_name (str): Client's last name.
            email (str): Client's email address.
            phone (str): Client's phone number.
            company_name (str): Client's company name.
            date_created (str, optional): Date the client was created.
            last_contact (str, optional): Date of last contact.
            sales_contact_id (int, optional): ID of the sales contact.
            created_at (str, optional): Timestamp of creation.
            updated_at (str, optional): Timestamp of last update.
        """
        self.id = id
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.phone = phone
        self.company_name = company_name
        self.date_created = date_created
        self.last_contact = last_contact
        self.sales_contact_id = sales_contact_id
        self.created_at = created_at
        self.updated_at = updated_at

    @staticmethod
    def create(first_name, last_name, email, phone, company_name, sales_contact_id):
        """Create a new client in the database.

        Args:
            first_name (str): Client's first name.
            last_name (str): Client's last name.
            email (str): Client's email address.
            phone (str): Client's phone number.
            company_name (str): Client's company name.
            sales_contact_id (int): ID of the sales contact.

        Returns:
            Client or str: The created Client object or an error message.
        """
        try:
            with Database.connect() as conn:
                cursor = conn.cursor()

                # Pre-insertion check for existing client with same unique fields
                cursor.execute(
                    """SELECT id FROM clients WHERE first_name = ? AND last_name = ? AND company_name = ?""",
                    (first_name, last_name, company_name),
                )
                existing_client = cursor.fetchone()
                if existing_client:
                    logging.warning(
                        f"Attempted to create duplicate client: {first_name} {last_name} at {company_name}."
                    )
                    return "A client with this first name, last name, and company already exists."

                cursor.execute(
                    """INSERT INTO clients (first_name, last_name, email, phone, company_name, sales_contact_id)
                    VALUES (?, ?, ?, ?, ?, ?)""",
                    (
                        first_name,
                        last_name,
                        email,
                        phone,
                        company_name,
                        sales_contact_id,
                    ),
                )
                conn.commit()
                client_id = cursor.lastrowid
                logging.info(f"Client {email} created with ID {client_id}.")
                return Client.get_by_id(client_id)
        except sqlite3.IntegrityError as e:
            logging.error(f"Integrity error in Client.create: {e}")
            if 'email' in str(e):
                return "A client with this email already exists."
            else:
                return "A client with this first name, last name, and company already exists."
        except sqlite3.Error as e:
            logging.error(f"Database error in Client.create: {e}")
            return "An error occurred while creating the client."

    @staticmethod
    def get_by_id(client_id):
        """Retrieve a client by ID.

        Args:
            client_id (int): The ID of the client.

        Returns:
            Client or None: The Client object if found, else None.
        """
        try:
            conn = Database.connect()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM clients WHERE id = ?", (client_id,))
            client_row = cursor.fetchone()
            if client_row:
                return Client(**client_row)
            return None
        except sqlite3.Error as e:
            logging.error(f"Database error in Client.get_by_id: {e}")
            return None
        finally:
            conn.close()

    def update(self):
        """Update the client's information in the database.

        Returns:
            bool or str: True if successful, False or error message otherwise.
        """
        try:
            with Database.connect() as conn:
                cursor = conn.cursor()

                # Pre-update check for existing client with same unique fields (excluding self)
                cursor.execute(
                    """SELECT id FROM clients WHERE first_name = ? AND last_name = ? AND company_name = ? AND id != ?""",
                    (self.first_name, self.last_name, self.company_name, self.id),
                )
                existing_client = cursor.fetchone()
                if existing_client:
                    logging.warning(
                        f"Attempted to update client to duplicate: {self.first_name} {self.last_name} at {self.company_name}."
                    )
                    return "Another client with this first name, last name, and company already exists."

                cursor.execute(
                    """UPDATE clients SET first_name = ?, last_name = ?, email = ?, phone = ?, company_name = ?, last_contact = CURRENT_DATE, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?""",
                    (
                        self.first_name,
                        self.last_name,
                        self.email,
                        self.phone,
                        self.company_name,
                        self.id,
                    ),
                )
                conn.commit()
                logging.info(f"Client {self.email} with ID {self.id} updated.")
                return True
        except sqlite3.IntegrityError as e:
            logging.error(f"Integrity error in Client.update: {e}")
            if 'email' in str(e):
                return "A client with this email already exists."
            else:
                return "Another client with this first name, last name, and company already exists."
        except sqlite3.Error as e:
            logging.error(f"Database error in Client.update: {e}")
            return False

    def delete(self):
        """Delete the client from the database.

        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            with Database.connect() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM clients WHERE id = ?", (self.id,))
                conn.commit()
                logging.info(f"Client {self.email} with ID {self.id} deleted.")
                return True
        except sqlite3.Error as e:
            logging.error(f"Database error in Client.delete: {e}")
            return False


class Contract:
    """Represents a contract in the application."""

    def __init__(
        self,
        id,
        client_id,
        sales_contact_id,
        total_amount,
        amount_remaining,
        date_created,
        status,
        created_at=None,
        updated_at=None,
    ):
        """Initialize a Contract instance.

        Args:
            id (int): The ID of the contract.
            client_id (int): The ID of the associated client.
            sales_contact_id (int): The ID of the sales contact.
            total_amount (float): Total amount of the contract.
            amount_remaining (float): Remaining amount.
            date_created (str): Date the contract was created.
            status (str): Status of the contract ('Signed' or 'Not Signed').
            created_at (str, optional): Timestamp of creation.
            updated_at (str, optional): Timestamp of last update.
        """
        self.id = id
        self.client_id = client_id
        self.sales_contact_id = sales_contact_id
        self.total_amount = total_amount
        self.amount_remaining = amount_remaining
        self.date_created = date_created
        self.status = status
        self.created_at = created_at
        self.updated_at = updated_at

    @staticmethod
    def create(client_id, sales_contact_id, total_amount, amount_remaining, status):
        """Create a new contract in the database.

        Args:
            client_id (int): The ID of the client.
            sales_contact_id (int): The ID of the sales contact.
            total_amount (float): Total amount of the contract.
            amount_remaining (float): Remaining amount.
            status (str): Status of the contract ('Signed' or 'Not Signed').

        Returns:
            Contract or str: The created Contract object or an error message.
        """
        try:
            with Database.connect() as conn:
                cursor = conn.cursor()

                # Pre-insertion check for existing contract with same unique fields
                cursor.execute(
                    """SELECT id FROM contracts WHERE client_id = ? AND total_amount = ? AND status = ? AND date_created = CURRENT_DATE""",
                    (client_id, total_amount, status),
                )
                existing_contract = cursor.fetchone()
                if existing_contract:
                    logging.warning(
                        f"Attempted to create duplicate contract for client ID {client_id}."
                    )
                    return "A contract with these details already exists for today."

                cursor.execute(
                    """INSERT INTO contracts (client_id, sales_contact_id, total_amount, amount_remaining, status)
                    VALUES (?, ?, ?, ?, ?)""",
                    (
                        client_id,
                        sales_contact_id,
                        total_amount,
                        amount_remaining,
                        status,
                    ),
                )
                conn.commit()
                contract_id = cursor.lastrowid
                logging.info(
                    f"Contract ID {contract_id} created for client ID {client_id}."
                )
                return Contract.get_by_id(contract_id)
        except sqlite3.IntegrityError as e:
            error_message = str(e)
            logging.error(f"Integrity error in Contract.create: {e}")
            if 'UNIQUE constraint failed' in error_message:
                return "A contract with these details already exists for today."
            elif 'CHECK constraint failed' in error_message:
                return "Invalid status value. Status must be 'Signed' or 'Not Signed'."
            elif 'FOREIGN KEY constraint failed' in error_message:
                return "Invalid client ID or sales contact ID."
            else:
                return f"An integrity error occurred: {error_message}"
        except sqlite3.Error as e:
            logging.error(f"Database error in Contract.create: {e}")
            return "Database error occurred while creating the contract."

    @staticmethod
    def get_by_id(contract_id):
        """Retrieve a contract by ID.

        Args:
            contract_id (int): The ID of the contract.

        Returns:
            Contract or None: The Contract object if found, else None.
        """
        try:
            conn = Database.connect()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM contracts WHERE id = ?", (contract_id,))
            contract_row = cursor.fetchone()
            if contract_row:
                return Contract(**contract_row)
            return None
        except sqlite3.Error as e:
            logging.error(f"Database error in Contract.get_by_id: {e}")
            return None
        finally:
            conn.close()

    def update(self):
        """Update the contract's information in the database.

        Returns:
            bool or str: True if successful, False or error message otherwise.
        """
        try:
            with Database.connect() as conn:
                cursor = conn.cursor()

                # Pre-update check for existing contract with same unique fields (excluding self)
                cursor.execute(
                    """SELECT id FROM contracts WHERE client_id = ? AND total_amount = ? AND status = ? AND date(created_at) = date(?) AND id != ?""",
                    (
                        self.client_id,
                        self.total_amount,
                        self.status,
                        self.created_at,
                        self.id,
                    ),
                )
                existing_contract = cursor.fetchone()
                if existing_contract:
                    logging.warning(
                        f"Attempted to update contract ID {self.id} to duplicate."
                    )
                    return "Another contract with these details already exists."

                cursor.execute(
                    """UPDATE contracts SET client_id = ?, sales_contact_id = ?, total_amount = ?, amount_remaining = ?, status = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?""",
                    (
                        self.client_id,
                        self.sales_contact_id,
                        self.total_amount,
                        self.amount_remaining,
                        self.status,
                        self.id,
                    ),
                )
                conn.commit()
                logging.info(f"Contract ID {self.id} updated.")
                return True
        except sqlite3.IntegrityError as e:
            logging.error(f"Integrity error in Contract.update: {e}")
            return "Another contract with these details already exists."
        except sqlite3.Error as e:
            logging.error(f"Database error in Contract.update: {e}")
            return False

    def delete(self):
        """Delete the contract from the database.

        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            with Database.connect() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM contracts WHERE id = ?", (self.id,))
                conn.commit()
                logging.info(f"Contract ID {self.id} deleted.")
                return True
        except sqlite3.Error as e:
            logging.error(f"Database error in Contract.delete: {e}")
            return False


class Event:
    """Represents an event in the application."""

    def __init__(
        self,
        id,
        contract_id,
        support_contact_id,
        event_date_start,
        event_date_end,
        location,
        attendees,
        notes,
        created_at=None,
        updated_at=None,
    ):
        """Initialize an Event instance.

        Args:
            id (int): The ID of the event.
            contract_id (int): The ID of the associated contract.
            support_contact_id (int): The ID of the support contact.
            event_date_start (str): Start date and time of the event.
            event_date_end (str): End date and time of the event.
            location (str): Location of the event.
            attendees (int): Number of attendees.
            notes (str): Additional notes.
            created_at (str, optional): Timestamp of creation.
            updated_at (str, optional): Timestamp of last update.
        """
        self.id = id
        self.contract_id = contract_id
        self.support_contact_id = support_contact_id
        self.event_date_start = event_date_start
        self.event_date_end = event_date_end
        self.location = location
        self.attendees = attendees
        self.notes = notes
        self.created_at = created_at
        self.updated_at = updated_at

    @staticmethod
    def create(
        contract_id,
        support_contact_id,
        event_date_start,
        event_date_end,
        location,
        attendees,
        notes,
    ):
        """Create a new event in the database.

        Args:
            contract_id (int): The ID of the associated contract.
            support_contact_id (int): The ID of the support contact.
            event_date_start (str): Start date and time of the event.
            event_date_end (str): End date and time of the event.
            location (str): Location of the event.
            attendees (int): Number of attendees.
            notes (str): Additional notes.

        Returns:
            Event or str: The created Event object or an error message.
        """
        try:
            with Database.connect() as conn:
                cursor = conn.cursor()

                # Pre-insertion check for existing event with same unique fields
                cursor.execute(
                    """SELECT id FROM events WHERE contract_id = ? AND event_date_start = ? AND event_date_end = ? AND location = ?""",
                    (contract_id, event_date_start, event_date_end, location),
                )
                existing_event = cursor.fetchone()
                if existing_event:
                    logging.warning(
                        f"Attempted to create duplicate event for contract ID {contract_id}."
                    )
                    return "An event with these details already exists."

                cursor.execute(
                    """INSERT INTO events (contract_id, support_contact_id, event_date_start, event_date_end, location, attendees, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (
                        contract_id,
                        support_contact_id,
                        event_date_start,
                        event_date_end,
                        location,
                        attendees,
                        notes,
                    ),
                )
                conn.commit()
                event_id = cursor.lastrowid
                logging.info(
                    f"Event ID {event_id} created for contract ID {contract_id}."
                )
                return Event.get_by_id(event_id)
        except sqlite3.IntegrityError as e:
            logging.error(f"Integrity error in Event.create: {e}")
            return "An event with these details already exists."
        except sqlite3.Error as e:
            logging.error(f"Database error in Event.create: {e}")
            return None

    @staticmethod
    def get_by_id(event_id):
        """Retrieve an event by ID.

        Args:
            event_id (int): The ID of the event.

        Returns:
            Event or None: The Event object if found, else None.
        """
        try:
            conn = Database.connect()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM events WHERE id = ?", (event_id,))
            event_row = cursor.fetchone()
            if event_row:
                return Event(**event_row)
            return None
        except sqlite3.Error as e:
            logging.error(f"Database error in Event.get_by_id: {e}")
            return None
        finally:
            conn.close()

    def update(self):
        """Update the event's information in the database.

        Returns:
            bool or str: True if successful, False or error message otherwise.
        """
        try:
            with Database.connect() as conn:
                cursor = conn.cursor()

                # Pre-update check for existing event with same unique fields (excluding self)
                cursor.execute(
                    """SELECT id FROM events WHERE contract_id = ? AND event_date_start = ? AND event_date_end = ? AND location = ? AND id != ?""",
                    (
                        self.contract_id,
                        self.event_date_start,
                        self.event_date_end,
                        self.location,
                        self.id,
                    ),
                )
                existing_event = cursor.fetchone()
                if existing_event:
                    logging.warning(
                        f"Attempted to update event ID {self.id} to duplicate."
                    )
                    return "Another event with these details already exists."

                cursor.execute(
                    """UPDATE events SET contract_id = ?, support_contact_id = ?, event_date_start = ?, event_date_end = ?, location = ?, attendees = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?""",
                    (
                        self.contract_id,
                        self.support_contact_id,
                        self.event_date_start,
                        self.event_date_end,
                        self.location,
                        self.attendees,
                        self.notes,
                        self.id,
                    ),
                )
                conn.commit()
                logging.info(f"Event ID {self.id} updated.")
                return True
        except sqlite3.IntegrityError as e:
            logging.error(f"Integrity error in Event.update: {e}")
            return "Another event with these details already exists."
        except sqlite3.Error as e:
            logging.error(f"Database error in Event.update: {e}")
            return False

    def delete(self):
        """Delete the event from the database.

        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            with Database.connect() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM events WHERE id = ?", (self.id,))
                conn.commit()
                logging.info(f"Event ID {self.id} deleted.")
                return True
        except sqlite3.Error as e:
            logging.error(f"Database error in Event.delete: {e}")
            return False


class Permission:
    """Represents a permission assigned to a role."""

    def __init__(self, id, role_id, entity, action):
        """Initialize a Permission instance.

        Args:
            id (int): The ID of the permission.
            role_id (int): The ID of the associated role.
            entity (str): The entity the permission applies to.
            action (str): The action permitted (e.g., 'create', 'read').
        """
        self.id = id
        self.role_id = role_id
        self.entity = entity
        self.action = action

    @staticmethod
    def get_permissions_by_role(role_id):
        """Retrieve permissions associated with a role.

        Args:
            role_id (int): The ID of the role.

        Returns:
            list: A list of Permission objects.
        """
        try:
            conn = Database.connect()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM permissions WHERE role_id = ?", (role_id,))
            permissions = []
            for row in cursor.fetchall():
                permissions.append(Permission(**row))
            return permissions
        except sqlite3.Error as e:
            logging.error(f"Database error in Permission.get_permissions_by_role: {e}")
            return []
        finally:
            conn.close()