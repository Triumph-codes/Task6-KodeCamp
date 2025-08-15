# main.py

from fastapi import FastAPI, HTTPException, status, Depends
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from contextlib import asynccontextmanager
import json
import os
from colorama import Fore, Style, init

# Import authentication and user models
from auth import (
    get_authenticated_user, 
    get_current_admin,
    hash_password,
    UserInDB,
    UserLogin,
    users_db
)

# Initialize colorama
init(autoreset=True)

# --- Constants ---
PRODUCTS_FILE = "products.json"
CART_FILE = "cart.json"

# --- Pydantic Models for Shopping API ---
class ProductBase(BaseModel):
    """Base model for product creation."""
    name: str = Field(..., min_length=1)
    description: Optional[str] = None
    price: float = Field(..., gt=0)
    stock: int = Field(..., gt=0)

class Product(ProductBase):
    """Full product model with a unique ID."""
    id: str

class CartItem(BaseModel):
    """Model for an item in a user's cart."""
    product_id: str
    quantity: int = Field(..., gt=0)

class Cart(BaseModel):
    """Model representing a user's shopping cart."""
    items: List[CartItem] = []

# --- Database Mock-ups ---
products_db: Dict[str, Product] = {}
carts_db: Dict[str, Cart] = {}

# --- Utility Functions for Data Persistence ---
def load_data() -> None:
    """Loads product and cart data from JSON files."""
    global products_db, carts_db

    # Load products
    if os.path.exists(PRODUCTS_FILE):
        try:
            with open(PRODUCTS_FILE, "r") as f:
                data = json.load(f)
                products_db = {
                    item_id: Product(**product_data)
                    for item_id, product_data in data.items()
                }
            print(f"{Fore.GREEN}INFO: Loaded {len(products_db)} products.{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}ERROR loading products data: {e}{Style.RESET_ALL}")
            products_db = {}
    
    # Load carts
    if os.path.exists(CART_FILE):
        try:
            with open(CART_FILE, "r") as f:
                data = json.load(f)
                carts_db = {
                    user_id: Cart(**cart_data)
                    for user_id, cart_data in data.items()
                }
            print(f"{Fore.GREEN}INFO: Loaded {len(carts_db)} carts.{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}ERROR loading carts data: {e}{Style.RESET_ALL}")
            carts_db = {}
            
def save_data() -> None:
    """Saves product and cart data to JSON files."""
    try:
        with open(PRODUCTS_FILE, "w") as f:
            json.dump(
                {item_id: product.model_dump() for item_id, product in products_db.items()},
                f, indent=4
            )
        with open(CART_FILE, "w") as f:
            json.dump(
                {user_id: cart.model_dump() for user_id, cart in carts_db.items()},
                f, indent=4
            )
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
    title="Secure Shopping Cart API",
    description="An API for managing products and a user's shopping cart.",
    version="1.0.0",
    lifespan=lifespan
)

# --- API Endpoints ---
@app.post("/register/", status_code=status.HTTP_201_CREATED, summary="Register a new customer")
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
    save_data()
    print(f"{Fore.GREEN}INFO: User '{user_login.username}' registered successfully.{Style.RESET_ALL}")
    
    return {"message": "Registration successful"}

@app.post("/login/", summary="Log in an existing user")
async def login(user: UserInDB = Depends(get_authenticated_user)):
    """Authenticates a user and confirms successful login."""
    print(f"{Fore.GREEN}INFO: User '{user.username}' logged in successfully.{Style.RESET_ALL}")
    return {"message": "Login successful!"}

@app.post("/admin/add_product/", response_model=Product, status_code=status.HTTP_201_CREATED, summary="Add a new product (Admin only)")
async def add_product(
    product_data: ProductBase, 
    admin_user: UserInDB = Depends(get_current_admin)
):
    """
    Adds a new product to the catalog. This endpoint is restricted to users with the 'admin' role.
    """
    product_id = str(len(products_db) + 1) # Simple ID generation
    new_product = Product(id=product_id, **product_data.model_dump())
    products_db[product_id] = new_product
    save_data()
    print(f"{Fore.GREEN}INFO: Admin '{admin_user.username}' added new product '{new_product.name}'.{Style.RESET_ALL}")
    return new_product

