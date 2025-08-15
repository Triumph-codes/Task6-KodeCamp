Notes API with JWT Authentication 📝
This is a simple, yet robust, FastAPI application that provides a secure notes management system. Users can register, log in with JSON Web Tokens (JWT), and perform full CRUD (Create, Read, Update, Delete) operations on their personal notes.

The API is built to demonstrate key concepts:

User Authentication: Secure user registration and login using JWT.

Dependencies: Using FastAPI's dependency injection to manage authentication.

Data Persistence: Storing user and notes data in JSON files.

Asynchronous Endpoints: Efficiently handling I/O-bound tasks.

Console Logging: Utilizing colorama for a better development experience.

🚀 Getting Started
These instructions will get a copy of the project up and running on your local machine for development and testing purposes.

Prerequisites
You'll need Python 3.8+ installed on your system. It's highly recommended to use a virtual environment.

Installation
Clone the repository:

Bash

git clone <your-repo-url>
cd <your-repo-name>
Create a virtual environment:

Bash

# On Windows
python -m venv venv
venv\Scripts\activate

# On macOS/Linux
python3 -m venv venv
source venv/bin/activate
Install the required packages:

Bash

pip install -r requirements.txt
Note: If you don't have a requirements.txt file, you can generate one after installing the necessary packages:

Bash

pip install fastapi "uvicorn[standard]" python-jose[cryptography] passlib[bcrypt] python-decouple colorama
Create your .env file:
Create a file named .env in the root directory and add your secret key and algorithm.

.env

SECRET_KEY="your_super_secret_and_long_key_here"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30
Running the Application
To run the API server, execute the following command from the project's root directory:

Bash

uvicorn main:app --reload
The server will be available at http://127.0.0.1:8000. You can access the interactive API documentation at http://127.0.0.1:8000/docs.

⚙️ API Endpoints
All endpoints require a valid JWT token in the Authorization: Bearer <token> header, except for /register/ and /login/.

Authentication
POST /register/: Register a new user with a username and password.

POST /login/: Log in with a username and password to get a JWT token.

Notes Management
GET /notes/: Retrieve all notes for the authenticated user.

POST /notes/: Create a new note.

GET /notes/{note_id}: Retrieve a single note by its ID.

PUT /notes/{note_id}: Update an existing note.

DELETE /notes/{note_id}: Delete a note by its ID.

🤝 Contributing
Feel free to fork the repository and contribute. Any contributions, bug reports, and feature requests are welcome.