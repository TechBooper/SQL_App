import sqlite3
import bcrypt

def authenticate(username, password):
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, password_hash, role_id FROM users WHERE username = ?",
        (username,)
    )
    user = cursor.fetchone()
    conn.close()

    if user and bcrypt.checkpw(password.encode(), user[1]):
        return {'user_id': user[0], 'role_id': user[2]}
    else:
        return None
    

def get_user_role(user_id):
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()
    cursor.execute(
        "SELECT roles.name FROM roles JOIN users ON users.role_id = roles.id WHERE users.id = ?",
        (user_id,)
    )
    role = cursor.fetchone()
    conn.close()
    return role[0] if role else None