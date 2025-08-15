# Secure Student Portal API

This is a FastAPI-based student portal API that allows students to register, log in, and view their grades securely. The API is designed to separate user authentication from data management and includes role-based access control to protect sensitive data like student grades.

## Features

* **User Authentication**: Students can register and log in using a secure username and password. Passwords are automatically hashed and stored using `bcrypt` for security.
* **Role-Based Access Control**: New users are automatically assigned the "student" role. A dedicated `admin` role is created on startup to demonstrate administrative access to grade management.
* **Protected Endpoints**: A dedicated `PUT /grades/{username}` endpoint is secured to be accessible only by a user with the "admin" role.
* **Data Persistence**: Student data, including usernames, hashed passwords, and grades, is stored in a `students.json` file.
* **Grade Management**: Averages and letter grades are automatically calculated based on subject scores.
* **Command-Line Interface**: The API provides colorful and informative logs on startup and shutdown using the `colorama` library.

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

## API Endpoints

| Method | Endpoint | Description | Authentication Required |
| :----- | :------------------ | :---------------------------------------------------------------------- | :-------------------------------- |
| `POST` | `/register/` | Register a new student user. | No |
| `POST` | `/login/` | Authenticate a user and receive a success message. | Yes (Basic Auth) |
| `GET` | `/grades/` | Retrieve the authenticated student's grades. | Yes (Student or Admin) |
| `PUT` | `/grades/{username}` | Update a student's grades. | Yes (Admin Only) |
| `GET` | `/students/` | Retrieve a list of all students. | Yes (Admin Only) |
| `GET` | `/students/{name}` | Retrieve a single student's profile. | Yes (Admin or Self) |
| `POST` | `/students/` | Create a student entry with grades. | Yes (Admin Only) |
| `PUT` | `/students/{name}` | Update a student's data. | Yes (Admin Only) |
| `DELETE`| `/students/{name}` | Delete a student entry. | Yes (Admin Only) |

---

## Admin Access

For testing administrative endpoints, the API is configured to create a default admin user on startup if one does not already exist.

**Default Credentials:**
* **Username:** `admin`
* **Password:** `admin_password`

You can use these credentials to access endpoints like `PUT /grades/{username}` to update student grades. For a production environment, this password should be changed immediately after the first run.

---

## Project Structure