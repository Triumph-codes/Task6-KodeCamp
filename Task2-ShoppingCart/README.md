Secure Shopping Cart API
A secure FastAPI designed for an e-commerce platform. This API handles user authentication, product management, shopping cart functionality, and includes a crucial security feature: rate limiting.

Features
User Authentication: Secure user registration and login endpoints.

Product Management: admin users can add and update product data.

Shopping Cart: customer users can add products to a personal shopping cart.

Checkout: A checkout process that finalizes the purchase and clears the cart.

Role-Based Access Control: Differentiates between admin and customer roles to protect sensitive endpoints.

Rate Limiting: Protects the login and registration endpoints from brute-force attacks by limiting the number of requests per minute.

Setup and Installation
Prerequisites
Python 3.7+

fastapi, uvicorn, python-jose, and colorama. Install with pip install fastapi uvicorn python-jose[cryptography] colorama.

fastapi-limiter for rate limiting. Install with pip install fastapi-limiter.

python-decouple for environment variables. Install with pip install python-decouple.

Required Files
Make sure you have the following files in the same directory:

main.py (The main API code)

auth.py (The authentication helper code)

products.json (An empty JSON object {} to store product data)

users.json (An empty JSON object {} to store user data)

Running the Server
Start the server using uvicorn:

uvicorn main:app --reload

The API will be available at http://127.0.0.1:8000. You can access the interactive documentation at http://127.0.0.1:8000/docs.

API Endpoints
1. Register a new user
curl -X POST "http://127.0.0.1:8000/register/" \
-H "Content-Type: application/json" \
-d '{
  "username": "customer_user",
  "password": "customer_password"
}'

2. Login as a user
Logging in will return a success message, which means your authentication token is now stored in the session.

curl -X POST "http://127.0.0.1:8000/login/" \
-H "Content-Type: application/json" \
-d '{
  "username": "customer_user",
  "password": "customer_password"
}'

3. Add a new product (Admin Only)
Note: You must log in as the admin user to access this endpoint.

curl -X POST "http://127.0.0.1:8000/products/" \
-H "Content-Type: application/json" \
-d '{
  "product_id": "P001",
  "name": "Laptop",
  "price": 999.99,
  "in_stock": true
}'

4. Add a product to the cart
curl -X POST "http://127.0.0.1:8000/cart/add/" \
-H "Content-Type: application/json" \
-d '{
  "product_id": "P001",
  "quantity": 1
}'

5. View your shopping cart
curl "http://127.0.0.1:8000/cart/"

6. Checkout
This endpoint will finalize the order and empty the cart.

curl -X POST "http://127.0.0.1:8000/cart/checkout/"

