# main.py

from fastapi import FastAPI, HTTPException, status, Depends
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from contextlib import asynccontextmanager
import json
import os
from colorama import Fore, Style, init

# Import authentication and user models from auth.py
from auth import (
    get_authenticated_user,
    hash_password,
    UserInDB,
    UserLogin,
    users_db
)

# Initialize colorama for colored console output
init(autoreset=True)

# --- Constants ---
APPLICATIONS_FILE = "applications.json"

# --- Pydantic Models for Job Applications ---
class JobApplication(BaseModel):
    """Model for a single job application."""
    job_title: str = Field(..., min_length=1)
    company: str = Field(..., min_length=1)
    date_applied: str
    status: str = Field(..., min_length=1)

# --- Mock-up Database ---
# The database will store applications per user
# Format: { "username": [JobApplication, ...] }
applications_db: Dict[str, List[JobApplication]] = {}

# --- Utility Functions for Data Persistence ---
def load_data() -> None:
    """Loads application data from a JSON file."""
    global applications_db

    if os.path.exists(APPLICATIONS_FILE):
        try:
            with open(APPLICATIONS_FILE, "r") as f:
                data = json.load(f)
                # Parse the loaded data into the correct Pydantic models
                applications_db = {
                    user: [JobApplication(**app) for app in apps]
                    for user, apps in data.items()
                }
            print(f"{Fore.GREEN}INFO: Loaded application data.{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}ERROR loading applications data: {e}{Style.RESET_ALL}")
            applications_db = {}
    
def save_data() -> None:
    """Saves application data to a JSON file."""
    try:
        with open(APPLICATIONS_FILE, "w") as f:
            # Convert Pydantic models back to dictionaries for JSON serialization
            serializable_db = {
                user: [app.model_dump() for app in apps]
                for user, apps in applications_db.items()
            }
            json.dump(serializable_db, f, indent=4)
        print(f"{Fore.GREEN}INFO: Saved application data.{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}ERROR saving data: {e}{Style.RESET_ALL}")

def create_initial_admin() -> None:
    """Creates a default admin user if one does not exist."""
    admin_username = "admin"
    admin_password = "admin_password"  
    if admin_username not in users_db:
        hashed_password = hash_password(admin_password)
        admin_user = UserInDB(
            username=admin_username,
            hashed_password=hashed_password,
            role="admin"
        )
        users_db[admin_username] = admin_user
        print(f"{Fore.YELLOW}WARNING: Default admin user '{admin_username}' created with password '{admin_password}'.{Style.RESET_ALL}")

# --- FastAPI App Lifecycle ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"{Fore.MAGENTA}Starting up...{Style.RESET_ALL}")
    load_data()
    create_initial_admin()
    yield
    print(f"{Fore.MAGENTA}Shutting down...{Style.RESET_ALL}")
    save_data()

app = FastAPI(
    title="Job Application Tracker API",
    description="An API for tracking personal job applications.",
    version="1.0.0",
    lifespan=lifespan
)

# --- API Endpoints ---
@app.post("/register/", status_code=status.HTTP_201_CREATED, summary="Register a new customer")
async def register_user(user_login: UserLogin):
    """Registers a new user with a unique username and password."""
    if user_login.username in users_db:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already registered"
        )
    
    hashed_password = hash_password(user_login.password)
    
    new_user = UserInDB(
        username=user_login.username,
        hashed_password=hashed_password,
        role="customer"
    )
    
    users_db[user_login.username] = new_user
    print(f"{Fore.GREEN}INFO: User '{user_login.username}' registered successfully.{Style.RESET_ALL}")
    
    return {"message": "Registration successful"}

@app.post("/login/", summary="Log in an existing user")
async def login(user: UserInDB = Depends(get_authenticated_user)):
    """Authenticates a user and confirms successful login."""
    print(f"{Fore.GREEN}INFO: User '{user.username}' logged in successfully.{Style.RESET_ALL}")
    return {"message": "Login successful!"}

@app.post("/applications/", status_code=status.HTTP_201_CREATED, summary="Add a new job application")
async def add_application(
    application: JobApplication,
    current_user: UserInDB = Depends(get_authenticated_user)
):
    """
    Adds a new job application to the current user's list.
    """
    # Use .model_dump() to convert the Pydantic object to a dictionary
    application_data = application.model_dump()
    
    # Get the current user's list of applications or create a new one
    user_applications = applications_db.get(current_user.username, [])
    
    user_applications.append(application)
    applications_db[current_user.username] = user_applications
    
    save_data()
    print(f"{Fore.GREEN}INFO: User '{current_user.username}' added a new application.{Style.RESET_ALL}")
    
    return {"message": "Application added successfully."}

@app.get("/applications/", response_model=List[JobApplication], summary="View all of the authenticated user's job applications")
async def get_applications(
    current_user: UserInDB = Depends(get_authenticated_user)
):
    """
    Retrieves all job applications for the currently logged-in user.
    """
    # Retrieve only the applications for the current user
    user_applications = applications_db.get(current_user.username, [])
    print(f"{Fore.GREEN}INFO: User '{current_user.username}' retrieved their applications.{Style.RESET_ALL}")
    
    return user_applications
