# Epic Events CRM CLI Application

This is a Command-Line Interface (CLI) application for managing customer relationships at Epic Events, an event management company. The application allows users to manage clients, contracts, events, and users with role-based access control, only through a command terminal.

# Features

- User Authentication: Secure login and password hashing using bcrypt.
- Role-Based Access Control: Users have roles (Management, Commercial, Support) with specific permissions.
- Client Management: Create, update, delete, and view clients.
- Contract Management: Manage contracts associated with clients.
- Event Management: Schedule and manage events tied to contracts.
- User Management: Admin users can create, update, and delete user accounts.
- Database Initialization: Automatically creates and initializes the SQLite database.
- Logging: Logs operations and errors to log files.
- Error Tracking: Integrated with Sentry for error monitoring.

# Installation

1. Clone the Repository

`git clone https://github.com/epic-events/epic-events-cli.git`

2. Set up virtual env

`python -m venv venv`
`source venv/bin/activate`  # Windows: venv\Scripts\activate

2. Install Dependencies

`pip install -r requirements.txt`

3. Initialize the Database

Run the database.py script to create and initialize the SQLite database by inputting:

`python database.py`

# Usage

Run the CLI application using:

`python cli.py`

# Available Actions

Profile Management:

awView Profile: View your user profile information.
Update Profile: Update your email address.

User Management (Management Role Only)

Create User: Add a new user to the system.
Update User: Modify an existing user's information.
Delete User: Remove a user from the system.

Client Management

View Clients: Display a list of all clients.
Create Client: Add a new client.
Update Client: Modify an existing client's information.
Delete Client: Remove a client from the system (Management role only).

Contract Management

View Contracts: Display a list of all contracts.
Create Contract: Add a new contract.
Update Contract: Modify an existing contract.
Delete Contract: Remove a contract from the system (Management role only).
Filter Contracts by Status: View contracts filtered by 'Signed' or 'Not Signed' status.

Event Management

View Events: Display a list of all events.
Create Event: Schedule a new event.
Update Event: Modify an existing event.
Delete Event: Remove an event from the system (Management role only).
Assign Support to Event: Assign a support user to an event (Management role only).
Filter Unassigned Events: View events without assigned support (Non-support roles).
View Events Assigned to Me: Support users can view events assigned to them.

Notes

Permissions: The options available to you in the menus depend on your user role and permissions.
Validation: The application validates your inputs and provides feedback if there's an error.
Logging: Operations are logged for auditing purposes.

Troubleshooting

Database Not Found: If you receive a "Database not found" error, ensure you've initialized the database by running python database.py.
Permission Denied: If you attempt to access a feature you don't have permissions for, the application will notify you.

Logging Out

To log out of the application, select the 'Logout' option from the main menu.