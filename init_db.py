# init_db.py
import sqlite3

from database import create_role, create_user

def initialize_database():
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()
    with open('schema.sql', 'r') as f:
        cursor.executescript(f.read())
    conn.commit()
    conn.close()
    print("Database initialized successfully.")
    create_role('admin')
    create_role('user')
    create_user('admin', 'admin_password', 'admin')

if __name__ == "__main__":
    initialize_database()