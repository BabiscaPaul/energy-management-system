import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
import models
import auth
from database import engine, get_db

from shared.types import RoleEnum

import schemas

# GET    /users           - get all users (admin only)
# GET    /users/{id}      - get one user by id
# POST   /users           - create new user profile
# PUT    /users/{id}      - update entire user profile
# DELETE /users/{id}      - delete user

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="User Service")

@app.get("/health")
def health():
    return {"status": "healthy", "service": "auth-service"}

@app.get("/users")
def get_all_users(
    current_user: dict = Depends(auth.require_admin),
    db: Session = Depends(get_db)
):
    users = db.query(models.User).all()
    return users

@app.get("/users/{id}")
def get_user(
    id: int,
    current_user: dict = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(models.User.id == id).first()
    
    if user is None: 
        raise HTTPException(status_code=404, detail="User not found")
    
    if current_user["role"] != RoleEnum.ADMIN.value:
        raise HTTPException(
            status_code=403, 
            detail="Access denied. Clients can only view their own profile."
        )
    
    return user

@app.post("/users", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    user_in: schemas.UserCreate, 
    current_user: dict = Depends(auth.require_admin),
    db: Session = Depends(get_db)
):
    does_exist = db.query(models.User).filter(models.User.id == user_in.id).first()
    if does_exist: raise HTTPException(status_code=400, detail="User profile already exists")
    
    is_email_taken = db.query(models.User).filter(models.User.email == user_in.email).first()
    if is_email_taken: raise HTTPException(status_code=400, detail='Email already in use')
    
    new_user = models.User(
        id = user_in.id,
        full_name = user_in.full_name,
        email = user_in.email, 
        phone_number = user_in.phone_number,
        address = user_in.address
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.put("/users/{id}", response_model=schemas.UserUpdate, status_code=status.HTTP_200_OK)
def update_user(
    id: int, 
    user_in: schemas.UserUpdate,
    current_user: dict = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(models.User.id == id).first()
    if user is None: raise HTTPException(status_code=404, detail='User not found')
    
    if current_user["role"] != RoleEnum.ADMIN.value and current_user["sub"] != id:
        raise HTTPException(
            status_code=403,
            detail="Access denied. Clients can only update their own profile."
        )
    
    if user_in.email and user_in.email != user.email:
        is_email_taken = db.query(models.User).filter(
            models.User.email == user_in.email,
            models.User.id != id
        ).first()
        if is_email_taken:
            raise HTTPException(status_code=400, detail='Email already in use')
    
    if user_in.full_name is not None:
        user.full_name = user_in.full_name
    if user_in.email is not None:
        user.email = user_in.email
    if user_in.phone_number is not None:
        user.phone_number = user_in.phone_number
    if user_in.address is not None:
        user.address = user_in.address
    
    db.commit()
    db.refresh(user)
    return user

@app.delete("/users/{id}", status_code=status.HTTP_200_OK)
def delete_user(
    id: int, 
    current_user: dict = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(models.User.id == id).first()
    if user is None:
        raise HTTPException(status_code=404, detail='User not found')
    
    if current_user["role"] != RoleEnum.ADMIN.value and current_user["user_id"] != id:
        raise HTTPException(
            status_code=403,
            detail="Access denied. Clients can only delete their own profile."
        )
    
    db.delete(user)
    db.commit()
    
    return {"message": "User deleted successfully", "id": id}