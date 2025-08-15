# main.py

from fastapi import FastAPI, HTTPException, status, Depends, Body
from pydantic import BaseModel, Field
from typing import List, Dict
from datetime import datetime, timedelta, timezone
import json
import os
import uuid

# Import authentication functions and models from auth.py
from auth import (
    get_current_user,
    UserInDB,
    load_users,
    create_initial_user,
    Token,
    verify_password,
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    pwd_context,
    get_user,
    save_users,
    users_db,
    UserRegister
)
from fastapi.security import OAuth2PasswordRequestForm
from contextlib import asynccontextmanager

# --- Constants ---
NOTES_FILE = "notes.json"

# --- Models ---
class Note(BaseModel):
    """Pydantic model for a single note."""
    note_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    content: str
    date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class NoteCreate(BaseModel):
    """Pydantic model for creating a new note (only requires title and content)."""
    title: str
    content: str

# In-memory database for notes, structured by username
notes_db: Dict[str, List[Note]] = {}

# --- Utility Functions for Data Persistence ---
def load_notes() -> None:
    """Loads notes data from a JSON file."""
    global notes_db
    if os.path.exists(NOTES_FILE):
        try:
            with open(NOTES_FILE, "r") as f:
                data = json.load(f)
                # Convert date strings back to datetime objects
                for username, notes in data.items():
                    notes_db[username] = [Note(**note) for note in notes]
        except Exception as e:
            print(f"Error loading notes data: {e}")

def save_notes() -> None:
    """Saves notes data to a JSON file."""
    try:
        with open(NOTES_FILE, "w") as f:
            serializable_notes = {
                username: [note.model_dump(mode='json') for note in notes]
                for username, notes in notes_db.items()
            }
            json.dump(serializable_notes, f, indent=4)
    except Exception as e:
            print(f"Error saving notes data: {e}")

# --- FastAPI App Lifecycle ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Function to run on app startup and shutdown.
    Loads data and creates a default user on startup.
    """
    print("Starting up...")
    load_users()
    create_initial_user()
    load_notes()
    yield
    print("Shutting down...")
    save_notes()
    save_users()


app = FastAPI(title="Notes API with JWT Auth", lifespan=lifespan)

# --- Authentication Endpoints ---
@app.post("/register/", status_code=status.HTTP_201_CREATED, summary="Register a new user")
async def register_user(user: UserRegister):
    """Registers a new user."""
    if get_user(user.username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already registered"
        )
    hashed_password = pwd_context.hash(user.password)
    new_user = UserInDB(username=user.username, hashed_password=hashed_password)
    users_db[user.username] = new_user
    save_users()
    return {"message": "Registration successful"}

@app.post("/login/", response_model=Token, summary="Login and get a JWT token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """Logs in a user and returns a JWT access token."""
    user = get_user(form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# --- Notes Management Endpoints (Secure) ---
@app.post("/notes/", status_code=status.HTTP_201_CREATED, summary="Add a new note for the current user")
async def add_note(
    note_create: NoteCreate,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Adds a new note for the authenticated user.
    Requires a valid JWT token in the Authorization header.
    """
    new_note = Note(title=note_create.title, content=note_create.content)
    
    # Get or create the user's notes list
    if current_user.username not in notes_db:
        notes_db[current_user.username] = []
    
    notes_db[current_user.username].append(new_note)
    save_notes()
    
    return {"message": "Note added successfully", "note_id": new_note.note_id}

@app.get("/notes/", response_model=List[Note], summary="View all notes for the current user")
async def get_notes(
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Retrieves all notes belonging to the authenticated user.
    Requires a valid JWT token in the Authorization header.
    """
    # Return the user's notes, or an empty list if they have none
    return notes_db.get(current_user.username, [])