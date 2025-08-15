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

class StudentPublic(BaseModel):
    """Public-facing student model for API responses (excludes sensitive data)."""
    username: str
    name: str
    subject_scores: Dict[str, float] = {}
    average: float = Field(...)
    grade: str = Field(...)
    role: str = "student"

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

class SubjectSummary(BaseModel):
    total_students: int
    average_score: float

class GradesSummary(BaseModel):
    overall_average: float
    subject_averages: Dict[str, SubjectSummary]

class PasswordChange(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=6)

# --- Password Hashing and Security ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBasic()

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_students_db() -> Dict[str, Student]:
    """Dependency to load the database for each request."""
    return students_db

def get_authenticated_user(
    credentials: HTTPBasicCredentials = Depends(security),
    db: Dict[str, Student] = Depends(get_students_db)
) -> Student:
    """Authenticates a user and returns the student object."""
    student = db.get(credentials.username)
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

def generate_grades_summary() -> GradesSummary:
    """Generates a comprehensive summary of all student grades."""
    if not students_db:
        return GradesSummary(overall_average=0.0, subject_averages={})
        
    total_students_with_grades = 0
    total_all_scores = 0.0
    subject_scores_sum: Dict[str, float] = {}
    subject_student_count: Dict[str, int] = {}

    for student in students_db.values():
        if student.subject_scores:
            total_students_with_grades += 1
            total_all_scores += student.average
            for subject, score in student.subject_scores.items():
                subject_scores_sum[subject] = subject_scores_sum.get(subject, 0.0) + score
                subject_student_count[subject] = subject_student_count.get(subject, 0) + 1

    overall_average = total_all_scores / total_students_with_grades if total_students_with_grades > 0 else 0.0

    subject_averages = {
        subject: SubjectSummary(
            total_students=subject_student_count[subject],
            average_score=subject_scores_sum[subject] / subject_student_count[subject]
        )
        for subject in subject_scores_sum
    }

    return GradesSummary(
        overall_average=round(overall_average, 2),
        subject_averages=subject_averages
    )

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
@app.post("/register/", status_code=status.HTTP_201_CREATED, summary="Register a new student")
async def register_student(student_login: StudentLogin, db: Dict[str, Student] = Depends(get_students_db)):
    """
    Registers a new student user with a unique username and password.
    """
    if student_login.username in db:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already registered"
        )
    
    hashed_password = hash_password(student_login.password)
    
    new_student = Student(
        username=student_login.username,
        hashed_password=hashed_password,
        name=student_login.username,
        role="student",
        subject_scores={},
        average=0.0,
        grade="N/A"
    )
    
    db[student_login.username] = new_student
    save_students_data()
    print(f"{Fore.GREEN}INFO: Student '{student_login.username}' registered successfully.{Style.RESET_ALL}")
    
    return {"message": "Registration successful"}

@app.post("/login/", summary="Log in a student")
async def login(student: Student = Depends(get_authenticated_user)):
    """
    Authenticates a user and confirms successful login.
    """
    print(f"{Fore.GREEN}INFO: Student '{student.username}' logged in successfully.{Style.RESET_ALL}")
    return {"message": "Login successful!"}

@app.get("/grades/", response_model=StudentPublic, summary="Get grades for the authenticated student")
async def get_grades(student: Student = Depends(get_authenticated_user)):
    """
    Retrieves the grades and profile information for the currently logged-in student.
    """
    return student

@app.put("/change-password/", summary="Change the authenticated student's password")
async def change_password(
    passwords: PasswordChange,
    current_user: Student = Depends(get_authenticated_user)
):
    """
    Allows a logged-in student to change their password by providing their old and new passwords.
    """
    # Verify the old password
    if not verify_password(passwords.old_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect old password"
        )
    
    # Hash and save the new password
    current_user.hashed_password = hash_password(passwords.new_password)
    save_students_data()
    
    print(f"{Fore.GREEN}INFO: Password for '{current_user.username}' changed successfully.{Style.RESET_ALL}")
    return {"message": "Password changed successfully"}

