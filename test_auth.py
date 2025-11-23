"""Test authentication directly."""
import sys
sys.path.insert(0, 'C:\\Users\\georg\\nextfarming-backend')

from api.auth import fake_users_db, verify_password

print("=" * 60)
print("TESTING AUTHENTICATION")
print("=" * 60)
print()

# Check what's in the database
demo_user = fake_users_db.get("demo")
print("Demo user data:")
print(f"  Username: {demo_user.get('username')}")
print(f"  Hashed password: {demo_user.get('hashed_password')}")
print(f"  Email: {demo_user.get('email')}")
print()

# Try to verify password
test_password = "demo123"
hashed = demo_user.get("hashed_password")

print(f"Testing password: {test_password}")
print(f"Against hash: {hashed}")
print()

try:
    result = verify_password(test_password, hashed)
    print(f"✓ Password verification result: {result}")
except Exception as e:
    print(f"✗ Error during verification: {e}")

print()
print("=" * 60)
