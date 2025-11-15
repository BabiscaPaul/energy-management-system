from pydantic import BaseModel, EmailStr
from typing import Optional

class UserBase(BaseModel):
    full_name: str
    email: EmailStr
    phone_number: Optional[str] = None
    address: Optional[str] = None
    
class UserCreate(UserBase):
    id: int
    
class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    address: Optional[str] = None

class UserResponse(UserBase):
    id: int 
    
    class Config:
        from_attributes = True