# auth.py

from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel
from typing import Dict, Optional
from decouple import config
import json
import os

# --- Constants ---
SECRET_KEY = config("SECRET_KEY")
ALGORITHM = config("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(config("ACCESS_TOKEN_EXPIRE_MINUTES"))
USERS_FILE = "users.json"

# --- Models ---
class UserInDB(BaseModel):
    """User model for storing in the database (or JSON file)."""
    username: str
    hashed_password: str

class User(BaseModel):
    """User model for public-facing data (e.g., login request)."""
    username: str
    # The password is only needed for registration, not for a public User model
    # I've updated this to only have the username and the password will be handled separately
    
class UserRegister(BaseModel):
    """Model for user registration, including a password."""
    username: str
    password: str

class Token(BaseModel):
    """Token response model."""
    access_token: str
    token_type: str = "bearer"

# --- Authentication and Hashing ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# In-memory database for users
users_db: Dict[str, UserInDB] = {}

def load_users() -> None:
    """Loads user data from a JSON file on startup."""
    global users_db
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r") as f:
                data = json.load(f)
                users_db.update({key: UserInDB(**user) for key, user in data.items()})
        except Exception as e:
            print(f"Error loading users data: {e}")

def save_users() -> None:
    """Saves user data to a JSON file."""
    try:
        with open(USERS_FILE, "w") as f:
            serializable_users = {key: user.model_dump() for key, user in users_db.items()}
            json.dump(serializable_users, f, indent=4)
    except Exception as e:
        print(f"Error saving users data: {e}")

def create_initial_user() -> None:
    """Creates a default user for testing if none exist."""
    default_username = "testuser"
    default_password = "password"
    if default_username not in users_db:
        hashed_password = pwd_context.hash(default_password)
        new_user = UserInDB(username=default_username, hashed_password=hashed_password)
        users_db[default_username] = new_user
        save_users()
        print(f"INFO: Default user '{default_username}' created with password '{default_password}'.")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Checks a plain password against a hashed one."""
    return pwd_context.verify(plain_password, hashed_password)

def get_user(username: str) -> Optional[UserInDB]:
    """Retrieves a user from the database by username."""
    return users_db.get(username)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Creates a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(token: str = Depends(oauth2_scheme)) -> UserInDB:
    """
    Dependency to get the authenticated user from a JWT token.
    Raises an HTTPException if the token is invalid or expired.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        user = get_user(username)
        if user is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    return user
