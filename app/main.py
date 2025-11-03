from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List
from datetime import timedelta

from . import crud, models, schemas
from .database import Local_Session, engine
from .auth import (
    create_access_token,
    get_current_user,
    get_current_admin,
    get_current_seller,
    get_current_admin_or_seller,
)

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Vardan E-Commerce API", version="0.1.0")


def get_db():
    db = Local_Session()
    try:
        yield db
    finally:
        db.close()


# Home
@app.get("/", summary="Welcome message", tags=["Auth"])
def home():
    return {"Message": "Welcome To Vardan E-Commerce FastAPI "}


# ==================== AUTH ====================

@app.post("/login", response_model=schemas.Token, summary="Login user", tags=["Auth"])
def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    user = crud.get_user_by_email(db, email=form_data.username)
    if not user or not crud.verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    token = create_access_token(
        data={"user_id": user.id, "email": user.email, "role": user.role},
        expires_delta=timedelta(minutes=60),
    )
    return {"access_token": token, "token_type": "bearer"}


# ==================== USERS ====================

@app.post("/users/", response_model=schemas.User, status_code=201, summary="Register new user", tags=["Users"])
def signup(user: schemas.UserCreate, db: Session = Depends(get_db)):
    if crud.get_user_by_email(db, email=user.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.Signup(db=db, user=user)


@app.get("/users/", response_model=List[schemas.User], summary="Get user list", tags=["Users"])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if current_user.role == "admin":
        return crud.get_users(db, skip=skip, limit=limit)
    return [crud.get_user(db, user_id=current_user.id)]


@app.get("/users/{user_id}", response_model=schemas.User, summary="Get user by ID", tags=["Users"])
def read_user(user_id: int, db: Session = Depends(get_db)):
    db_user = crud.get_user(db, user_id=user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@app.put("/users/", response_model=schemas.User, summary="Update user details", tags=["Users"])
def update_user(update: schemas.UserUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    db_user = crud.get_user(db, user_id=current_user.id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return crud.update_user(db, user=db_user, update=update)


@app.delete("/users/{user_id}", response_model=schemas.User, summary="Delete user by ID", tags=["Users"])
def delete_user_by_admin(user_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if current_user.role != "admin" and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="You can only delete your own account")
    db_user = crud.del_user(db, user_id=user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@app.delete("/users/", response_model=schemas.User, summary="Delete my account", tags=["Users"])
def delete_own_user(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    db_user = crud.del_user(db, user_id=current_user.id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@app.put("/admin/users/{user_id}/role", response_model=schemas.User, summary="Update user role (Admin only)", tags=["Users"])
def admin_update_user_role(user_id: int, update: schemas.UserUpdate, db: Session = Depends(get_db), admin: models.User = Depends(get_current_admin)):
    db_user = crud.get_user(db, user_id=user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    if update.role not in ["customer", "seller", "admin"]:
        raise HTTPException(status_code=400, detail="Invalid role")
    return crud.update_user(db, user=db_user, update=update)


@app.get("/me", response_model=schemas.User, summary="Get current user", tags=["Users"])
def read_me(current_user: models.User = Depends(get_current_user)):
    return current_user


# ==================== ADDRESSES ====================

@app.post("/addresses/", response_model=schemas.Address, summary="Add new address", tags=["Addresses"])
def add_address(address: schemas.AddressCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return crud.create_address(db, user_id=current_user.id, address=address)


@app.put("/addresses/update", response_model=schemas.Address, summary="Update address", tags=["Addresses"])
def update_address(update: schemas.AddressUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    db_address = crud.get_address(db, user_id=current_user.id)
    if not db_address:
        raise HTTPException(status_code=404, detail="Address not found")
    return crud.update_address(db=db, db_address=db_address, update=update)


@app.get("/addresses/", response_model=List[schemas.Address], summary="List all addresses", tags=["Addresses"])
def list_addresses(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return crud.get_addresses(db, user_id=current_user.id)


# ==================== CATEGORIES ====================

@app.post("/categories/", response_model=schemas.Category, summary="Create new category", tags=["Categories"])
def create_category(category: schemas.CategoryCreate, db: Session = Depends(get_db), admin_seller: models.User = Depends(get_current_admin_or_seller)):
    return crud.create_category(db, category=category)


@app.get("/categories/", response_model=List[schemas.Category], summary="Get all categories", tags=["Categories"])
def get_categories(db: Session = Depends(get_db)):
    return crud.get_categories(db)


@app.put("/categories/{category_id}", response_model=schemas.Category, summary="Update category", tags=["Categories"])
def update_category(category_id: int, category: schemas.CategoryCreate, db: Session = Depends(get_db), admin_seller: models.User = Depends(get_current_admin_or_seller)):
    updated_category = crud.update_category(db, category_id=category_id, update=category)
    if not updated_category:
        raise HTTPException(status_code=404, detail="Category not found")
    return updated_category


@app.delete("/categories/{category_id}", summary="Delete category", tags=["Categories"])
def delete_category(category_id: int, db: Session = Depends(get_db), admin: models.User = Depends(get_current_admin)):
    deleted = crud.delete_category(db, category_id=category_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Category not found")
    return {"message": "Category deleted successfully"}


# ==================== PRODUCTS ====================

@app.get("/products/", response_model=List[schemas.Product], summary="List all products", tags=["Products"])
def list_products(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_products(db, skip=skip, limit=limit)


@app.get("/products/{product_id}", response_model=schemas.Product, summary="Get product by ID", tags=["Products"])
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = crud.get_product(db, product_id=product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@app.post("/products/", response_model=schemas.Product, status_code=201, summary="Create new product", tags=["Products"])
def create_product(product: schemas.ProductBase, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return crud.create_product(db, product=product, seller_id=current_user.id if current_user.role == "seller" else None)


@app.get("/seller/products/", response_model=List[schemas.Product], summary="Get seller's products", tags=["Products"])
def seller_get_products(db: Session = Depends(get_db), seller: models.User = Depends(get_current_seller)):
    if seller.role == "admin":
        return crud.get_products(db)
    return crud.get_products_by_seller(db, seller_id=seller.id)
@app.put("/seller/products/{product_id}", response_model=schemas.Product, summary="Update seller product", tags=["Products"])
def seller_update_product(product_id: int, product_update: schemas.ProductBase, db: Session = Depends(get_db), seller: models.User = Depends(get_current_seller)):
    updated = crud.update_product(db, product_id=product_id, update=product_update, seller_id=seller.id if seller.role == "seller" else None)
    if not updated:
        raise HTTPException(status_code=404, detail="Product not found or not authorized")
    return updated


@app.delete("/seller/products/{product_id}", summary="Delete seller product", tags=["Products"])
def seller_delete_product(product_id: int, db: Session = Depends(get_db), seller: models.User = Depends(get_current_seller)):
    deleted = crud.delete_product(db, product_id=product_id, user_id=seller.id, user_role=seller.role)
    if not deleted:
        raise HTTPException(status_code=404, detail="Product not found or not authorized")
    return {"message": "Product deleted successfully"}


@app.delete("/admin/products/{product_id}", summary="Delete product (Admin only)", tags=["Products"])
def admin_delete_product(product_id: int, db: Session = Depends(get_db), admin: models.User = Depends(get_current_admin)):
    deleted = crud.delete_product(db, product_id=product_id, user_id=admin.id, user_role=admin.role)
    if not deleted:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"message": "Product deleted successfully"}


# ==================== CART ====================

@app.get("/cart/", response_model=schemas.Cart, tags=["Cart"], summary="Get current user's cart")
def get_cart(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    cart = crud.get_cart(db, user_id=current_user.id)
    if not cart:
        cart = crud.create_cart(db, user_id=current_user.id)
    return cart

@app.post("/cart/items", response_model=schemas.CartItem, tags=["Cart"], summary="Add item to current user's cart")
def add_item_to_cart(item: schemas.CartItemBase, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    cart = crud.get_cart(db, user_id=current_user.id)
    if not cart:
        cart = crud.create_cart(db, user_id=current_user.id)
    try:
        return crud.add_cart_item(db, cart_id=cart.id, item=item)
    except ValueError as e:
        msg = str(e).lower()
        if "not found" in msg:
            raise HTTPException(status_code=404, detail=str(e))
        if "insufficient" in msg:
            raise HTTPException(status_code=400, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/cart/items/{cart_item_id}", response_model=schemas.CartItem, tags=["Cart"], summary="Update quantity of a cart item")
def update_cart_item(cart_item_id: int, quantity: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    item = crud.update_cart_item(db, cart_item_id=cart_item_id, quantity=quantity)
    if not item:
        raise HTTPException(status_code=404, detail="Cart item not found")
    if item.cart.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not allowed to modify this item")
    return item

@app.delete("/cart/items/{cart_item_id}", tags=["Cart"], summary="Remove an item from the cart")
def delete_cart_item(cart_item_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    # item = crud.remove_cart_item(db, cart_item_id)
    # if not item:
    #     raise HTTPException(status_code=404, detail="Cart item not found")
    # cart = db.query(models.Cart).filter(models.Cart.id == item.cart_id).first()
    # if item.cart.user_id != current_user.id and current_user.role != "admin":
    #     raise HTTPException(status_code=403, detail="Not allowed to delete this item")
    # crud.remove_cart_item(db, cart_item_id=cart_item_id)
    # return {"message": "Cart Item Deleted Successfully"}

    item = db.query(models.CartItem).filter(models.CartItem.id == cart_item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Cart item not found")
    cart = db.query(models.Cart).filter(models.Cart.id == item.cart_id).first()
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")
    if cart.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not allowed to delete this item")

    # Step 4: Delete the item safely
    deleted = crud.remove_cart_item(db, cart_item_id=cart_item_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Cart item not found")

    return {"message": "Cart Item Deleted Successfully"}


# ==================== ORDERS ====================

@app.post("/orders/", response_model=schemas.Order, tags=["Orders"], summary="Create an order from the current user's cart")
def create_order_from_cart(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    try:
        return crud.create_order_from_cart_for_user(db=db, user_id=current_user.id)
    except ValueError as e:
        msg = str(e).lower()
        # Map resource-not-found errors to 404, empty cart to 400
        if "not found" in msg:
            raise HTTPException(status_code=404, detail=str(e))
        if "empty" in msg:
            raise HTTPException(status_code=400, detail=str(e))
        # fallback
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/orders/", response_model=List[schemas.Order], tags=["Orders"], summary="List orders for current user")
def get_orders(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return crud.get_orders(db, user_id=current_user.id)

@app.get("/orders/detail/{order_id}", response_model=schemas.Order, tags=["Orders"], summary="Get order detail")
def get_order(order_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    order = crud.get_order(db, order_id=order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not allowed to access this order")
    return order
# ==================== WISHLIST ====================

@app.post("/wishlist/", response_model=schemas.WishlistResponse, status_code=201, summary="Add item to wishlist", tags=["Wishlist"])
def add_to_wishlist(w: schemas.WishlistCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return crud.add_to_wishlist(db, user_id=current_user.id, product_id=w.product_id)


@app.get("/wishlist/", response_model=List[schemas.WishlistResponse], summary="Get wishlist", tags=["Wishlist"])
def get_wishlist(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return crud.get_wishlist(db, user_id=current_user.id)


@app.delete("/wishlist/{wishlist_id}", status_code=204, summary="Remove item from wishlist", tags=["Wishlist"])
def remove_wishlist(wishlist_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    item = crud.remove_from_wishlist(db, wishlist_id)
    if not item:
        raise HTTPException(status_code=404, detail="Wishlist item not found")
    if item.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not allowed")
    return None


# ==================== REVIEWS ====================

@app.post("/reviews/", response_model=schemas.ReviewResponse, status_code=201, summary="Add product review", tags=["Reviews"])
def add_review(review: schemas.ReviewCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    try:
        return crud.create_review(db, user_id=current_user.id, review=review)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/reviews/{product_id}", response_model=List[schemas.ReviewResponse], summary="Get reviews for product", tags=["Reviews"])
def get_reviews(product_id: int, db: Session = Depends(get_db)):
    return crud.get_reviews_for_product(db, product_id=product_id)


# ==================== SHIPMENTS ====================

@app.post("/shipments/", response_model=schemas.ShipmentResponse, status_code=201, summary="Create new shipment", tags=["Shipments"])
def create_shipment(shipment: schemas.ShipmentCreate, db: Session = Depends(get_db), admin_seller: models.User = Depends(get_current_admin_or_seller)):
    try:
        return crud.create_shipment(db, shipment)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/shipments/", response_model=List[schemas.ShipmentResponse], summary="Get all shipments", tags=["Shipments"])
def get_shipments(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), admin_seller: models.User = Depends(get_current_admin_or_seller)):
    return crud.get_shipments(db, skip=skip, limit=limit)


@app.get("/shipments/{shipment_id}", response_model=schemas.ShipmentResponse, summary="Get shipment by ID", tags=["Shipments"])
def get_shipment(shipment_id: int, db: Session = Depends(get_db), admin_seller: models.User = Depends(get_current_admin_or_seller)):
    ship = crud.get_shipment(db, shipment_id)
    if not ship:
        raise HTTPException(status_code=404, detail="Shipment not found")
    return ship


@app.put("/shipments/{shipment_id}", response_model=schemas.ShipmentResponse, summary="Update shipment status", tags=["Shipments"])
def update_shipment(shipment_id: int, status: str, db: Session = Depends(get_db), admin_seller: models.User = Depends(get_current_admin_or_seller)):
    ship = crud.update_shipment_status(db, shipment_id=shipment_id, status=status)
    if not ship:
        raise HTTPException(status_code=404, detail="Shipment not found")
    return ship
