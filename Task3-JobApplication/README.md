Job Application Tracker API
This is a comprehensive FastAPI application designed to manage job listings and track user applications. It provides a secure, role-based system for both regular users and administrators, with data persistence handled by local JSON files.

Features
User Authentication: Secure user registration and login with hashed passwords.

Role-Based Access Control (RBAC): Differentiates between customer and admin roles, restricting certain endpoints to administrators.

Job Listings: Admins can create, update, and delete job postings. All authenticated users can view active job listings.

Job Applications: Authenticated users can apply for jobs by providing only a listing_id and date_applied. The API automatically populates the remaining details, ensuring data accuracy.

Admin Applicant Management: Admins can view all applicants for a specific job listing with powerful filtering, sorting, and pagination options.

Data Persistence: All user, job listing, and application data is saved to local JSON files (users.json, job_listings.json, applications.json) to ensure persistence across server restarts.

Informative Logging: The API provides colorful and detailed logs on startup and shutdown.

Setup and Installation
Prerequisites: Ensure you have Python 3.8+ installed.

Install dependencies:

pip install fastapi "uvicorn[standard]" passlib[bcrypt] python-multipart colorama

Run the API:

uvicorn main:app --reload

The API will be running at http://127.0.0.1:8000. You can access the interactive API documentation at http://127.0.0.1:8000/docs.

Admin Access
For testing administrative endpoints, the API is configured to create a default admin user on startup if one doesn't already exist.

Default Credentials:

Username: admin

Password: admin_password

You can use these credentials to access all admin-only endpoints, such as adding a new job listing or viewing applicant reports.

API Endpoints
This table provides a summary of all available API endpoints and their access requirements.

Method

Endpoint

Description

Authentication Required

POST

/register/

Register a new user.

No

POST

/login/

Authenticate a user and receive a success message.

No

GET

/listings/

View all open job listings.

User

POST

/listings/

Add a new job listing.

Admin Only

PUT

/listings/{listing_id}

Update an existing job listing.

Admin Only

DELETE

/listings/{listing_id}

Delete a job listing.

Admin Only

POST

/applications/

Submit a new job application.

User

GET

/applications/

Retrieve all job applications for the logged-in user.

User

GET

/listings/{listing_id}/applicants/

View applicants for a listing with filtering and pagination.

Admin Only

Project Structure
/job-application-tracker
├── main.py                    # Main application file with all API logic
├── auth.py                    # Handles user authentication logic
├── users.json                 # Stores user data (username, hashed password)
├── applications.json          # Stores all job application data
├── job_listings.json          # Stores all job listing data
└── README.md                  # This file
