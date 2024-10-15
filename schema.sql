-- Roles Table
CREATE TABLE roles (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

-- Users Table
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role_id INTEGER NOT NULL,
    email TEXT NOT NULL UNIQUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE
);

-- Profiles Table
CREATE TABLE profiles (
    user_id INTEGER PRIMARY KEY,
    bio TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Clients Table
CREATE TABLE clients (
    id INTEGER PRIMARY KEY,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    phone TEXT,
    company_name TEXT,
    date_created DATE DEFAULT (CURRENT_DATE),
    last_contact DATE,
    sales_contact_id INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sales_contact_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Contracts Table
CREATE TABLE contracts (
    id INTEGER PRIMARY KEY,
    client_id INTEGER NOT NULL,
    sales_contact_id INTEGER NOT NULL,
    total_amount REAL NOT NULL,
    amount_remaining REAL NOT NULL,
    date_created DATE DEFAULT (CURRENT_DATE),
    status TEXT NOT NULL CHECK (status IN ('Signed', 'Not Signed')),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE,
    FOREIGN KEY (sales_contact_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Events Table
CREATE TABLE events (
    id INTEGER PRIMARY KEY,
    contract_id INTEGER NOT NULL,
    support_contact_id INTEGER,
    event_date_start DATETIME NOT NULL,
    event_date_end DATETIME NOT NULL,
    location TEXT,
    attendees INTEGER,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (contract_id) REFERENCES contracts(id) ON DELETE CASCADE,
    FOREIGN KEY (support_contact_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Permissions Table (Optional: For role-based access control)
CREATE TABLE permissions (
    id INTEGER PRIMARY KEY,
    role_id INTEGER NOT NULL,
    entity TEXT NOT NULL,
    action TEXT NOT NULL,
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE
);

-- Insert permissions for management
INSERT INTO permissions (role_id, entity, action) VALUES
    (1, 'client', 'create'),
    (1, 'client', 'update'),
    (1, 'contract', 'create'),
    (1, 'contract', 'update'),
    (1, 'event', 'create'),
    (1, 'event', 'update');

-- Insert permissions for commercial users
INSERT INTO permissions (role_id, entity, action) VALUES
    (2, 'client', 'create'),
    (2, 'client', 'update'),
    (2, 'contract', 'create'),
    (2, 'contract', 'update');

-- Insert permissions for support users
INSERT INTO permissions (role_id, entity, action) VALUES
    (3, 'event', 'read'),
    (3, 'event', 'update');
