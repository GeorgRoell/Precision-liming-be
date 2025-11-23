"""Create a new user via the API."""
import requests
import sys

# Your backend URL
BACKEND_URL = "https://nextfarming-api-545668369577.us-central1.run.app"
# Or for local testing:
# BACKEND_URL = "http://localhost:8000"

def create_user(username: str, password: str):
    """Create a new user account."""

    print("=" * 60)
    print(f"Creating user: {username}")
    print("=" * 60)

    # Call register endpoint
    response = requests.post(
        f"{BACKEND_URL}/auth/register",
        json={"username": username, "password": password}
    )

    if response.status_code == 200:
        print(f"✓ User '{username}' created successfully!")
        print(f"  Password: {password}")
        print()
        print("User can now login with these credentials.")
        return True
    else:
        print(f"✗ Failed to create user")
        print(f"  Status code: {response.status_code}")
        print(f"  Error: {response.json().get('detail', 'Unknown error')}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python create_user.py <username> <password>")
        print()
        print("Examples:")
        print('  python create_user.py john "mypassword123"')
        print('  python create_user.py farmer1 "secure_password"')
        sys.exit(1)

    username = sys.argv[1]
    password = sys.argv[2]

    create_user(username, password)
