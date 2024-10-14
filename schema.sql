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
    email TEXT NOT NULL UNIQUE, -- Added email field for better user management
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP, -- Added timestamp for user creation
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP, -- Updated when profile changes
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE
);

-- Profiles Table
CREATE TABLE profiles (
    user_id INTEGER PRIMARY KEY,
    bio TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE -- Ensures profile is deleted when user is deleted
);

-- Clients Table
CREATE TABLE clients (
    id INTEGER PRIMARY KEY,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    phone TEXT,
    company_name TEXT,
    date_created DATE DEFAULT CURRENT_DATE, -- Automatically set date when client is created
    last_contact DATE, 
    sales_contact_id INTEGER NOT NULL,
    FOREIGN KEY (sales_contact_id) REFERENCES users(id) ON DELETE SET NULL, -- If sales contact is deleted, set NULL
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP, -- Added creation timestamp
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP -- Added last update timestamp
);

-- Contracts Table
CREATE TABLE contracts (
    id INTEGER PRIMARY KEY,
    client_id INTEGER NOT NULL,
    sales_contact_id INTEGER NOT NULL,
    total_amount REAL NOT NULL,
    amount_remaining REAL NOT NULL,
    date_created DATE DEFAULT CURRENT_DATE, -- Automatically set the contract creation date
    status TEXT NOT NULL CHECK (status IN ('Signed', 'Not Signed')), -- Added status validation
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE, -- If client is deleted, delete contract
    FOREIGN KEY (sales_contact_id) REFERENCES users(id) ON DELETE SET NULL, -- If sales contact is deleted, set to NULL
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP, -- Added creation timestamp
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP -- Added last update timestamp
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
    FOREIGN KEY (contract_id) REFERENCES contracts(id) ON DELETE CASCADE, 
    FOREIGN KEY (support_contact_id) REFERENCES users(id) ON DELETE SET NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP 
);

-- Permissions Table (Optional: For role-based access control)
CREATE TABLE permissions (
    id INTEGER PRIMARY KEY,
    role_id INTEGER NOT NULL,
    permission TEXT NOT NULL, -- e.g., 'can_edit_clients', 'can_view_events'
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE
);


-- Insert permissions for management
INSERT INTO permissions (role_id, entity, action) VALUES
(1, 'client', 'create'),     -- Management can create clients
(1, 'client', 'update'),     -- Management can update clients
(1, 'contract', 'create'),   -- Management can create contracts
(1, 'contract', 'update'),   -- Management can update contracts
(1, 'event', 'create'),      -- Management can create events
(1, 'event', 'update');      -- Management can update events

-- Insert permissions for commercial users
INSERT INTO permissions (role_id, entity, action) VALUES
(2, 'client', 'create'),   -- Commercial users can create clients
(2, 'client', 'update'),   -- Commercial users can update clients they own
(2, 'contract', 'create'), -- Commercial users can create contracts for their clients
(2, 'contract', 'update'); -- Commercial users can update contracts for their clients

-- Insert permissions for support users
INSERT INTO permissions (role_id, entity, action) VALUES
(3, 'event', 'read'),      -- Support users can view assigned events
(3, 'event', 'update');    -- Support users can update assigned events
