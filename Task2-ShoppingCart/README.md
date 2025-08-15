Secure Shopping Cart API
This is a FastAPI-based API designed for a secure e-commerce platform. It handles user authentication, product management, and shopping cart functionality, with a crucial focus on security features like rate limiting and role-based access control.

Features
User Authentication: Secure user registration and login endpoints.

Product Management: admin users can add and update product data.

Shopping Cart: customer users can add products to a personal shopping cart.

Checkout: A checkout process that finalizes the purchase and clears the cart.

Role-Based Access Control: Differentiates between admin and customer roles to protect sensitive endpoints.

Rate Limiting: Protects the login and registration endpoints from brute-force attacks by limiting the number of requests per minute.

Setup and Installation
Prerequisites:

Python 3.7+

Install dependencies:

Bash

pip install fastapi "uvicorn[standard]" python-jose[cryptography] colorama fastapi-limiter python-decouple
Required Files:
Make sure you have the following files in the same directory:

main.py (The main API code)

auth.py (The authentication helper code)

products.json (An empty JSON object {} to store product data)

users.json (An empty JSON object {} to store user data)

Running the Server:
Start the server using Uvicorn:

Bash

uvicorn main:app --reload
The API will be available at http://127.0.0.1:8000. You can access the interactive documentation at http://127.0.0.1:8000/docs.

API Endpoints
This table provides a summary of all available API endpoints and their access requirements.

Method	Endpoint	Description	Access
POST	/register/	Register a new user.	No
POST	/login/	Log in and receive an authentication token.	No
POST	/products/	Add a new product.	Admin Only
PUT	/products/{product_id}	Update an existing product.	Admin Only
POST	/cart/add/	Add a product to the cart.	Customer
GET	/cart/	View the contents of the shopping cart.	Customer
POST	/cart/checkout/	Finalize the purchase and clear the cart.	Customer

Export to Sheets
Project Structure
/secure-shopping-cart-api
├── main.py                    # Main application file with all API logic
├── auth.py                    # Handles user authentication logic
├── products.json              # Simple file-based database for products
└── cart.json                 # Simple file-based database for user's cart