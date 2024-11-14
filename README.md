#Epic Events CRM CLI Application

This is a Command-Line Interface (CLI) application for managing customer relationships at Epic Events, an event management company. The application allows users to manage clients, contracts, events, and users with role-based access control, only through a command terminal.

#Features

-User Authentication: Secure login and password hashing using bcrypt.
-Role-Based Access Control: Users have roles (Management, Commercial, Support) with specific permissions.
-Client Management: Create, update, delete, and view clients.
-Contract Management: Manage contracts associated with clients.
-Event Management: Schedule and manage events tied to contracts.
-User Management: Admin users can create, update, and delete user accounts.
-Database Initialization: Automatically creates and initializes the SQLite database.
-Logging: Logs operations and errors to log files.
-Error Tracking: Integrated with Sentry for error monitoring.

#Installation

1. Clone the Repository

'git clone https://github.com/yourusername/epic-events-cli.git'
'cd epic-events-cli'

2. Create a Virtual Environment

'python -m venv venv'

3. Install Dependencies

'pip install -r requirements.txt'

4. Initialize the Database

Run the database.py script to create and initialize the SQLite database by inputting:

'python database.py'


#Usage

Run the CLI application using:

python cli.py login <username>

Here's a compilation of the commands:

#Commands

Once logged in, you can use the following commands:

User Commands:

view_profile: View your user profile.
update_profile <email>: Update your email address.
create_user <username> <role_id> <email>: Create a new user (Management only).
update_user <user_id> <username> <email> <role_id>: Update a user's information (Management only).
delete_user <user_id>: Delete a user (Management only).
Client Commands:

create_client <first_name> <last_name> <email> <phone> <company_name>: Create a new client.
update_client <client_id> <first_name> <last_name> <email> <phone> <company_name>: Update client information.
delete_client <client_id>: Delete a client (Management only).
view_clients: View all clients.
Contract Commands:

create_contract <client_id> <total_amount> <amount_remaining> <status>: Create a new contract.
update_contract <contract_id> <total_amount> <amount_remaining> <status>: Update a contract.
delete_contract <contract_id>: Delete a contract (Management only).
view_contracts: View all contracts.
filter_contracts <status>: View contracts filtered by status.

Event Commands:

create_event <contract_id> <event_date_start> <event_date_end> <location> <attendees> <notes>: Create a new event.
update_event <event_id> <event_date_start> <event_date_end> <location> <attendees> <notes>: Update an event.
delete_event <event_id>: Delete an event (Management only).
assign_support <event_id> <support_user_id>: Assign a support user to an event (Management only).
view_events: View all events.
filter_events_unassigned: View events without assigned support.
filter_events_assigned_to_me: View events assigned to you (Support role).

Additional Commands:

help: Display available commands.
logout: Log out of the application.
