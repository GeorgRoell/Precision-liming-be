"""User management script for backend authentication."""
import sys

# Add the backend directory to the path
sys.path.insert(0, 'C:\\Users\\georg\\nextfarming-backend')

from api.auth import fake_users_db, get_password_hash
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def list_users():
    """List all users in the database."""
    print("=" * 60)
    print("CURRENT USERS")
    print("=" * 60)
    print()

    if not fake_users_db:
        print("No users in database.")
        return

    for username, user_data in fake_users_db.items():
        print(f"Username: {username}")
        print(f"  Email: {user_data.get('email', 'N/A')}")
        print(f"  Disabled: {user_data.get('disabled', False)}")
        print(f"  Has hashed password: {'hashed_password' in user_data}")
        print()


def add_user(username: str, password: str, email: str = None):
    """Add a new user to the database."""
    print("=" * 60)
    print(f"ADDING NEW USER: {username}")
    print("=" * 60)
    print()

    if username in fake_users_db:
        print(f"✗ Error: User '{username}' already exists!")
        return False

    # Generate password hash
    hashed_password = get_password_hash(password)

    # Create user entry
    user_data = {
        "username": username,
        "hashed_password": hashed_password,
        "email": email or f"{username}@omya.com",
        "disabled": False
    }

    # Add to database
    fake_users_db[username] = user_data

    print(f"✓ User '{username}' created successfully!")
    print()
    print("Add this to your api/auth.py file:")
    print("-" * 60)
    print(f'    "{username}": {{')
    print(f'        "username": "{username}",')
    print(f'        "hashed_password": "{hashed_password}",  # {password}')
    print(f'        "email": "{user_data["email"]}",')
    print(f'        "disabled": False,')
    print(f'    }},')
    print("-" * 60)
    print()
    print("⚠️  IMPORTANT: This change is only in memory!")
    print("    You must manually copy the above code to api/auth.py")
    print("    Then redeploy the backend with: deploy-simple.bat")
    print()

    return True


def generate_hash(password: str):
    """Generate a bcrypt hash for a password."""
    print("=" * 60)
    print("PASSWORD HASH GENERATOR")
    print("=" * 60)
    print()
    print(f"Password: {password}")
    print()

    hashed = get_password_hash(password)
    print(f"Bcrypt hash:")
    print(f'  "{hashed}"')
    print()
    print("Copy this hash to your fake_users_db in api/auth.py")
    print()


def verify_credentials(username: str, password: str):
    """Test if credentials work."""
    print("=" * 60)
    print("TESTING CREDENTIALS")
    print("=" * 60)
    print()

    user = fake_users_db.get(username)
    if not user:
        print(f"✗ User '{username}' not found")
        return False

    hashed = user.get("hashed_password")
    if not hashed:
        print(f"✗ User '{username}' has no hashed password!")
        return False

    result = pwd_context.verify(password, hashed)

    if result:
        print(f"✓ Credentials are VALID")
        print(f"  Username: {username}")
        print(f"  Password: {password}")
        print(f"  Email: {user.get('email')}")
    else:
        print(f"✗ Password is INCORRECT for user '{username}'")

    print()
    return result


def main():
    """Main menu."""
    if len(sys.argv) < 2:
        print("=" * 60)
        print("USER MANAGEMENT TOOL")
        print("=" * 60)
        print()
        print("Usage:")
        print("  python manage_users.py list")
        print("  python manage_users.py add <username> <password> [email]")
        print("  python manage_users.py hash <password>")
        print("  python manage_users.py verify <username> <password>")
        print()
        print("Examples:")
        print('  python manage_users.py list')
        print('  python manage_users.py add john "mypass123" "john@omya.com"')
        print('  python manage_users.py hash "newpassword"')
        print('  python manage_users.py verify demo demo123')
        print()
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "list":
        list_users()

    elif command == "add":
        if len(sys.argv) < 4:
            print("Error: Missing arguments")
            print('Usage: python manage_users.py add <username> <password> [email]')
            sys.exit(1)

        username = sys.argv[2]
        password = sys.argv[3]
        email = sys.argv[4] if len(sys.argv) > 4 else None

        add_user(username, password, email)

    elif command == "hash":
        if len(sys.argv) < 3:
            print("Error: Missing password")
            print('Usage: python manage_users.py hash <password>')
            sys.exit(1)

        password = sys.argv[2]
        generate_hash(password)

    elif command == "verify":
        if len(sys.argv) < 4:
            print("Error: Missing arguments")
            print('Usage: python manage_users.py verify <username> <password>')
            sys.exit(1)

        username = sys.argv[2]
        password = sys.argv[3]
        verify_credentials(username, password)

    else:
        print(f"Unknown command: {command}")
        print("Valid commands: list, add, hash, verify")
        sys.exit(1)


if __name__ == "__main__":
    main()
