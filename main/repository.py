# repository.py

import logging
import sqlite3
import bcrypt
from datetime import datetime

from .models import Database, User, Role, Client, Contract, Event, Permission

logging.basicConfig(
    filename="repository.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


class UserRepository:
    @staticmethod
    def create_user(username, password, role_id, email):
        """
        Handles User creation in DB. Returns a User instance or an error message.
        """
        try:
            password_hash = bcrypt.hashpw(
                password.encode("utf-8"), bcrypt.gensalt()
            ).decode("utf-8")

            with Database.connect() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO users (username, password_hash, role_id, email)
                    VALUES (?, ?, ?, ?)
                    """,
                    (username, password_hash, role_id, email),
                )
                conn.commit()

            # Return the newly created user object
            return UserRepository.get_user_by_username(username)

        except sqlite3.IntegrityError as e:
            logging.error(f"Integrity error in UserRepository.create_user: {e}")
            if "username" in str(e):
                return "A user with this username already exists."
            elif "email" in str(e):
                return "A user with this email already exists."
            else:
                return "An error occurred while creating the user."
        except sqlite3.Error as e:
            logging.error(f"Database error in UserRepository.create_user: {e}")
            return "An error occurred while creating the user."

    @staticmethod
    def get_user_by_username(username):
        """
        Fetches a user by username. Returns a User instance or None.
        """
        try:
            conn = Database.connect()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            row = cursor.fetchone()
            if row:
                return User(**dict(row))
            return None
        except sqlite3.Error as e:
            logging.error(f"Database error in UserRepository.get_user_by_username: {e}")
            return None
        finally:
            if conn:
                conn.close()

    @staticmethod
    def get_all_users():
        """
        Fetches all users from the database. Returns a list of User instances.
        """
        try:
            conn = Database.connect()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users")
            rows = cursor.fetchall()
            return [User(**dict(row)) for row in rows]
        except sqlite3.Error as e:
            logging.error(f"Database error in UserRepository.get_all_users: {e}")
            return []
        finally:
            if conn:
                conn.close()

    @staticmethod
    def update_user(user_obj, new_password=None):
        """
        Updates the User record in DB.
        Returns True on success, or an error message / False on failure.
        """
        try:
            with Database.connect() as conn:
                cursor = conn.cursor()
                if new_password:
                    new_hash = bcrypt.hashpw(
                        new_password.encode("utf-8"), bcrypt.gensalt()
                    ).decode("utf-8")
                else:
                    new_hash = user_obj.password_hash

                cursor.execute(
                    """
                    UPDATE users
                    SET password_hash = ?,
                        role_id = ?,
                        email = ?,
                        updated_at = datetime('now')
                    WHERE username = ?
                    """,
                    (new_hash, user_obj.role_id, user_obj.email, user_obj.username),
                )
                conn.commit()
                logging.info(f"User {user_obj.username} updated.")
                return True
        except sqlite3.IntegrityError as e:
            logging.error(f"Integrity error in UserRepository.update_user: {e}")
            if "username" in str(e):
                return "A user with this username already exists."
            elif "email" in str(e):
                return "A user with this email already exists."
            return "An error occurred while updating the user."
        except sqlite3.Error as e:
            logging.error(f"Database error in UserRepository.update_user: {e}")
            return False

    @staticmethod
    def delete_user(user_obj):
        """
        Deletes a User from the DB.
        Returns True on success, or False on DB error.
        """
        try:
            with Database.connect() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM users WHERE username = ?", (user_obj.username,)
                )
                conn.commit()
                logging.info(f"User {user_obj.username} deleted.")
                return True
        except sqlite3.Error as e:
            logging.error(f"Database error in UserRepository.delete_user: {e}")
            return False

    @staticmethod
    def verify_user_password(user_obj, password):
        """
        Verifies a plaintext password against the stored hash.
        Returns True if matching, else False.
        """
        try:
            return bcrypt.checkpw(
                password.encode("utf-8"), user_obj.password_hash.encode("utf-8")
            )
        except Exception as e:
            logging.error(f"Error verifying password for user {user_obj.username}: {e}")
            return False


class RoleRepository:
    @staticmethod
    def get_role_by_name(name):
        """
        Fetches a Role by its name. Returns a Role instance or None.
        """
        try:
            conn = Database.connect()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM roles WHERE name = ?", (name,))
            row = cursor.fetchone()
            if row:
                return Role(**dict(row))
            return None
        except sqlite3.Error as e:
            logging.error(f"Database error in RoleRepository.get_role_by_name: {e}")
            return None
        finally:
            if conn:
                conn.close()


class ClientRepository:
    @staticmethod
    def create_client(
        first_name, last_name, email, phone, company_name, sales_contact_id
    ):
        """
        Creates a Client in the DB. Returns the new Client or an error message.
        """
        try:
            with Database.connect() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO clients 
                    (first_name, last_name, email, phone, company_name, sales_contact_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
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
                return ClientRepository.get_client_by_email(email)
        except sqlite3.IntegrityError as e:
            logging.error(f"Integrity error in ClientRepository.create_client: {e}")
            # Adjust the message as per your business logic
            return (
                "A client with this first name, last name, and company already exists."
            )
        except sqlite3.Error as e:
            logging.error(f"Database error in ClientRepository.create_client: {e}")
            return None

    @staticmethod
    def get_client_by_email(email):
        """
        Fetches a Client by email. Returns a Client instance or None.
        """
        try:
            conn = Database.connect()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM clients WHERE email = ?", (email,))
            row = cursor.fetchone()
            if row:
                return Client(**dict(row))
            return None
        except sqlite3.Error as e:
            logging.error(
                f"Database error in ClientRepository.get_client_by_email: {e}"
            )
            return None
        finally:
            if conn:
                conn.close()

    @staticmethod
    def update_client(client_obj):
        """
        Updates an existing Client in DB. Returns True on success, or an error message / False on failure.
        """
        try:
            with Database.connect() as conn:
                cursor = conn.cursor()
                # Check uniqueness
                cursor.execute(
                    """
                    SELECT email FROM clients
                    WHERE first_name = ? AND last_name = ? AND company_name = ?
                          AND email != ?
                    """,
                    (
                        client_obj.first_name,
                        client_obj.last_name,
                        client_obj.company_name,
                        client_obj.email,
                    ),
                )
                existing = cursor.fetchone()
                if existing:
                    return "Another client with this first name, last name, and company already exists."

                cursor.execute(
                    """
                    UPDATE clients
                    SET first_name = ?,
                        last_name = ?,
                        phone = ?,
                        company_name = ?,
                        last_contact = date('now'),
                        updated_at = datetime('now')
                    WHERE email = ?
                    """,
                    (
                        client_obj.first_name,
                        client_obj.last_name,
                        client_obj.phone,
                        client_obj.company_name,
                        client_obj.email,
                    ),
                )
                conn.commit()
                logging.info(f"Client {client_obj.email} updated.")
                return True
        except sqlite3.IntegrityError as e:
            logging.error(f"Integrity error in ClientRepository.update_client: {e}")
            return "Another client with these details already exists."
        except sqlite3.Error as e:
            logging.error(f"Database error in ClientRepository.update_client: {e}")
            return False

    @staticmethod
    def delete_client(client_obj):
        """
        Deletes a Client from the DB. Returns True on success, or False on DB error.
        """
        try:
            with Database.connect() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM clients WHERE email = ?", (client_obj.email,)
                )
                conn.commit()
                logging.info(f"Client {client_obj.email} deleted.")
                return True
        except sqlite3.Error as e:
            logging.error(f"Database error in ClientRepository.delete_client: {e}")
            return False


class ContractRepository:
    @staticmethod
    def create_contract(
        client_id, sales_contact_id, total_amount, amount_remaining, status
    ):
        """
        Creates a new Contract. Returns the Contract or an error message.
        """
        try:
            if status not in ("Signed", "Not Signed"):
                return "CHECK constraint failed: status IN ('Signed', 'Not Signed')"
            with Database.connect() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO contracts
                    (client_id, sales_contact_id, total_amount, amount_remaining, status)
                    VALUES (?, ?, ?, ?, ?)
                    """,
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
            return ContractRepository.get_contract_by_id(contract_id)
        except sqlite3.IntegrityError as e:
            logging.error(f"Integrity error in ContractRepository.create_contract: {e}")
            return str(e)
        except sqlite3.Error as e:
            logging.error(f"Database error in ContractRepository.create_contract: {e}")
            return "Database error occurred."

    @staticmethod
    def get_contract_by_id(contract_id):
        """
        Fetches a Contract by ID. Returns a Contract instance or None.
        """
        try:
            conn = Database.connect()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM contracts WHERE id = ?", (contract_id,))
            row = cursor.fetchone()
            if row:
                return Contract(**dict(row))
            return None
        except sqlite3.Error as e:
            logging.error(
                f"Database error in ContractRepository.get_contract_by_id: {e}"
            )
            return None
        finally:
            if conn:
                conn.close()

    @staticmethod
    def update_contract(contract_obj):
        """
        Updates a Contract. Returns True on success, or False on error.
        """
        try:
            with Database.connect() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE contracts
                    SET client_id = ?,
                        sales_contact_id = ?,
                        total_amount = ?,
                        amount_remaining = ?,
                        status = ?,
                        updated_at = datetime('now')
                    WHERE id = ?
                    """,
                    (
                        contract_obj.client_id,
                        contract_obj.sales_contact_id,
                        contract_obj.total_amount,
                        contract_obj.amount_remaining,
                        contract_obj.status,
                        contract_obj.id,
                    ),
                )
                conn.commit()
                logging.info(f"Contract ID {contract_obj.id} updated.")
                return True
        except sqlite3.Error as e:
            logging.error(f"Database error in ContractRepository.update_contract: {e}")
            return False

    @staticmethod
    def delete_contract(contract_obj):
        """
        Deletes a Contract. Returns True on success, or False on error.
        """
        try:
            with Database.connect() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM contracts WHERE id = ?", (contract_obj.id,))
                conn.commit()
                logging.info(f"Contract ID {contract_obj.id} deleted.")
                return True
        except sqlite3.Error as e:
            logging.error(f"Database error in ContractRepository.delete_contract: {e}")
            return False


class EventRepository:
    @staticmethod
    def create_event(
        contract_id,
        support_contact_id,
        event_date_start,
        event_date_end,
        location,
        attendees,
        notes,
    ):
        """
        Creates a new Event. Returns the Event or an error message / None on error.
        """
        try:
            with Database.connect() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO events
                    (contract_id, support_contact_id, event_date_start, event_date_end,
                     location, attendees, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
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
            return EventRepository.get_event_by_id(event_id)
        except sqlite3.IntegrityError as e:
            logging.error(f"Integrity error in EventRepository.create_event: {e}")
            return "An event with these details already exists."
        except sqlite3.Error as e:
            logging.error(f"Database error in EventRepository.create_event: {e}")
            return None

    @staticmethod
    def get_event_by_id(event_id):
        """
        Fetches an Event by ID. Returns an Event instance or None.
        """
        try:
            conn = Database.connect()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM events WHERE id = ?", (event_id,))
            row = cursor.fetchone()
            if row:
                return Event(**dict(row))
            return None
        except sqlite3.Error as e:
            logging.error(f"Database error in EventRepository.get_event_by_id: {e}")
            return None
        finally:
            if conn:
                conn.close()

    @staticmethod
    def update_event(event_obj):
        """
        Updates an Event record. Returns a success string or error string.
        """
        try:
            with Database.connect() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE events
                    SET contract_id = ?,
                        support_contact_id = ?,
                        event_date_start = ?,
                        event_date_end = ?,
                        location = ?,
                        attendees = ?,
                        notes = ?,
                        updated_at = datetime('now')
                    WHERE id = ?
                    """,
                    (
                        event_obj.contract_id,
                        event_obj.support_contact_id,
                        event_obj.event_date_start,
                        event_obj.event_date_end,
                        event_obj.location,
                        event_obj.attendees,
                        event_obj.notes,
                        event_obj.id,
                    ),
                )
                conn.commit()
                if cursor.rowcount > 0:
                    logging.info(f"Event ID {event_obj.id} updated successfully.")
                    return "updated successfully"
                return "Error updating event."
        except sqlite3.Error as e:
            logging.error(f"Database error in EventRepository.update_event: {e}")
            return "Error updating event."

    @staticmethod
    def delete_event(event_obj):
        """
        Deletes an Event. Returns True on success, False on error.
        """
        try:
            with Database.connect() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM events WHERE id = ?", (event_obj.id,))
                conn.commit()
                logging.info(f"Event ID {event_obj.id} deleted.")
                return True
        except sqlite3.Error as e:
            logging.error(f"Database error in EventRepository.delete_event: {e}")
            return False


class PermissionRepository:
    @staticmethod
    def get_permissions_by_role(role_name):
        """
        Fetches all permissions for a given role_name. Returns a list of Permission objects.
        """
        try:
            conn = Database.connect()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM permissions WHERE role_id = ?", (role_name,))
            return [Permission(**dict(row)) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logging.error(
                f"Database error in PermissionRepository.get_permissions_by_role: {e}"
            )
            return []
        finally:
            if conn:
                conn.close()

    @staticmethod
    def has_permission(role_name, entity, action):
        """
        Checks if a role has permission for a specific entity/action.
        Returns True or False.
        """
        try:
            conn = Database.connect()
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT 1 FROM permissions
                WHERE role_id = ?
                  AND (entity = ? OR entity = '*')
                  AND (action = ? OR action = '*')
                """,
                (role_name, entity, action),
            )
            return bool(cursor.fetchone())
        except sqlite3.Error as e:
            logging.error(f"Database error in PermissionRepository.has_permission: {e}")
            return False
        finally:
            if conn:
                conn.close()
