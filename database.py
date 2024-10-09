import bcrypt

def create_user(username, password, role_name):
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()

    # Get role_id
    cursor.execute("SELECT id FROM roles WHERE name = ?", (role_name,))
    role = cursor.fetchone()
    if not role:
        print(f"Role '{role_name}' does not exist.")
        conn.close()
        return

    role_id = role[0]
    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

    try:
        cursor.execute(
            "INSERT INTO users (username, password_hash, role_id) VALUES (?, ?, ?)",
            (username, password_hash, role_id)
        )
        conn.commit()
        print(f"User '{username}' created with role '{role_name}'.")
    except sqlite3.IntegrityError:
        print(f"User '{username}' already exists.")
    conn.close()


def create_role(name):
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO roles (name) VALUES (?)", (name,))
        conn.commit()
        print(f"Role '{name}' created.")
    except sqlite3.IntegrityError:
        print(f"Role '{name}' already exists.")
    conn.close()