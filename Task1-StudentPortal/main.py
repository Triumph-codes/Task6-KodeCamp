# main.py

from fastapi import FastAPI, HTTPException, status, Security, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel, Field, model_validator
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager
import json
import os
from colorama import Fore, Style, init 
from passlib.context import CryptContext

# Initialize colorama
init(autoreset=True)

# --- Constants ---
STUDENTS_FILE = "students.json"

# --- Pydantic Models ---
class StudentBase(BaseModel):
    """Base model for creating or updating a student."""
    name: str = Field(..., min_length=1)
    subject_scores: Dict[str, float] = Field(...)

    @model_validator(mode='after')
    def validate_scores(self):
        for subject, score in self.subject_scores.items():
            if not (0 <= score <= 100):
                raise ValueError(f"Score for {subject} must be between 0 and 100.")
        return self

class Student(StudentBase):
    """Full student model with authentication details, role, and calculated grades."""
    username: str
    hashed_password: str
    role: str = "student"
    average: float = Field(...)
    grade: str = Field(...)

class StudentLogin(BaseModel):
    """Model for student registration/login"""
    username: str = Field(..., min_length=3)
    password: str = Field(..., min_length=6)

class GradeUpdate(BaseModel):
    """Model for updating a student's grades."""
    subject_scores: Dict[str, float] = Field(...)

    @model_validator(mode='after')
    def validate_scores(self):
        for subject, score in self.subject_scores.items():
            if not (0 <= score <= 100):
                raise ValueError(f"Score for {subject} must be between 0 and 100.")
        return self

# --- Password Hashing and Security ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBasic()

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_authenticated_user(credentials: HTTPBasicCredentials = Depends(security)) -> Student:
    """Authenticates a user and returns the student object."""
    student = students_db.get(credentials.username)
    if not student or not verify_password(credentials.password, student.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    return student

def get_current_admin(student: Student = Depends(get_authenticated_user)) -> Student:
    """Authenticates a user and checks if they are an admin."""
    if student.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to perform this action."
        )
    return student

# --- Database and Utility Functions ---
students_db: Dict[str, Student] = {}

def load_students_data() -> None:
    global students_db
    if os.path.exists(STUDENTS_FILE):
        try:
            with open(STUDENTS_FILE, "r") as f:
                data = json.load(f)
                students_db = {
                    name: Student(**student_data)
                    for name, student_data in data.items()
                }
            print(f"{Fore.GREEN}INFO: Loaded {len(students_db)} students{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}ERROR loading data: {e}{Style.RESET_ALL}")
            students_db = {}

def save_students_data() -> None:
    try:
        with open(STUDENTS_FILE, "w") as f:
            json.dump(
                {name: student.model_dump() for name, student in students_db.items()},
                f, indent=4
            )
    except Exception as e:
        print(f"{Fore.RED}ERROR saving data: {e}{Style.RESET_ALL}")

def calculate_average_and_grade(scores: Dict[str, float]) -> tuple[float, str]:
    if not scores: return 0.0, "N/A"
    average = sum(scores.values()) / len(scores)
    if average >= 90: return round(average, 2), "A"
    elif average >= 80: return round(average, 2), "B"
    elif average >= 70: return round(average, 2), "C"
    elif average >= 60: return round(average, 2), "D"
    return round(average, 2), "F"

def create_initial_admin() -> None:
    """Creates a default admin user if one does not exist."""
    admin_username = "admin"
    admin_password = "admin_password" 

    if admin_username not in students_db:
        hashed_password = hash_password(admin_password)
        admin_user = Student(
            username=admin_username,
            hashed_password=hashed_password,
            name="Administrator",
            role="admin",
            subject_scores={},
            average=0.0,
            grade="N/A"
        )
        students_db[admin_username] = admin_user
        save_students_data()
        print(f"{Fore.YELLOW}WARNING: Default admin user '{admin_username}' created with password '{admin_password}'.{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}WARNING: This password should be changed in a production environment.{Style.RESET_ALL}")

# --- FastAPI App ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"{Fore.MAGENTA}Starting up...{Style.RESET_ALL}")
    load_students_data()
    create_initial_admin()
    yield
    print(f"{Fore.MAGENTA}Shutting down...{Style.RESET_ALL}")

app = FastAPI(
    title="Student Portal API",
    description="Manages student scores and grades with user authentication",
    version="1.0.0",
    lifespan=lifespan
)

# --- API Endpoints ---
@app.post("/register/", status_code=status.HTTP_201_CREATED)
async def register_student(student_login: StudentLogin):
    if student_login.username in students_db:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already registered"
        )
    
    hashed_password = hash_password(student_login.password)
    
    # New students are assigned a default role of "student"
    new_student = Student(
        username=student_login.username,
        hashed_password=hashed_password,
        name=student_login.username, # Default name to username
        role="student",
        subject_scores={},
        average=0.0,
        grade="N/A"
    )
    
    students_db[student_login.username] = new_student
    save_students_data()
    print(f"{Fore.GREEN}INFO: Student '{student_login.username}' registered successfully.{Style.RESET_ALL}")
    
    return {"message": "Registration successful"}

@app.post("/login/", summary="Log in a student")
async def login(student: Student = Depends(get_authenticated_user)):
    print(f"{Fore.GREEN}INFO: Student '{student.username}' logged in successfully.{Style.RESET_ALL}")
    return {"message": "Login successful!"}

@app.put(
    "/grades/{username}",
    response_model=Student,
    summary="Update grades for a student (Admin only)",
    description="Allows an admin to add or modify grades for any student.",
)
async def update_grades(
    username: str,
    grade_update: GradeUpdate,
    admin_user: Student = Depends(get_current_admin)
):
    student = students_db.get(username)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    student.subject_scores.update(grade_update.subject_scores)
    
    avg, grade = calculate_average_and_grade(student.subject_scores)
    student.average = avg
    student.grade = grade
    
    save_students_data()

    print(f"{Fore.GREEN}INFO: Admin '{admin_user.username}' updated grades for '{username}'.{Style.RESET_ALL}")
    return student

@app.get("/grades/", response_model=Student)
async def get_grades(student: Student = Depends(get_authenticated_user)):
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    return student

@app.get("/students/{name}", response_model=Student)
async def get_student(name: str):
    if (student := students_db.get(name.lower())) is None:
        raise HTTPException(404, detail="Student not found")
    return student

@app.get("/students/", response_model=List[Student])
async def get_all_students():
    return list(students_db.values())

@app.put("/students/{name}", response_model=Student)
async def update_student(name: str, student_data: StudentBase):
    name_lower = name.lower()
    if name_lower not in students_db:
        raise HTTPException(404, detail="Student not found")
    if student_data.name.lower() != name_lower:
        raise HTTPException(400, detail="Name mismatch")
    
    avg, grade = calculate_average_and_grade(student_data.subject_scores)
    student = students_db[name_lower]
    student.subject_scores = student_data.subject_scores
    student.average = avg
    student.grade = grade
    
    students_db[name_lower] = student
    save_students_data()
    return student

@app.delete("/students/{name}", status_code=204)
async def delete_student(name: str):
    if (name_lower := name.lower()) not in students_db:
        raise HTTPException(404, detail="Student not found")
    del students_db[name_lower]
    save_students_data()
    return None