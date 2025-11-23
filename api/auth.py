from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext

from config.settings import settings
from models.schemas import Token, UserLogin, User

router = APIRouter()
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Temporary user database (replace with real database later)
# NOTE: Passwords are now hashed with bcrypt for security!
# To generate a new hashed password: get_password_hash("your_password")
fake_users_db = {
    "demo": {
        "username": "demo",
        "hashed_password": "$2b$12$a9V23LSohqUhat7Rm9easOBvYyOIKLsxv1XnQHkve24Y1Lvge/zO6",  # demo123
        "email": "demo@omya.com",
        "disabled": False,
    },
    "admin": {
        "username": "admin",
        "hashed_password": "$2b$12$005NY.0Jyk4FvC4IeE9c6.A56ij4id08Qr8uO7TRs9EJ02I0iH1Ze",  # admin123
        "email": "admin@omya.com",
        "disabled": False,
    },
    "next": {
        "username": "next",
        "hashed_password": "$2b$12$nlSBHNO12vo2aF04aMAge.1Uu0e51hwOWBCgBP2r6Q4R.dB51HPjm",  # next123
        "email": "next@omya.com",
        "disabled": False,
    },
    "local": {
        "username": "local",
        "hashed_password": "$2b$12$DcTOKVtUvJxgGH.wQBxQIe1dFv9cqXC3RY7BGaOdIHXJ33BZMAhK2",  # local123
        "email": "local@omya.com",
        "disabled": False,
    }
}


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password for storing."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    Dependency to verify JWT token and get current user.
    Use this in endpoints that require authentication.
    """
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = fake_users_db.get(username)
    if user is None:
        raise credentials_exception

    if user.get("disabled"):
        raise HTTPException(status_code=400, detail="Inactive user")

    return user


@router.post("/login", response_model=Token)
async def login(user_login: UserLogin):
    """
    Login endpoint - returns JWT token for client to use.

    The desktop/web app uses this token for all subsequent API calls.

    Example:
        POST /auth/login
        {
            "username": "demo",
            "password": "demo123"
        }

        Returns:
        {
            "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
            "token_type": "bearer"
        }
    """
    user = fake_users_db.get(user_login.username)

    # Verify password using bcrypt hashing
    if not user or not verify_password(user_login.password, user.get("hashed_password")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user.get("disabled"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )

    access_token = create_access_token(data={"sub": user_login.username})

    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=User)
async def read_users_me(current_user: dict = Depends(get_current_user)):
    """
    Get current user info.

    Requires authentication (Bearer token in Authorization header).

    Example:
        GET /auth/me
        Headers: Authorization: Bearer <token>

        Returns:
        {
            "username": "demo",
            "email": "demo@omya.com",
            "disabled": false
        }
    """
    return User(
        username=current_user["username"],
        email=current_user.get("email"),
        disabled=current_user.get("disabled", False)
    )


@router.post("/register")
async def register(user_login: UserLogin):
    """
    Register a new user (simple version - replace with proper user management).

    Example:
        POST /auth/register
        {
            "username": "newuser",
            "password": "securepassword"
        }
    """
    if user_login.username in fake_users_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    # Hash password before storing using bcrypt
    fake_users_db[user_login.username] = {
        "username": user_login.username,
        "hashed_password": get_password_hash(user_login.password),
        "email": f"{user_login.username}@omya.com",
        "disabled": False
    }

    return {"message": "User registered successfully", "username": user_login.username}
