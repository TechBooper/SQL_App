import bcrypt
import sqlite3
import logging
import os
import getpass
import sys
import re
from datetime import datetime

# Configure logging
logging.basicConfig(
    filename="models.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE_FOLDER = os.path.join(BASE_DIR, "database")
DATABASE_URL = os.path.join(DATABASE_FOLDER, "app.db")


class Database:
    @staticmethod
    def connect():
        conn = sqlite3.connect(DATABASE_URL)
        conn.row_factory = sqlite3.Row
        return conn


class User:
    def __init__(self, **kwargs):
        self.username = kwargs.get("username")
        self.password_hash = kwargs.get("password_hash")
        self.role_id = kwargs.get("role_id")
        self.email = kwargs.get("email")
        self.created_at = kwargs.get("created_at")
        self.updated_at = kwargs.get("updated_at")
        logging.debug(f"Created User instance: {self.__dict__}")

    @staticmethod
    def create(username, password, role_id, email):
        try:
            password_hash = bcrypt.hashpw(
                password.encode("utf-8"), bcrypt.gensalt()
            ).decode("utf-8")
            with Database.connect() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO users (username, password_hash, role_id, email) VALUES (?, ?, ?, ?)",
                    (username, password_hash, role_id, email),
                )
                conn.commit()
                return User.get_by_username(username)
        except sqlite3.IntegrityError as e:
            logging.error(f"Integrity error in User.create: {e}")
            if "username" in str(e):
                return "A user with this username already exists."
            elif "email" in str(e):
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
                return User(**dict(user_row))
            return None
        except sqlite3.Error as e:
            logging.error(f"Database error in User.get_by_username: {e}")
            return None
        finally:
            conn.close()

    @staticmethod
    def get_all_users():
        try:
            conn = Database.connect()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users")
            rows = cursor.fetchall()
            users = [User(**dict(row)) for row in rows]
            return users
        except sqlite3.Error as e:
            logging.error(f"Database error in User.get_all_users: {e}")
            return []
        finally:
            conn.close()

    def update(self, password=None):
        try:
            with Database.connect() as conn:
                cursor = conn.cursor()
                if password:
                    new_hash = bcrypt.hashpw(
                        password.encode("utf-8"), bcrypt.gensalt()
                    ).decode("utf-8")
                else:
                    new_hash = self.password_hash

                cursor.execute(
                    "UPDATE users SET password_hash = ?, role_id = ?, email = ?, updated_at = datetime('now') WHERE username = ?",
                    (new_hash, self.role_id, self.email, self.username),
                )
                conn.commit()
                logging.info(f"User {self.username} updated.")
                return True
        except sqlite3.IntegrityError as e:
            logging.error(f"Integrity error in User.update: {e}")
            if "username" in str(e):
                return "A user with this username already exists."
            elif "email" in str(e):
                return "A user with this email already exists."
            return "An error occurred while updating the user."
        except sqlite3.Error as e:
            logging.error(f"Database error in User.update: {e}")
            return False

    def delete(self):
        try:
            with Database.connect() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM users WHERE username = ?", (self.username,))
                conn.commit()
                logging.info(f"User {self.username} deleted.")
                return True
        except sqlite3.Error as e:
            logging.error(f"Database error in User.delete: {e}")
            return False

    def verify_password(self, password):
        try:
            return bcrypt.checkpw(password.encode("utf-8"), self.password_hash.encode("utf-8"))
        except Exception as e:
            logging.error(f"Error verifying password for user {self.username}: {e}")
            return False


class Role:
    def __init__(self, **kwargs):
        self.name = kwargs.get("name")
        logging.debug(f"Created Role instance: {self.__dict__}")

    @staticmethod
    def get_by_name(name):
        try:
            conn = Database.connect()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM roles WHERE name = ?", (name,))
            role_row = cursor.fetchone()
            if role_row:
                return Role(**dict(role_row))
            return None
        except sqlite3.Error as e:
            logging.error(f"Database error in Role.get_by_name: {e}")
            return None
        finally:
            conn.close()


