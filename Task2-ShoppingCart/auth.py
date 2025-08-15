# auth.py

from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from typing import Dict, Optional
from passlib.context import CryptContext

# --- Pydantic Models for Authentication ---
class UserBase(BaseModel):
    """Base user model."""
    username: str
    role: str = "customer"

class UserInDB(UserBase):
    """User model with hashed password, used for storing in the database."""
    hashed_password: str

class UserLogin(BaseModel):
    """Model for user registration and login."""
    username: str
    password: str

# --- Password Hashing and Security ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBasic()

def hash_password(password: str) -> str:
    """Hashes a plain-text password using bcrypt."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain-text password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)

# --- Database Mock-up ---
# This dictionary will act as our in-memory user database.
users_db: Dict[str, UserInDB] = {}

def get_users_db() -> Dict[str, UserInDB]:
    """Dependency to provide access to the user database."""
    return users_db

# --- Dependency Injection Functions ---
def get_authenticated_user(
    credentials: HTTPBasicCredentials = Depends(security),
    db: Dict[str, UserInDB] = Depends(get_users_db)
) -> UserInDB:
    """
    Authenticates a user based on HTTP Basic credentials.
    Returns the user object if successful, otherwise raises an HTTPException.
    """
    user = db.get(credentials.username)
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    return user

def get_current_admin(user: UserInDB = Depends(get_authenticated_user)) -> UserInDB:
    """
    Dependency that authenticates a user and checks if they have the 'admin' role.
    Raises an HTTPException if the user is not an admin.
    """
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to perform this action."
        )
    return user
