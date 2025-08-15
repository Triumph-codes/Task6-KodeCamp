# main.py

from fastapi import FastAPI, HTTPException, status, Depends, Body
from pydantic import BaseModel, Field
from typing import List, Dict
from datetime import datetime, timedelta, timezone
import json
import os
import uuid
from colorama import init, Fore, Style

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

class NoteUpdate(BaseModel):
    """Pydantic model for updating a note (all fields are optional)."""
    title: str | None = None
    content: str | None = None


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
            print(f"{Fore.RED}Error loading notes data: {e}{Style.RESET_ALL}")

def save_notes() -> None:
    """Saves notes data to a JSON file."""
    try:
        with open(NOTES_FILE, "w") as f:
            serializable_notes = {
                username: [note.model_dump(mode='json') for note in notes]
                for username, notes in notes_db.items()
            }
            json.dump(serializable_notes, f, indent=4)
        print(f"{Fore.GREEN}INFO: Notes data saved successfully.{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}Error saving notes data: {e}{Style.RESET_ALL}")

# --- FastAPI App Lifecycle ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Function to run on app startup and shutdown.
    Loads data and creates a default user on startup.
    """
    init() # Initialize colorama
    print(f"{Fore.CYAN}Starting up...{Style.RESET_ALL}")
    load_users()
    create_initial_user()
    load_notes()
    yield
    print(f"{Fore.CYAN}Shutting down...{Style.RESET_ALL}")
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


@app.get("/notes/{note_id}", response_model=Note, summary="View a single note by ID")
async def get_single_note(
    note_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Retrieves a single note for the authenticated user by its ID.
    Raises 404 if the note is not found or does not belong to the user.
    """
    user_notes = notes_db.get(current_user.username, [])
    for note in user_notes:
        if note.note_id == note_id:
            return note
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Note not found."
    )

@app.put("/notes/{note_id}", response_model=Note, summary="Update an existing note")
async def update_note(
    note_id: str,
    note_update: NoteUpdate,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Updates an existing note for the authenticated user.
    Raises 404 if the note is not found or does not belong to the user.
    """
    user_notes = notes_db.get(current_user.username, [])
    for i, note in enumerate(user_notes):
        if note.note_id == note_id:
            if note_update.title:
                note.title = note_update.title
            if note_update.content:
                note.content = note_update.content
            notes_db[current_user.username][i] = note
            save_notes()
            return note
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Note not found."
    )

@app.delete("/notes/{note_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a note by ID")
async def delete_note(
    note_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Deletes a single note for the authenticated user by its ID.
    Raises 404 if the note is not found or does not belong to the user.
    """
    user_notes = notes_db.get(current_user.username, [])
    # Find the note index and remove it
    for i, note in enumerate(user_notes):
        if note.note_id == note_id:
            del notes_db[current_user.username][i]
            save_notes()
            return
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Note not found."
    )