class Client:
    def __init__(self, **kwargs):
        self.email = kwargs.get("email")
        self.first_name = kwargs.get("first_name")
        self.last_name = kwargs.get("last_name")
        self.phone = kwargs.get("phone")
        self.company_name = kwargs.get("company_name")
        self.last_contact = kwargs.get("last_contact")
        self.sales_contact_id = kwargs.get("sales_contact_id")
        self.created_at = kwargs.get("created_at")
        self.updated_at = kwargs.get("updated_at")
        logging.debug(f"Created Client instance: {self.__dict__}")

    @staticmethod
    def create(first_name, last_name, email, phone, company_name, sales_contact_id):
        try:
            with Database.connect() as conn:
                cursor = conn.cursor()

                # Check for duplicate client
                cursor.execute(
                    "SELECT email FROM clients WHERE first_name = ? AND last_name = ? AND company_name = ?",
                    (first_name, last_name, company_name),
                )
                existing = cursor.fetchone()
                if existing:
                    return "A client with this first name, last name, and company already exists."

                cursor.execute(
                    """INSERT INTO clients (first_name, last_name, email, phone, company_name, sales_contact_id)
                    VALUES (?, ?, ?, ?, ?, ?)""",
                    (first_name, last_name, email, phone, company_name, sales_contact_id),
                )
                conn.commit()
                return Client.get_by_email(email)
        except sqlite3.IntegrityError as e:
            logging.error(f"Integrity error in Client.create: {e}")
            if "email" in str(e):
                return "A client with this email already exists."
            return "A client with these details already exists."
        except sqlite3.Error as e:
            logging.error(f"Database error in Client.create: {e}")
            return "An error occurred while creating the client."

    @staticmethod
    def get_by_email(email):
        try:
            conn = Database.connect()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM clients WHERE email = ?", (email,))
            row = cursor.fetchone()
            if row:
                return Client(**dict(row))
            return None
        except sqlite3.Error as e:
            logging.error(f"Database error in Client.get_by_email: {e}")
            return None
        finally:
            conn.close()

    def update(self):
        try:
            with Database.connect() as conn:
                cursor = conn.cursor()
                # Check uniqueness
                cursor.execute(
                    "SELECT email FROM clients WHERE first_name = ? AND last_name = ? AND company_name = ? AND email != ?",
                    (self.first_name, self.last_name, self.company_name, self.email),
                )
                existing = cursor.fetchone()
                if existing:
                    return "Another client with this first name, last name, and company already exists."

                cursor.execute(
                    """UPDATE clients SET first_name = ?, last_name = ?, phone = ?, company_name = ?, last_contact = date('now'), updated_at = datetime('now')
                    WHERE email = ?""",
                    (
                        self.first_name,
                        self.last_name,
                        self.phone,
                        self.company_name,
                        self.email,
                    ),
                )
                conn.commit()
                logging.info(f"Client {self.email} updated.")
                return True
        except sqlite3.IntegrityError as e:
            logging.error(f"Integrity error in Client.update: {e}")
            return "Another client with these details already exists."
        except sqlite3.Error as e:
            logging.error(f"Database error in Client.update: {e}")
            return False

    def delete(self):
        try:
            with Database.connect() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM clients WHERE email = ?", (self.email,))
                conn.commit()
                logging.info(f"Client {self.email} deleted.")
                return True
        except sqlite3.Error as e:
            logging.error(f"Database error in Client.delete: {e}")
            return False


