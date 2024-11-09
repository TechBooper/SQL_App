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

-- Clients Table with UNIQUE constraint to prevent duplicates
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
    FOREIGN KEY (sales_contact_id) REFERENCES users(id) ON DELETE SET NULL,
    UNIQUE (first_name, last_name, company_name)
);

-- Contracts Table with additional constraints and data type changes
CREATE TABLE contracts (
    id INTEGER PRIMARY KEY,
    client_id INTEGER NOT NULL,
    sales_contact_id INTEGER,
    total_amount DECIMAL(10, 2) NOT NULL CHECK (total_amount >= 0),
    amount_remaining DECIMAL(10, 2) NOT NULL CHECK (amount_remaining >= 0 AND amount_remaining <= total_amount),
    status TEXT NOT NULL CHECK (status IN ('Signed', 'Not Signed')),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE,
    FOREIGN KEY (sales_contact_id) REFERENCES users(id) ON DELETE SET NULL,
    UNIQUE (client_id, total_amount, status, DATE(created_at))
);

-- Events Table with UNIQUE constraint to prevent duplicates
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
    FOREIGN KEY (support_contact_id) REFERENCES users(id) ON DELETE SET NULL,
    UNIQUE (contract_id, event_date_start, event_date_end, location)
);

-- Permissions Table with constraints
CREATE TABLE permissions (
    id INTEGER PRIMARY KEY,
    role_id INTEGER NOT NULL,
    entity TEXT NOT NULL CHECK (entity IN ('client', 'contract', 'event', 'user')),
    action TEXT NOT NULL CHECK (action IN ('create', 'read', 'update', 'delete')),
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

-- Create triggers to auto-update updated_at fields using BEFORE UPDATE
-- For users table
CREATE TRIGGER update_users_updated_at
BEFORE UPDATE ON users
FOR EACH ROW
BEGIN
    SET NEW.updated_at = CURRENT_TIMESTAMP;
END;

-- For clients table
CREATE TRIGGER update_clients_updated_at
BEFORE UPDATE ON clients
FOR EACH ROW
BEGIN
    SET NEW.updated_at = CURRENT_TIMESTAMP;
END;

-- For contracts table
CREATE TRIGGER update_contracts_updated_at
BEFORE UPDATE ON contracts
FOR EACH ROW
BEGIN
    SET NEW.updated_at = CURRENT_TIMESTAMP;
END;

-- For events table
CREATE TRIGGER update_events_updated_at
BEFORE UPDATE ON events
FOR EACH ROW
BEGIN
    SET NEW.updated_at = CURRENT_TIMESTAMP;
END;

-- Create indexes on foreign key columns
CREATE INDEX idx_users_role_id ON users(role_id);
CREATE INDEX idx_clients_sales_contact_id ON clients(sales_contact_id);
CREATE INDEX idx_contracts_client_id ON contracts(client_id);
CREATE INDEX idx_contracts_sales_contact_id ON contracts(sales_contact_id);
CREATE INDEX idx_events_contract_id ON events(contract_id);
CREATE INDEX idx_events_support_contact_id ON events(support_contact_id);