@app.get(
    "/products/{product_id}",
    response_model=Product,
    summary="Get a single product by ID (Public)"
)
async def get_product(product_id: str):
    """
    Retrieves a single product from the catalog using its unique ID.
    """
    product = products_db.get(product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    return product

@app.put(
    "/admin/products/{product_id}",
    response_model=Product,
    summary="Update an existing product (Admin only)"
)
async def update_product(
    product_id: str,
    product_data: ProductBase,
    admin_user: UserInDB = Depends(get_current_admin)
):
    """
    Updates the details of an existing product. Restricted to admins.
    """
    if product_id not in products_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Update the product data while keeping the original ID
    updated_product = products_db[product_id].model_copy(update=product_data.model_dump())
    
    products_db[product_id] = updated_product
    save_data()
    print(f"{Fore.GREEN}INFO: Admin '{admin_user.username}' updated product '{updated_product.name}'.{Style.RESET_ALL}")
    return updated_product

@app.delete(
    "/admin/products/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a product (Admin only)"
)
async def delete_product(
    product_id: str,
    admin_user: UserInDB = Depends(get_current_admin)
):
    """
    Deletes a product from the catalog. Restricted to admins.
    """
    if product_id not in products_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    del products_db[product_id]
    save_data()
    print(f"{Fore.RED}INFO: Admin '{admin_user.username}' deleted product with ID '{product_id}'.{Style.RESET_ALL}")
    return None

@app.get("/products/", response_model=List[Product], summary="Get all products (Public)")
async def get_products():
    """Retrieves a list of all available products in the catalog."""
    return list(products_db.values())

@app.post("/cart/add/", summary="Add an item to the cart (Authenticated users only)")
async def add_to_cart(
    cart_item: CartItem, 
    current_user: UserInDB = Depends(get_authenticated_user)
):
    """
    Adds a specific quantity of a product to the authenticated user's cart.
    """
    product = products_db.get(cart_item.product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    if cart_item.quantity > product.stock:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Requested quantity exceeds available stock"
        )

    # Get or create the user's cart
    cart = carts_db.get(current_user.username, Cart())
    
    cart.items.append(cart_item)
    carts_db[current_user.username] = cart
    save_data()
    print(f"{Fore.GREEN}INFO: User '{current_user.username}' added {cart_item.quantity} of product '{product.name}' to cart.{Style.RESET_ALL}")
    
    return {"message": f"Added {cart_item.quantity} of product {product.name} to cart."}

@app.get("/cart/", response_model=Cart, summary="Get the authenticated user's cart (Authenticated users only)")
async def get_cart(current_user: UserInDB = Depends(get_authenticated_user)):
    """
    Retrieves the shopping cart for the currently logged-in user.
    """
    # Returns the cart or an empty cart if the user has no items yet
    return carts_db.get(current_user.username, Cart())

# --- Advanced Cart Management Endpoints ---

@app.put("/cart/", summary="Update an item's quantity in the cart (Authenticated users only)")
async def update_cart_item_quantity(
    cart_item: CartItem,
    current_user: UserInDB = Depends(get_authenticated_user)
):
    """
    Updates the quantity of a specific item in the authenticated user's cart.
    The new quantity must be greater than 0 and not exceed product stock.
    """
    product = products_db.get(cart_item.product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    if cart_item.quantity > product.stock:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Requested quantity exceeds available stock"
        )
        
    cart = carts_db.get(current_user.username, Cart())
    
    # Find and update the item in the cart
    item_updated = False
    for item in cart.items:
        if item.product_id == cart_item.product_id:
            item.quantity = cart_item.quantity
            item_updated = True
            break

    if not item_updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found in cart"
        )

    carts_db[current_user.username] = cart
    save_data()
    print(f"{Fore.GREEN}INFO: User '{current_user.username}' updated quantity for product '{product.name}' to {cart_item.quantity}.{Style.RESET_ALL}")
    
    return {"message": f"Updated quantity for product {product.name} to {cart_item.quantity}."}

@app.delete("/cart/{product_id}", summary="Remove a single item from the cart (Authenticated users only)")
async def remove_from_cart(
    product_id: str,
    current_user: UserInDB = Depends(get_authenticated_user)
):
    """
    Removes a single item from the authenticated user's cart by product ID.
    """
    cart = carts_db.get(current_user.username, None)
    if not cart:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart is empty or not found"
        )
    
    # Use list comprehension to create a new list without the item to be removed
    updated_items = [item for item in cart.items if item.product_id != product_id]
    
    # Check if the product was actually removed
    if len(updated_items) == len(cart.items):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found in cart"
        )

    cart.items = updated_items
    carts_db[current_user.username] = cart
    save_data()
    print(f"{Fore.GREEN}INFO: User '{current_user.username}' removed product '{product_id}' from cart.{Style.RESET_ALL}")

    return {"message": f"Product {product_id} removed from cart."}

@app.delete("/cart/", summary="Clear the entire cart (Authenticated users only)")
async def clear_cart(
    current_user: UserInDB = Depends(get_authenticated_user)
):
    """
    Deletes all items from the authenticated user's shopping cart.
    """
    if current_user.username not in carts_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart is already empty or not found"
        )
    
    del carts_db[current_user.username]
    save_data()
    print(f"{Fore.GREEN}INFO: User '{current_user.username}' cleared their cart.{Style.RESET_ALL}")

    return {"message": "Cart cleared successfully."}