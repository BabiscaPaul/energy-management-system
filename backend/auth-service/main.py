import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
import models
import schemas
import auth
from database import engine, get_db

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Auth Service")

@app.post("/register", response_model=schemas.Token, status_code=status.HTTP_201_CREATED)
def register(user: schemas.UserRegister, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    hashed_pw = auth.hash_password(user.password)
    new_user = models.User(
        username=user.username,
        hashed_password=hashed_pw,
        role=user.role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    access_token = auth.create_access_token(
        data={
            "sub": user.username,
            "role": user.role.value,
            "user_id": new_user.id,       
        }
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": new_user.id,
    }

@app.post("/login", response_model=schemas.Token)
def login(user: schemas.UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not auth.verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = auth.create_access_token(
        data={
            "sub": db_user.username, 
            "role": db_user.role.value,
            "user_id": db_user.id,     
        }
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": db_user.id,
    }

@app.get("/health")
def health():
    return {"status": "healthy", "service": "auth-service"}