# cli.py
import argparse
from auth import authenticate, get_user_role
from profile import view_profile, update_profile
import sentry_setup

def main():
    parser = argparse.ArgumentParser(description="Application CLI")
    subparsers = parser.add_subparsers(dest='command')

    # Login Command
    login_parser = subparsers.add_parser('login')
    login_parser.add_argument('username')
    login_parser.add_argument('password')

    # View Profile Command
    view_parser = subparsers.add_parser('view_profile')

    # Update Profile Command
    update_parser = subparsers.add_parser('update_profile')
    update_parser.add_argument('bio')

    # Additional Commands as Needed...

    args = parser.parse_args()
    session = {}

    if args.command == 'login':
        user = authenticate(args.username, args.password)
        if user:
            session['user_id'] = user['user_id']
            session['role'] = get_user_role(user['user_id'])
            print(f"Logged in as {args.username} with role {session['role']}.")
        else:
            print("Authentication failed.")
    elif args.command == 'view_profile':
        if 'user_id' in session:
            view_profile(session['user_id'])
        else:
            print("Please log in first.")
    elif args.command == 'update_profile':
        if 'user_id' in session:
            update_profile(session['user_id'], args.bio)
        else:
            print("Please log in first.")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
