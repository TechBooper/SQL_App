# models.py

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
    DB_NAME = "app.db"

    @staticmethod
    def connect():
        conn = sqlite3.connect(Database.DB_NAME)
        conn.row_factory = sqlite3.Row
        return conn

# User model
class User:
    def __init__(self, **kwargs):
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

# Role model
class Role:
    def __init__(self, **kwargs):
        self.id = kwargs.get("id")
        self.name = kwargs.get("name")

    @staticmethod
    def get_by_id(role_id):
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

# Client model
class Client:
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

# Contract model
class Contract:
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

# Event model
class Event:
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

# Permission model
class Permission:
    def __init__(self, id, role_id, entity, action):
        self.id = id
        self.role_id = role_id
        self.entity = entity
        self.action = action

    @staticmethod
    def get_permissions_by_role(role_id):
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
