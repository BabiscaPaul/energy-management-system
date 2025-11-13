import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
import models
import auth
from database import engine, get_db

from shared.types import RoleEnum

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
    current_user: dict = Depends(auth.get_current_user),  # Authenticated users only
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
