"""Generate bcrypt password hashes for users."""
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Generate hashes for demo users
demo_hash = pwd_context.hash("demo123")
admin_hash = pwd_context.hash("admin123")

print("=" * 60)
print("GENERATED PASSWORD HASHES")
print("=" * 60)
print()
print("Demo user:")
print(f'    "hashed_password": "{demo_hash}",  # demo123')
print()
print("Admin user:")
print(f'    "hashed_password": "{admin_hash}",  # admin123')
print()
print("=" * 60)
print()

# Verify they work
print("Verification tests:")
print(f"  demo123 with demo hash: {pwd_context.verify('demo123', demo_hash)}")
print(f"  admin123 with admin hash: {pwd_context.verify('admin123', admin_hash)}")
print()
