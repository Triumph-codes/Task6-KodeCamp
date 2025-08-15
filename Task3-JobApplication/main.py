# main.py

from fastapi import FastAPI, HTTPException, status, Depends
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from contextlib import asynccontextmanager
import json
import os
import uuid
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
LISTINGS_FILE = "job_listings.json"

# --- Pydantic Models ---
class JobListing(BaseModel):
    """Model for a job listing posted by an admin."""
    listing_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    job_title: str
    company: str
    description: str
    status: str = "open"  # Can be "open" or "closed"

class JobApplication(BaseModel):
    """Model for a user's job application."""
    application_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    listing_id: str
    job_title: str
    company: str
    date_applied: str
    status: str = "Applied"
    username: str

# --- Mock-up Databases ---
# We now store applications as a flat list
applications_db: List[JobApplication] = []

# Listings are stored by their unique ID
listings_db: Dict[str, JobListing] = {}

# --- Utility Functions for Data Persistence ---
def load_data() -> None:
    """Loads application and listing data from JSON files."""
    global applications_db, listings_db

    # Load applications
    if os.path.exists(APPLICATIONS_FILE):
        try:
            with open(APPLICATIONS_FILE, "r") as f:
                data = json.load(f)
                applications_db = [JobApplication(**app) for app in data]
            print(f"{Fore.GREEN}INFO: Loaded application data.{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}ERROR loading applications data: {e}{Style.RESET_ALL}")
            applications_db = []

    # Load listings
    if os.path.exists(LISTINGS_FILE):
        try:
            with open(LISTINGS_FILE, "r") as f:
                data = json.load(f)
                listings_db = {
                    key: JobListing(**listing)
                    for key, listing in data.items()
                }
            print(f"{Fore.GREEN}INFO: Loaded job listings.{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}ERROR loading listings data: {e}{Style.RESET_ALL}")
            listings_db = {}
    
def save_data() -> None:
    """Saves application and listing data to JSON files."""
    try:
        # Save applications
        with open(APPLICATIONS_FILE, "w") as f:
            serializable_apps = [app.model_dump() for app in applications_db]
            json.dump(serializable_apps, f, indent=4)
        print(f"{Fore.GREEN}INFO: Saved application data.{Style.RESET_ALL}")

        # Save listings
        with open(LISTINGS_FILE, "w") as f:
            serializable_listings = {
                key: listing.model_dump()
                for key, listing in listings_db.items()
            }
            json.dump(serializable_listings, f, indent=4)
        print(f"{Fore.GREEN}INFO: Saved job listings.{Style.RESET_ALL}")

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

# --- Custom Dependencies ---
def is_admin(current_user: UserInDB = Depends(get_authenticated_user)):
    """A dependency that checks if the current user is an admin."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to perform this action."
        )
    return current_user

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
    description="An API for tracking personal job applications and managing job listings.",
    version="2.0.0",
    lifespan=lifespan
)

# --- Authentication Endpoints (unchanged) ---
@app.post("/register/", status_code=status.HTTP_201_CREATED, summary="Register a new User")
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

# --- Job Listings Endpoints (Admin-only) ---
@app.post("/listings/", status_code=status.HTTP_201_CREATED, summary="[Admin] Add a new job listing")
async def add_listing(
    listing: JobListing,
    current_user: UserInDB = Depends(is_admin)
):
    """Adds a new job listing to the database. Accessible only by admins."""
    if listing.listing_id in listings_db:
         raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Listing with this ID already exists."
        )

    listings_db[listing.listing_id] = listing
    save_data()
    print(f"{Fore.GREEN}INFO: Admin '{current_user.username}' added a new listing: '{listing.job_title}'.{Style.RESET_ALL}")
    return {"message": "Listing added successfully", "listing_id": listing.listing_id}

@app.put("/listings/{listing_id}", summary="[Admin] Update a job listing")
async def update_listing(
    listing_id: str,
    updated_listing: JobListing,
    current_user: UserInDB = Depends(is_admin)
):
    """Updates an existing job listing. Accessible only by admins."""
    if listing_id not in listings_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job listing not found."
        )
    
    listings_db[listing_id] = updated_listing
    save_data()
    print(f"{Fore.GREEN}INFO: Admin '{current_user.username}' updated listing '{listing_id}'.{Style.RESET_ALL}")
    return {"message": "Listing updated successfully"}

@app.delete("/listings/{listing_id}", summary="[Admin] Delete a job listing")
async def delete_listing(
    listing_id: str,
    current_user: UserInDB = Depends(is_admin)
):
    """Deletes an existing job listing. Accessible only by admins."""
    if listing_id not in listings_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job listing not found."
        )
    
    del listings_db[listing_id]
    save_data()
    print(f"{Fore.GREEN}INFO: Admin '{current_user.username}' deleted listing '{listing_id}'.{Style.RESET_ALL}")
    return {"message": "Listing deleted successfully"}

# --- Job Listings (User and Admin) ---
@app.get("/listings/", response_model=List[JobListing], summary="View all open job listings")
async def get_listings(
    current_user: UserInDB = Depends(get_authenticated_user)
):
    """Retrieves all open job listings for a logged-in user."""
    open_listings = [
        listing for listing in listings_db.values()
        if listing.status == "open"
    ]
    print(f"{Fore.GREEN}INFO: User '{current_user.username}' viewed job listings.{Style.RESET_ALL}")
    return open_listings

@app.get("/listings/{listing_id}/applicants/", summary="[Admin] View all applicants for a job listing")
async def get_applicants(
    listing_id: str,
    current_user: UserInDB = Depends(is_admin)
):
    """Retrieves all applicants for a specific job listing. Accessible only by admins."""
    applicants = [
        app for app in applications_db
        if app.listing_id == listing_id
    ]
    if not applicants:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No applicants found for this listing."
        )
    
    print(f"{Fore.GREEN}INFO: Admin '{current_user.username}' viewed applicants for listing '{listing_id}'.{Style.RESET_ALL}")
    return {"listing_id": listing_id, "applicants": applicants}

# --- Job Applications (User-specific) ---
@app.post("/applications/", status_code=status.HTTP_201_CREATED, summary="[User] Add a new job application")
async def add_application(
    application: JobApplication,
    current_user: UserInDB = Depends(get_authenticated_user)
):
    """
    Adds a new job application for the current user, associated with a job listing.
    """
    if application.listing_id not in listings_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job listing not found."
        )

    # Ensure the user is not trying to apply for a closed job
    if listings_db[application.listing_id].status == "closed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This job listing is no longer accepting applications."
        )

    # Automatically set the username based on the authenticated user
    application.username = current_user.username
    
    applications_db.append(application)
    
    save_data()
    print(f"{Fore.GREEN}INFO: User '{current_user.username}' added a new application for listing '{application.listing_id}'.{Style.RESET_ALL}")
    
    return {"message": "Application added successfully."}

@app.get("/applications/", response_model=List[JobApplication], summary="[User] View all of your job applications")
async def get_applications(
    current_user: UserInDB = Depends(get_authenticated_user)
):
    """
    Retrieves all job applications for the currently logged-in user.
    """
    # Filter the global list of applications for the current user's username
    user_applications = [
        app for app in applications_db
        if app.username == current_user.username
    ]
    print(f"{Fore.GREEN}INFO: User '{current_user.username}' retrieved their applications.{Style.RESET_ALL}")
    
    return user_applications
