# Secure Student Portal API

This is a FastAPI-based student portal API that allows students to register, log in, and view their grades securely. The API is designed to separate user authentication from data management and includes fine-grained role-based access control to protect sensitive data.

## Features

* **User Authentication**: Students can register and log in using a secure username and password. Passwords are automatically hashed and stored using `bcrypt`.
* **Role-Based Access Control**: Users are assigned either a "student" or "admin" role to control access to specific endpoints.
* **Student Self-Service**: Students can change their own password without needing administrative intervention.
* **Admin-Only Reports**: A dedicated endpoint provides statistical reports, such as average scores per subject, for administrators.
* **Protected Endpoints**: Sensitive actions like student data management are restricted to admins.
* **Data Protection**: API responses use a public-facing Pydantic model (`StudentPublic`) to ensure sensitive data is never exposed.
* **Data Persistence**: All student data is stored in a `students.json` file.
* **Informative Logging**: The API provides colorful and detailed logs on startup and shutdown.

---

## Setup and Installation

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/Triumph-codes/Task5-KodeCamp.git](https://github.com/Triumph-codes/Task5-KodeCamp.git)
    cd Task5-KodeCamp/Task1-StudentPortal
    ```

2.  **Create a virtual environment:**
    ```bash
    python -m venv venv
    ```

3.  **Activate the virtual environment:**
    * **Windows:**
        ```bash
        venv\Scripts\activate
        ```
    * **macOS / Linux:**
        ```bash
        source venv/bin/activate
        ```

4.  **Install dependencies:**
    ```bash
    pip install fastapi "uvicorn[standard]" passlib[bcrypt] python-multipart colorama
    ```

5.  **Run the API:**
    ```bash
    uvicorn main:app --reload
    ```
    The API will be running at `http://127.0.0.1:8000`. You can access the interactive documentation at `http://127.0.0.1:8000/docs`.

---

## Admin Access

For testing administrative endpoints, the API is configured to create a default admin user on startup if one doesn't already exist.

**Default Credentials:**
* **Username:** `admin`
* **Password:** `admin_password`

You can use these credentials to access all endpoints, including those with restricted access, such as updating grades or creating student entries.

---

## API Endpoints

This table provides a summary of all available API endpoints and their access requirements.

| Method | Endpoint | Description | Authentication Required |
| :----- | :------------------ | :---------------------------------------------------------------------- | :-------------------------------- |
| `POST` | `/register/` | Register a new student user. | No |
| `POST` | `/login/` | Authenticate a user and receive a success message. | Yes (Basic Auth) |
| `PUT` | `/change-password/` | Change the authenticated student's password. | Yes (Student or Admin) |
| `GET` | `/grades/` | Retrieve the authenticated student's grades. | Yes (Student or Admin) |
| `PUT` | `/grades/{username}` | Update a student's grades. | Yes (Admin Only) |
| `GET` | `/reports/grades-summary` | Get a summary of all student grades. | Yes (Admin Only) |
| `POST` | `/students/` | Create a new student entry. | Yes (Admin Only) |
| `GET` | `/students/` | Retrieve a list of all students. | Yes (Admin Only) |
| `GET` | `/students/{name}` | Retrieve a single student's profile. | Yes (Admin or Self) |
| `PUT` | `/students/{name}` | Update a student's data. | Yes (Admin Only) |
| `DELETE`| `/students/{name}` | Delete a student entry. | Yes (Admin Only) |

---

## Project Structure
'''
/Task1-StudentPortal
├── main.py                # Main application file with all API logic
├── students.json          # Simple file-based database for students
└── README.md              # This file

'''