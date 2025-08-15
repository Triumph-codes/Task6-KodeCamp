API Projects Repository
This repository contains a collection of API projects built with Python and the FastAPI framework. Each project is a self-contained application, designed to demonstrate robust backend development, secure authentication, and common API patterns.

1. Student Portal API 👨‍🎓
This API is designed to manage the core functionality of a simple student portal. It focuses on user management and academic data.

Key Features:
Student & Staff Accounts: Handles user registration and authentication for both students and staff.

Course Management: Endpoints for creating, listing, and retrieving details about courses.

Enrollment System: Functionality to enroll students in courses and track their academic progress.

2. Shopping API 🛒
A complete e-commerce backend for a simple online store. This API manages products, user carts, and the checkout process.

Key Features:
Product Catalog: Endpoints to view, search, and manage products.

Shopping Cart: Allows users to add, update, and remove items from their shopping cart.

Order Processing: Handles the creation of new orders and manages their status.

3. Job Application API 💼
This API serves as a backend for a job board, connecting employers with job seekers. It streamlines the process of posting and applying for jobs.

Key Features:
Job Postings: Endpoints for employers to create, update, and delete job listings.

Candidate Applications: Allows job seekers to submit applications for specific jobs.

Application Tracking: Provides a way for employers to track the status of applications.

4. Notes API 📝
A personal note-taking API that is secure and robust. It provides a complete set of CRUD (Create, Read, Update, Delete) operations for managing a user's private notes.

Key Features:
Secure Authentication: Utilizes JWT-based authentication to ensure that only the note owner can access their data.

Full CRUD.

Secure Configuration: Sensitive details like API keys and tokens are managed using a .env file and python-decouple.