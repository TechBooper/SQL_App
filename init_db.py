import sqlite3
import getpass
from auth import create_user

def initialize_database():
    # Initialize the database schema from schema.sql
    with sqlite3.connect('app.db') as conn:
        cursor = conn.cursor()
        with open('schema.sql', 'r') as f:
            cursor.executescript(f.read())
    print("Database initialized successfully.")

    # Insert default roles into the roles table
    with sqlite3.connect('app.db') as conn:
        cursor = conn.cursor()
        roles = ['Management', 'Sales', 'Support']
        for role_name in roles:
            cursor.execute(
                "INSERT INTO roles (name) VALUES (?) ON CONFLICT(name) DO NOTHING",
                (role_name,)
            )
        conn.commit()
    print("Default roles inserted.")

    # Create the admin user with the 'Management' role
    admin_username = input("Enter admin username: ")
    admin_email = input("Enter admin email: ")  # Added email prompt
    admin_password = getpass.getpass("Enter admin password: ")

    # Get role_id for 'Management'
    with sqlite3.connect('app.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM roles WHERE name = ?", ('Management',))
        role = cursor.fetchone()
        if role:
            role_id = role[0]
            create_user(admin_username, admin_password, role_id, admin_email)  # Pass email to create_user
            print(f"Admin user '{admin_username}' created.")
        else:
            print("Error: 'Management' role not found.")
    
    # Optionally, insert default permissions
    insert_default_permissions()

def insert_default_permissions():
    # Insert default permissions for each role
    with sqlite3.connect('app.db') as conn:
        cursor = conn.cursor()

        # Permissions for Management
        management_permissions = [
            ('Management', 'client', 'create'),
            ('Management', 'client', 'update'),
            ('Management', 'contract', 'create'),
            ('Management', 'contract', 'update'),
            ('Management', 'event', 'create'),
            ('Management', 'event', 'update')
        ]

        # Permissions for Sales
        sales_permissions = [
            ('Sales', 'client', 'create'),
            ('Sales', 'client', 'update'),
            ('Sales', 'contract', 'create'),
            ('Sales', 'contract', 'update'),
            ('Sales', 'event', 'create')
        ]

        # Permissions for Support
        support_permissions = [
            ('Support', 'event', 'read'),
            ('Support', 'event', 'update')
        ]

        # Insert Management Permissions
        for role, entity, action in management_permissions:
            cursor.execute("""
                INSERT INTO permissions (role_id, entity, action)
                SELECT roles.id, ?, ?
                FROM roles
                WHERE roles.name = ?""", (entity, action, role))
        
        # Insert Sales Permissions
        for role, entity, action in sales_permissions:
            cursor.execute("""
                INSERT INTO permissions (role_id, entity, action)
                SELECT roles.id, ?, ?
                FROM roles
                WHERE roles.name = ?""", (entity, action, role))
        
        # Insert Support Permissions
        for role, entity, action in support_permissions:
            cursor.execute("""
                INSERT INTO permissions (role_id, entity, action)
                SELECT roles.id, ?, ?
                FROM roles
                WHERE roles.name = ?""", (entity, action, role))

        conn.commit()
    print("Default permissions inserted.")

if __name__ == "__main__":
    initialize_database()
