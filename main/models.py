# models.py

import bcrypt
import sqlite3
import logging
import os
import sys
from datetime import datetime

logging.basicConfig(
    filename="models.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE_FOLDER = os.path.join(BASE_DIR, "db_folder")
DATABASE_URL = os.path.join(DATABASE_FOLDER, "app.db")


class Database:
    @staticmethod
    def connect():
        try:
            conn = sqlite3.connect(DATABASE_URL)
            conn.row_factory = sqlite3.Row
            return conn
        except sqlite3.Error as e:
            logging.error(f"Error connecting to database: {e}")
            raise


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
        from main.repository import UserRepository

        return UserRepository.create_user(username, password, role_id, email)

    @staticmethod
    def get_by_username(username):
        from main.repository import UserRepository

        return UserRepository.get_user_by_username(username)

    @staticmethod
    def get_all_users():
        from main.repository import UserRepository

        return UserRepository.get_all_users()

    def update(self, password=None):
        from main.repository import UserRepository

        return UserRepository.update_user(self, password)

    def delete(self):
        from main.repository import UserRepository

        return UserRepository.delete_user(self)

    def verify_password(self, password):
        from main.repository import UserRepository

        return UserRepository.verify_user_password(self, password)


class Role:
    def __init__(self, **kwargs):
        self.name = kwargs.get("name")
        logging.debug(f"Created Role instance: {self.__dict__}")

    def is_management_role(self):
        """Check if the role is 'Management'."""
        return self.name == "Management"

    @staticmethod
    def get_by_name(name):
        from main.repository import RoleRepository

        return RoleRepository.get_role_by_name(name)


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
        from main.repository import ClientRepository

        return ClientRepository.create_client(
            first_name, last_name, email, phone, company_name, sales_contact_id
        )

    @staticmethod
    def get_by_email(email):
        from main.repository import ClientRepository

        return ClientRepository.get_client_by_email(email)

    def update(self):
        from main.repository import ClientRepository

        return ClientRepository.update_client(self)

    def delete(self):
        from main.repository import ClientRepository

        return ClientRepository.delete_client(self)


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
        from main.repository import ContractRepository

        return ContractRepository.create_contract(
            client_id, sales_contact_id, total_amount, amount_remaining, status
        )

    @staticmethod
    def get_by_id(contract_id):
        from main.repository import ContractRepository

        return ContractRepository.get_contract_by_id(contract_id)

    def update(self):
        from main.repository import ContractRepository

        return ContractRepository.update_contract(self)

    def delete(self):
        from main.repository import ContractRepository

        return ContractRepository.delete_contract(self)


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
    def create(
        contract_id,
        support_contact_id,
        event_date_start,
        event_date_end,
        location,
        attendees,
        notes,
    ):
        from main.repository import EventRepository

        return EventRepository.create_event(
            contract_id,
            support_contact_id,
            event_date_start,
            event_date_end,
            location,
            attendees,
            notes,
        )

    @staticmethod
    def get_by_id(event_id):
        from main.repository import EventRepository

        return EventRepository.get_event_by_id(event_id)

    def update(self):
        from main.repository import EventRepository

        return EventRepository.update_event(self)

    def delete(self):
        from main.repository import EventRepository

        return EventRepository.delete_event(self)


class Permission:
    def __init__(self, **kwargs):
        self.id = kwargs.get("id")
        self.role_id = kwargs.get("role_id")
        self.entity = kwargs.get("entity")
        self.action = kwargs.get("action")
        logging.debug(f"Created Permission instance: {self.__dict__}")

    @staticmethod
    def get_permissions_by_role(role_name):
        from main.repository import PermissionRepository

        return PermissionRepository.get_permissions_by_role(role_name)

    @staticmethod
    def has_permission(role_name, entity, action):
        from main.repository import PermissionRepository

        return PermissionRepository.has_permission(role_name, entity, action)