class Contract:
    def __init__(self, **kwargs):
        self.id = kwargs.get("id")
        self.client_id = kwargs.get("client_id")
        self.sales_contact_id = kwargs.get("sales_contact_id")
        self.total_amount = kwargs.get("total_amount")
        self.amount_remaining = kwargs.get("amount_remaining")
        self.status = kwargs.get("status")
        self.date_created = kwargs.get("date_created")
        self.created_at = kwargs.get("created_at")
        self.updated_at = kwargs.get("updated_at")
        logging.debug(f"Created Contract instance: {self.__dict__}")

    @staticmethod
    def create(client_id, sales_contact_id, total_amount, amount_remaining, status):
        try:
            with Database.connect() as conn:
                cursor = conn.cursor()
                # date_created defaults to date('now'), so no need to insert explicitly
                cursor.execute(
                    """INSERT INTO contracts (client_id, sales_contact_id, total_amount, amount_remaining, status)
                    VALUES (?, ?, ?, ?, ?)""",
                    (client_id, sales_contact_id, total_amount, amount_remaining, status),
                )
                conn.commit()
                contract_id = cursor.lastrowid
                return Contract.get_by_id(contract_id)
        except sqlite3.IntegrityError as e:
            logging.error(f"Integrity error in Contract.create: {e}")
            return str(e)
        except sqlite3.Error as e:
            logging.error(f"Database error in Contract.create: {e}")
            return "Database error occurred."

    @staticmethod
    def get_by_id(contract_id):
        try:
            conn = Database.connect()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM contracts WHERE id = ?", (contract_id,))
            row = cursor.fetchone()
            if row:
                return Contract(**dict(row))
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
                cursor.execute(
                    """UPDATE contracts SET client_id = ?, sales_contact_id = ?, total_amount = ?, amount_remaining = ?, status = ?, updated_at = datetime('now')
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


class Event:
    def __init__(self, **kwargs):
        self.id = kwargs.get("id")
        self.contract_id = kwargs.get("contract_id")
        self.support_contact_id = kwargs.get("support_contact_id")
        self.event_date_start = kwargs.get("event_date_start")
        self.event_date_end = kwargs.get("event_date_end")
        self.location = kwargs.get("location")
        self.attendees = kwargs.get("attendees")
        self.notes = kwargs.get("notes")
        self.created_at = kwargs.get("created_at")
        self.updated_at = kwargs.get("updated_at")
        logging.debug(f"Created Event instance: {self.__dict__}")

    @staticmethod
    def create(contract_id, support_contact_id, event_date_start, event_date_end, location, attendees, notes):
        try:
            with Database.connect() as conn:
                cursor = conn.cursor()
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
            row = cursor.fetchone()
            if row:
                return Event(**dict(row))
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
                cursor.execute(
                    """UPDATE events SET contract_id = ?, support_contact_id = ?, event_date_start = ?, event_date_end = ?, location = ?, attendees = ?, notes = ?, updated_at = datetime('now')
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
        except sqlite3.IntegrityError:
            logging.warning(f"Duplicate event attempted in Event.update for ID {self.id}.")
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


class Permission:
    def __init__(self, **kwargs):
        self.id = kwargs.get("id")
        self.role_id = kwargs.get("role_id")
        self.entity = kwargs.get("entity")
        self.action = kwargs.get("action")
        logging.debug(f"Created Permission instance: {self.__dict__}")

    @staticmethod
    def get_permissions_by_role(role_name):
        try:
            conn = Database.connect()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM permissions WHERE role_id = ?", (role_name,))
            permissions = [Permission(**dict(row)) for row in cursor.fetchall()]
            return permissions
        except sqlite3.Error as e:
            logging.error(f"Database error in Permission.get_permissions_by_role: {e}")
            return []
        finally:
            conn.close()

    @staticmethod
    def has_permission(role_name, entity, action):
        try:
            conn = Database.connect()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT 1 FROM permissions WHERE role_id = ? AND entity = ? AND action = ?",
                (role_name, entity, action),
            )
            result = cursor.fetchone()
            return result is not None
        except sqlite3.Error as e:
            logging.error(f"Database error in Permission.has_permission: {e}")
            return False
        finally:
            conn.close()
