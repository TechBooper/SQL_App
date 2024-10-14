import sqlite3
import sentry_setup

def view_profile(user_id):
    try:
        with sqlite3.connect('app.db') as conn:
            conn.row_factory = sqlite3.Row  # Enables column access by name
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT users.id, users.username, roles.name AS role, profiles.bio
                FROM users
                JOIN roles ON users.role_id = roles.id
                LEFT JOIN profiles ON users.id = profiles.user_id
                WHERE users.id = ?
                """,
                (user_id,)
            )
            user = cursor.fetchone()
            if user:
                print("User ID:", user['id'])
                print("Username:", user['username'])
                print("Role:", user['role'])
                print("Bio:", user['bio'] if user['bio'] else "No bio available.")
            else:
                print("User not found.")
    except Exception as e:
        sentry_setup.capture_exception(e)
        print("An error occurred while viewing the profile.")

def update_profile(user_id, bio):
    try:
        with sqlite3.connect('app.db') as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO profiles (user_id, bio) VALUES (?, ?) ON CONFLICT(user_id) DO UPDATE SET bio = ?",
                (user_id, bio, bio)
            )
            conn.commit()
            print("Profile updated successfully.")
    except Exception as e:
        sentry_setup.capture_exception(e)
        print("An error occurred while updating the profile.")

def create_profile(user_id, bio):
    try:
        with sqlite3.connect('app.db') as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO profiles (user_id, bio) VALUES (?, ?)",
                (user_id, bio)
            )
            conn.commit()
            print("Profile created successfully.")
    except sqlite3.IntegrityError:
        print("Profile already exists.")
    except Exception as e:
        sentry_setup.capture_exception(e)
        print("An error occurred while creating the profile.")

def delete_profile(user_id):
    try:
        with sqlite3.connect('app.db') as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM profiles WHERE user_id = ?",
                (user_id,)
            )
            conn.commit()
            print("Profile deleted successfully.")
    except Exception as e:
        sentry_setup.capture_exception(e)
        print("An error occurred while deleting the profile.")
