-- Roles Table
CREATE TABLE roles (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

-- Insert roles into the roles table
INSERT INTO roles (id, name) VALUES
    (1, 'Management'),
    (2, 'Commercial'),
    (3, 'Support');

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
    last_contact DATE,
    sales_contact_id INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sales_contact_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Contracts Table
CREATE TABLE contracts (
    id INTEGER PRIMARY KEY,
    client_id INTEGER NOT NULL,
    sales_contact_id INTEGER,
    total_amount REAL NOT NULL,
    amount_remaining REAL NOT NULL,
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

-- Permissions Table (For role-based access control)
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
    (1, 'client', 'read'),
    (1, 'client', 'delete'),
    (1, 'contract', 'create'),
    (1, 'contract', 'update'),
    (1, 'contract', 'read'),
    (1, 'contract', 'delete'),
    (1, 'event', 'create'),
    (1, 'event', 'update'),
    (1, 'event', 'read'),
    (1, 'event', 'delete'),
    (1, 'user', 'create'),
    (1, 'user', 'update'),
    (1, 'user', 'delete'),
    (1, 'user', 'read');

-- Insert permissions for commercial users
INSERT INTO permissions (role_id, entity, action) VALUES
    (2, 'client', 'create'),
    (2, 'client', 'update'),
    (2, 'client', 'read'),
    (2, 'contract', 'create'),
    (2, 'contract', 'update'),
    (2, 'contract', 'read'),
    (2, 'event', 'create'),
    (2, 'event', 'read');

-- Insert permissions for support users
INSERT INTO permissions (role_id, entity, action) VALUES
    (3, 'event', 'read'),
    (3, 'event', 'update'),
    (3, 'client', 'read'),
    (3, 'contract', 'read');

-- Create triggers to auto-update updated_at fields

-- For users table
CREATE TRIGGER update_users_updated_at
AFTER UPDATE ON users
FOR EACH ROW
BEGIN
    UPDATE users SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;

-- For clients table
CREATE TRIGGER update_clients_updated_at
AFTER UPDATE ON clients
FOR EACH ROW
BEGIN
    UPDATE clients SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;

-- For contracts table
CREATE TRIGGER update_contracts_updated_at
AFTER UPDATE ON contracts
FOR EACH ROW
BEGIN
    UPDATE contracts SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;

-- For events table
CREATE TRIGGER update_events_updated_at
AFTER UPDATE ON events
FOR EACH ROW
BEGIN
    UPDATE events SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;