@app.put(
    "/grades/{username}",
    response_model=StudentPublic,
    summary="Update grades for a student (Admin only)",
    description="Allows an admin to add or modify grades for any student. This is restricted to users with the 'admin' role."
)
async def update_grades(
    username: str,
    grade_update: GradeUpdate,
    db: Dict[str, Student] = Depends(get_students_db),
    admin_user: Student = Depends(get_current_admin)
):
    student = db.get(username)
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

@app.get(
    "/reports/grades-summary",
    response_model=GradesSummary,
    summary="Get a summary of all student grades (Admin only)",
    description="Retrieves statistical information, including overall average and per-subject averages for all students. Restricted to users with the 'admin' role."
)
async def get_grades_summary(admin_user: Student = Depends(get_current_admin)):
    return generate_grades_summary()

@app.post(
    "/students/",
    response_model=StudentPublic,
    status_code=201,
    summary="Create a new student entry (Admin only)",
    description="Creates a new student entry with initial grades. This is an admin-only operation."
)
async def create_student(
    student_data: StudentBase,
    db: Dict[str, Student] = Depends(get_students_db),
    admin_user: Student = Depends(get_current_admin)
):
    name_lower = student_data.name.lower()
    if name_lower in db:
        raise HTTPException(409, detail="Student already exists")
    
    avg, grade = calculate_average_and_grade(student_data.subject_scores)
    student = Student(
        username=name_lower,
        hashed_password=hash_password("defaultpassword"),
        name=student_data.name,
        role="student",
        subject_scores=student_data.subject_scores,
        average=avg,
        grade=grade
    )
    db[name_lower] = student
    save_students_data()
    return student

@app.get(
    "/students/{name}",
    response_model=StudentPublic,
    summary="Get a student's profile (Admin only or self)",
    description="Allows an admin to get any student's profile, or a student to get their own profile. Access to other student profiles is forbidden."
)
async def get_student(
    name: str,
    db: Dict[str, Student] = Depends(get_students_db),
    current_user: Student = Depends(get_authenticated_user)
):
    if current_user.role != "admin" and current_user.username != name:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view this student's profile."
        )

    if (student := db.get(name.lower())) is None:
        raise HTTPException(404, detail="Student not found")
    return student

@app.get(
    "/students/",
    response_model=List[StudentPublic],
    summary="Get all student profiles (Admin only)",
    description="Retrieves a list of all students and their profiles. This endpoint is restricted to users with the 'admin' role."
)
async def get_all_students(
    db: Dict[str, Student] = Depends(get_students_db),
    admin_user: Student = Depends(get_current_admin)
):
    return list(db.values())

@app.put(
    "/students/{name}",
    response_model=StudentPublic,
    summary="Update a student's profile (Admin only)",
    description="Updates a student's profile data. This endpoint is restricted to users with the 'admin' role."
)
async def update_student(
    name: str,
    student_data: StudentBase,
    db: Dict[str, Student] = Depends(get_students_db),
    admin_user: Student = Depends(get_current_admin)
):
    name_lower = name.lower()
    if name_lower not in db:
        raise HTTPException(404, detail="Student not found")
    if student_data.name.lower() != name_lower:
        raise HTTPException(400, detail="Name mismatch")
    
    avg, grade = calculate_average_and_grade(student_data.subject_scores)
    student = db[name_lower]
    student.subject_scores = student_data.subject_scores
    student.average = avg
    student.grade = grade
    
    db[name_lower] = student
    save_students_data()
    return student

@app.delete(
    "/students/{name}",
    status_code=204,
    summary="Delete a student entry (Admin only)",
    description="Deletes a student and all their data from the system. This endpoint is restricted to users with the 'admin' role."
)
async def delete_student(
    name: str,
    db: Dict[str, Student] = Depends(get_students_db),
    admin_user: Student = Depends(get_current_admin)
):
    if (name_lower := name.lower()) not in db:
        raise HTTPException(404, detail="Student not found")
    del db[name_lower]
    save_students_data()
    return None