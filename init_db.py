# init_db.py

import sqlite3
import getpass

from auth import create_user

def initialize_database():
    # Initialize the database schema
    with sqlite3.connect('app.db') as conn:
        cursor = conn.cursor()
        with open('schema.sql', 'r') as f:
            cursor.executescript(f.read())
    print("Database initialized successfully.")

    # Insert default roles
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

    # Create admin user
    admin_username = input("Enter admin username: ")
    admin_password = getpass.getpass("Enter admin password: ")

    # Get role_id for 'Management'
    with sqlite3.connect('app.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM roles WHERE name = ?", ('Management',))
        role = cursor.fetchone()
        if role:
            role_id = role[0]
            create_user(admin_username, admin_password, role_id)
            print(f"Admin user '{admin_username}' created.")
        else:
            print("Error: 'Management' role not found.")

if __name__ == "__main__":
    initialize_database()
