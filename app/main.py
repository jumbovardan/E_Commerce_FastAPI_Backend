from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List
from datetime import timedelta

from . import crud, models, schemas
from .database import Local_Session, engine
from .auth import create_access_token, get_current_user

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Vardan E-Commerce Here U Can Buy Anything U Want Just add in cart and place order ")


# Dependency: DB session
def get_db():
    db = Local_Session()
    try:
        yield db
    finally:
        db.close()


# HOME
@app.get("/")
def home():
    return {"Message": "Welcome To Vardan E-Commerce FastAPI Here U Can Buy Anything U Want Just add in cart and place order "}


# USER ENDPOINTS
@app.post("/users/", response_model=schemas.User, status_code=201)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)

@app.get("/users/", response_model=List[schemas.User])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_users(db, skip=skip, limit=limit)

@app.get("/users/{user_id}", response_model=schemas.User)
def read_user(user_id: int, db: Session = Depends(get_db)):
    db_user = crud.get_user(db, user_id=user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@app.put("/users/{user_id}", response_model=schemas.User)
def update_user(user_id: int, update: schemas.UserUpdate, db: Session = Depends(get_db),current_user:models.User=Depends(get_current_user)):
    if user_id != current_user.id:
        raise HTTPException(status_code=403,detail="You are not authorized to modify this user")
    db_user = crud.get_user(db, user_id=user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return crud.update_user(db, user=db_user, update=update)

@app.delete("/users/{user_id}", response_model=schemas.User)
def delete_user(user_id: int, db: Session = Depends(get_db),current_user:models.User=Depends(get_current_user)):
    if user_id != current_user.id:
        raise HTTPException(status_code=403,detail="You are not authorized to Delete this user")
    db_user = crud.del_user(db, user_id=user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


# ADDRESS USER
@app.post("/addresses/", response_model=schemas.Address)
def add_address(user_id: int, address: schemas.AddressCreate, db: Session = Depends(get_db),current_user:models.User=Depends(get_current_user)):
    if user_id != current_user.id:
        raise HTTPException(status_code=403,detail="You are not authorized to for this action")
    return crud.create_address(db, user_id=user_id, address=address)

@app.post("/addresses/{user_id}/update", response_model=schemas.Address)
def update_address(
    user_id: int,
    update: schemas.AddressUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You are not authorized to update another user's address")

    db_address = crud.get_address(db, user_id=user_id)
    if not db_address:
        raise HTTPException(status_code=404, detail="Address not found")
    if db_address.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this address")

    return crud.update_address(db=db, db_address=db_address, update=update)



@app.get("/addresses/{user_id}", response_model=List[schemas.Address])
def list_addresses(user_id: int, db: Session = Depends(get_db)):
    return crud.get_addresses(db, user_id=user_id)


# CURRENT LOGGED-IN USER
@app.get("/me", response_model=schemas.User)
def read_me(current_user: models.User = Depends(get_current_user)):
    return current_user


# LOGIN
@app.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = crud.get_user_by_email(db, email=form_data.username)
    if not user or not crud.verify_password(form_data.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    access_token = create_access_token(
        data={"user_id": user.id, "email": user.email},
        expires_delta=timedelta(minutes=60)
    )
    return {"access_token": access_token, "token_type": "bearer"}


# CATEGOTY ENDPOINTS
@app.post("/categories/", response_model=schemas.Category)
def create_category(category: schemas.CategoryCreate, db: Session = Depends(get_db)):
    return crud.create_category(db, category=category)

@app.get("/categories/", response_model=list[schemas.Category])
def get_categories(db: Session = Depends(get_db)):
    return crud.get_categories(db)


# PRODUCT ENDPOINTS
@app.get("/products/", response_model=List[schemas.Product])
def list_products(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_products(db, skip=skip, limit=limit)

@app.get("/products/{product_id}", response_model=schemas.Product)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = crud.get_product(db, product_id=product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@app.post("/products/", response_model=schemas.Product, status_code=201)
def create_product(product: schemas.ProductBase, db: Session = Depends(get_db)):
    return crud.create_product(db, product=product)


# CART ENDPOINTS
@app.get("/cart/{user_id}", response_model=schemas.Cart)
def get_cart(user_id: int, db: Session = Depends(get_db), current_user:models.User=Depends(get_current_user)):
    if current_user.id != user_id:
        raise HTTPException(status_code=403,detail="You are not authorized to access this cart")
    cart = crud.get_cart(db, user_id=current_user.id)
    if not cart:
        cart = crud.create_cart(db, user_id=current_user.id)
    return cart

@app.post("/cart/{user_id}/items", response_model=schemas.CartItem)
def add_item_to_cart(user_id: int, item: schemas.CartItemBase, db: Session = Depends(get_db),current_user:models.User=Depends(get_current_user)):
    if current_user.id != user_id:
        raise HTTPException(status_code=403,detail="You are not authorized to access this cart")
    cart = crud.get_cart(db, user_id=current_user.id)
    if not cart:
        cart = crud.create_cart(db, user_id=current_user.id)
    return crud.add_cart_item(db, cart_id=cart.id, item=item)

@app.put("/cart/items/{cart_item_id}", response_model=schemas.CartItem)
def update_cart_item(cart_item_id: int, quantity: int, db: Session = Depends(get_db),current_user:models.User=Depends(get_current_user)):
    item = crud.update_cart_item(db, cart_item_id=cart_item_id, quantity=quantity)
    if not item:
        raise HTTPException(status_code=404, detail="Cart item not found")
    if item.cart.user_id !=current_user.id:
        raise HTTPException(status_code=403,detail="Not allowed to modify this item")
    return item

@app.delete("/cart/items/{cart_item_id}")
def delete_cart_item(cart_item_id: int, db: Session = Depends(get_db),current_user:models.User=Depends(get_current_user)):
    item = crud.remove_cart_item(db, cart_item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Cart item not found")
    cart=db.query(models.Cart).filter(models.Cart.id == item.cart_id).first()
    if item.cart.user_id != current_user.id:
        raise HTTPException(status_code=403,detail="Not allowed to delete this item")
    crud.remove_cart_item(db, cart_item_id=cart_item_id)
    return {"message": "Cast Item Deleted Successfully"}


# ORDER ENDPOINTS
@app.post("/orders/", response_model=schemas.Order)
def create_order_from_cart(
    user_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return crud.create_order_from_cart_for_user(db=db, user_id=current_user.id)


@app.get("/orders/{user_id}", response_model=List[schemas.Order])
def get_orders(user_id: int, db: Session = Depends(get_db),current_user:models.User=Depends(get_current_user)):
    return crud.get_orders(db, user_id=current_user.id)

@app.get("/orders/detail/{order_id}", response_model=schemas.Order)
def get_order(order_id: int, db: Session = Depends(get_db),current_user:models.User=Depends(get_current_user)):
    order = crud.get_order(db, order_id=order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed to access this order")
    return order


# WISHLIST
@app.post("/wishlist/", response_model=schemas.WishlistResponse, status_code=201)
def add_to_wishlist_endpoint(w: schemas.WishlistCreate,
                             db: Session = Depends(get_db),
                             current_user: models.User = Depends(get_current_user)):
    item = crud.add_to_wishlist(db, user_id=current_user.id, product_id=w.product_id)
    return item

@app.get("/wishlist/", response_model=List[schemas.WishlistResponse])
def get_wishlist_endpoint(db: Session = Depends(get_db),
                          current_user: models.User = Depends(get_current_user)):
    return crud.get_wishlist(db, user_id=current_user.id)

@app.delete("/wishlist/{wishlist_id}", status_code=204)
def remove_wishlist_endpoint(wishlist_id: int,
                             db: Session = Depends(get_db),
                             current_user: models.User = Depends(get_current_user)):
    item = crud.remove_from_wishlist(db, wishlist_id)
    if not item:
        raise HTTPException(status_code=404, detail="Wishlist item not found")
    
    if item.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed")
    return None


# REVIEWS
@app.post("/reviews/", response_model=schemas.ReviewResponse, status_code=201)
def add_review_endpoint(review: schemas.ReviewCreate,
                        db: Session = Depends(get_db),
                        current_user: models.User = Depends(get_current_user)):
    try:
        db_review = crud.create_review(db, user_id=current_user.id, review=review)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return db_review

@app.get("/reviews/{product_id}", response_model=List[schemas.ReviewResponse])
def get_reviews_endpoint(product_id: int, db: Session = Depends(get_db)):
    return crud.get_reviews_for_product(db, product_id=product_id)


# ---------- SHIPMENTS ----------
# NOTE: typically shipments are created/managed by admin/seller. Here we allow create/update,
# but you can require role-check for admin by checking current_user.role.
@app.post("/shipments/", response_model=schemas.ShipmentResponse, status_code=201)
def create_shipment_endpoint(shipment: schemas.ShipmentCreate,
                             db: Session = Depends(get_db),
                             current_user: models.User = Depends(get_current_user)):
    # If you want only admins: if current_user.role != "admin": raise HTTPException(403)
    try:
        db_ship = crud.create_shipment(db, shipment)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return db_ship

@app.get("/shipments/{shipment_id}", response_model=schemas.ShipmentResponse)
def get_shipment_endpoint(shipment_id: int, db: Session = Depends(get_db)):
    ship = crud.get_shipment(db, shipment_id)
    if not ship:
        raise HTTPException(status_code=404, detail="Shipment not found")
    return ship

@app.put("/shipments/{shipment_id}", response_model=schemas.ShipmentResponse)
def update_shipment_endpoint(shipment_id: int, status: str,
                             db: Session = Depends(get_db),
                             current_user: models.User = Depends(get_current_user)):
    # consider role check here (only admin/seller)
    ship = crud.update_shipment_status(db, shipment_id=shipment_id, status=status)
    if not ship:
        raise HTTPException(status_code=404, detail="Shipment not found")
    return ship
