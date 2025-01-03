/*
This database schema sets up a foundation for Epic Events CRM, similar to the previous design, but simplified to avoid any SQLite-specific pitfalls. The logic and constraints remain effectively the same, but we’ll use standard SQLite-compatible syntax.

Changes from previous attempts:
- No "IF NOT EXISTS" for triggers.
- No "SET" keyword in triggers.
- Using standard SQLite-compatible data types and syntax.
- Decimals will be stored as REAL because SQLite doesn’t have a DECIMAL type; checks remain to ensure valid values.
- Ensuring all columns and constraints are compatible with SQLite.

This schema uses:
- Roles, Users, Clients, Contracts, Events, Permissions tables.
- Triggers to auto-update updated_at on update.
- Indexes on foreign key columns.

We will rely on REAL for amounts since SQLite stores numeric values as REAL; checks still enforce numeric constraints.
*/

-- Roles Table
CREATE TABLE IF NOT EXISTS roles   (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT PRIMARY KEY
);

INSERT INTO roles (name) VALUES 
    ('Management'),
    ('Commercial'),
    ('Support');

-- Users Table
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    password_hash TEXT NOT NULL,
    role_id TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (role_id) REFERENCES roles(name)
);

-- Profiles Table
CREATE TABLE IF NOT EXISTS profiles  (
    user_id TEXT PRIMARY KEY,
    bio TEXT,
    FOREIGN KEY (user_id) REFERENCES users(username)
);

-- Clients Table
CREATE TABLE IF NOT EXISTS clients  (
    email TEXT PRIMARY KEY,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    phone TEXT,
    company_name TEXT,
    last_contact TEXT, -- SQLite date
    sales_contact_id TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (sales_contact_id) REFERENCES users(username),
    UNIQUE (first_name, last_name, company_name)
);

-- Contracts Table
CREATE TABLE IF NOT EXISTS contracts  (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id TEXT NOT NULL,
    sales_contact_id TEXT,
    total_amount REAL NOT NULL CHECK (total_amount >= 0),
    amount_remaining REAL NOT NULL CHECK (amount_remaining >= 0),
    status TEXT NOT NULL CHECK (status IN ('Signed', 'Not Signed')),
    date_created TEXT DEFAULT (date('now')),
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    CHECK (amount_remaining <= total_amount),
    FOREIGN KEY (client_id) REFERENCES clients(email),
    FOREIGN KEY (sales_contact_id) REFERENCES users(username)
);

-- Events Table
CREATE TABLE IF NOT EXISTS events  (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_id INTEGER NOT NULL,
    support_contact_id TEXT,
    event_date_start TEXT NOT NULL,
    event_date_end TEXT NOT NULL,
    location TEXT,
    attendees INTEGER,
    notes TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (contract_id) REFERENCES contracts(id),
    FOREIGN KEY (support_contact_id) REFERENCES users(username)
);

-- Permissions Table
CREATE TABLE IF NOT EXISTS permissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role_id TEXT NOT NULL,
    entity TEXT NOT NULL,
    action TEXT NOT NULL,
    FOREIGN KEY (role_id) REFERENCES roles(name),
    CHECK (entity IN ('client', 'contract', 'event', 'user')),
    CHECK (action IN ('create', 'read', 'update', 'delete'))
);

-- Insert Management Permissions
INSERT INTO permissions (role_id, entity, action) VALUES
    ('Management', 'client', 'create'),
    ('Management', 'client', 'read'),
    ('Management', 'client', 'update'),
    ('Management', 'client', 'delete'),
    ('Management', 'contract', 'create'),
    ('Management', 'contract', 'read'),
    ('Management', 'contract', 'update'),
    ('Management', 'contract', 'delete'),
    ('Management', 'event', 'create'),
    ('Management', 'event', 'read'),
    ('Management', 'event', 'update'),
    ('Management', 'event', 'delete'),
    ('Management', 'user', 'create'),
    ('Management', 'user', 'read'),
    ('Management', 'user', 'update'),
    ('Management', 'user', 'delete');

-- Insert Commercial Permissions
INSERT INTO permissions (role_id, entity, action) VALUES
    ('Commercial', 'client', 'create'),
    ('Commercial', 'client', 'read'),
    ('Commercial', 'client', 'update'),
    ('Commercial', 'contract', 'create'),
    ('Commercial', 'contract', 'read'),
    ('Commercial', 'contract', 'update'),
    ('Commercial', 'event', 'create'),
    ('Commercial', 'event', 'read');

-- Insert Support Permissions
INSERT INTO permissions (role_id, entity, action) VALUES
    ('Support', 'event', 'read'),
    ('Support', 'event', 'update'),
    ('Support', 'client', 'read'),
    ('Support', 'contract', 'read');

-- Create indexes for better performance
CREATE INDEX idx_users_role ON users(role_id);
CREATE INDEX idx_clients_sales_contact ON clients(sales_contact_id);
CREATE INDEX idx_contracts_client ON contracts(client_id);
CREATE INDEX idx_contracts_sales_contact ON contracts(sales_contact_id);
CREATE INDEX idx_events_contract ON events(contract_id);
CREATE INDEX idx_events_support_contact ON events(support_contact_id);

-- Create triggers for updated_at timestamps
CREATE TRIGGER users_updated_at_trigger 
    AFTER UPDATE ON users
BEGIN
    UPDATE users SET updated_at = datetime('now')
    WHERE username = NEW.username;
END;

CREATE TRIGGER clients_updated_at_trigger
    AFTER UPDATE ON clients
BEGIN
    UPDATE clients SET updated_at = datetime('now')
    WHERE email = NEW.email;
END;

CREATE TRIGGER contracts_updated_at_trigger
    AFTER UPDATE ON contracts
BEGIN
    UPDATE contracts SET updated_at = datetime('now')
    WHERE id = NEW.id;
END;

CREATE TRIGGER events_updated_at_trigger
    AFTER UPDATE ON events
BEGIN
    UPDATE events SET updated_at = datetime('now')
    WHERE id = NEW.id;
END;